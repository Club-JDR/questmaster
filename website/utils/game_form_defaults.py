"""Resolve game-form field values and validate per-user defaults.

Centralizes the "what value should this field start with?" logic for
``game_form.j2`` (previously scattered as inline ``{% if game %}`` checks
throughout the template) behind a single precedence rule: an existing or
cloned game's own value always wins; otherwise a user's saved default is used
if the field is whitelisted and one was saved; otherwise an application-wide
default is used.

Only fields in :data:`USER_DEFAULT_FIELDS` are resolved by this module at
all — that whitelist is the single source of truth for both what's read
from/written to ``User.game_defaults`` and what the template consults
``defaults`` for. Everything else (``name``, ``date``, ``length``,
``classification``, ``restriction``, ``restriction_tags``, ``img``) has no
default concept and stays read directly off ``game`` in the template, exactly
as before. ``frequency`` is a borderline case — only meaningful for
campaigns, so a default for it would need to apply conditionally on the
(also-resolved) ``type`` default rather than as a flat whitelist entry — not
implemented here.
"""

from config.constants import AMBIENCES, GAME_CHAR, GAME_TYPES, GAME_XP


def _validate_text_default(value) -> str | None:
    """Validate a proposed text default (description/complement).

    Args:
        value: Raw value submitted for the field.

    Returns:
        The stripped string, or None if it isn't a non-empty string.
    """
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _validate_id_default(value) -> int | None:
    """Validate a proposed foreign-key default (system/vtt).

    Structural validation only (positive integer); whether the referenced
    row still exists is checked later, at resolution time, against the
    caller-supplied set of currently valid IDs.

    Args:
        value: Raw value submitted for the field.

    Returns:
        The value as a positive int, or None if it isn't one.
    """
    try:
        value = int(value)
    except TypeError, ValueError:
        return None
    return value if value > 0 else None


def _validate_session_length_default(value) -> float | None:
    """Validate a proposed session-length default, in hours.

    Args:
        value: Raw value submitted for the field.

    Returns:
        The value as a float within the form's [0.5, 24] bounds, or None.
    """
    try:
        value = float(value)
    except TypeError, ValueError:
        return None
    return value if 0.5 <= value <= 24 else None


def _validate_party_size_default(value) -> int | None:
    """Validate a proposed party-size default.

    Args:
        value: Raw value submitted for the field.

    Returns:
        The value as an int within the form's [1, 99] bounds, or None.
    """
    try:
        value = int(value)
    except TypeError, ValueError:
        return None
    return value if 1 <= value <= 99 else None


def _validate_bool_default(value) -> bool | None:
    """Validate a proposed boolean default (party_selection).

    Accepts either an already-stored bool (read back from JSONB) or a raw
    HTML checkbox value ("on" when checked, absent from form data when not —
    handled by the caller, not here). False collapses to None: it's
    indistinguishable from "no preference" since the app default is also
    False, so there is nothing meaningful to persist.

    Args:
        value: Raw value submitted for the field.

    Returns:
        True if set/checked, else None.
    """
    if isinstance(value, bool):
        return value or None
    if isinstance(value, str):
        return True if value.strip().lower() in ("on", "true", "1", "yes") else None
    return None


def _validate_ambience_default(value) -> list[str] | None:
    """Validate a proposed ambience-tags default.

    Args:
        value: Raw value submitted for the field (expected to be a list of
            ambience keys, e.g. built via ``website.utils.form_parsers.
            get_ambience`` from raw checkbox form data).

    Returns:
        The subset of valid ambience keys, or None if empty/invalid.
    """
    if not isinstance(value, list):
        return None
    cleaned = [v for v in value if v in AMBIENCES]
    return cleaned or None


def _make_enum_validator(valid_values):
    """Build a validator accepting only one of a fixed set of values.

    Args:
        valid_values: Iterable of allowed values.

    Returns:
        A validator function: value -> value if allowed, else None.
    """

    def validate(value):
        return value if value in valid_values else None

    return validate


# Whitelist of fields a user may configure as a personal default, mapped to
# their validator. This is the single source of truth for what this module
# resolves: ALL_FIELDS and APP_DEFAULTS below are both keyed off it.
USER_DEFAULT_FIELDS = {
    "type": _make_enum_validator(GAME_TYPES),
    "system": _validate_id_default,
    "vtt": _validate_id_default,
    "session_length": _validate_session_length_default,
    "party_size": _validate_party_size_default,
    "party_selection": _validate_bool_default,
    "xp": _make_enum_validator(GAME_XP),
    "characters": _make_enum_validator(GAME_CHAR),
    "ambience": _validate_ambience_default,
    "description": _validate_text_default,
    "complement": _validate_text_default,
}

ALL_FIELDS = tuple(USER_DEFAULT_FIELDS)

# Application-wide fallback for each field. Fields not listed here (system,
# vtt) have no app-wide default: they stay unset unless an existing/cloned
# game or a user default supplies a value.
APP_DEFAULTS = {
    "type": "oneshot",
    "session_length": "3.5",
    "party_size": 4,
    "party_selection": False,
    "xp": "all",
    "characters": "with_gm",
    "ambience": [],
    "description": "",
    "complement": "",
}

# Game model attributes that don't share the form field's name.
_FIELD_ATTR_OVERRIDES = {"system": "system_id", "vtt": "vtt_id"}

# Whitelisted fields whose value is a foreign key that may go stale (the
# referenced System/Vtt gets deleted after being saved as a default).
# Resolution cross-checks these against the currently valid IDs.
_FK_FIELDS = {"system", "vtt"}


def sanitize_user_defaults(data: dict) -> dict:
    """Validate and whitelist proposed per-user game-form defaults.

    Args:
        data: Raw mapping of proposed defaults (e.g. submitted form data).
            Only whitelisted keys are considered; anything else is ignored.

    Returns:
        A clean dict containing only whitelisted fields with a valid, non-empty
        value. A field submitted empty/invalid is simply omitted (clearing
        any previously saved default for it).
    """
    cleaned = {}
    for field, validate in USER_DEFAULT_FIELDS.items():
        if field not in data:
            continue
        value = validate(data[field])
        if value is not None:
            cleaned[field] = value
    return cleaned


def _game_field_value(game, field: str):
    """Read a form field's value off an existing/cloned game.

    Args:
        game: Game instance to read from.
        field: Form field name (see :data:`ALL_FIELDS`).

    Returns:
        The value to prefill the field with. ``type`` is always plain
        ``game.type`` ("oneshot"/"campaign") here, matching the
        USER_DEFAULT_FIELDS "type" validator's contract — the template
        reads ``game.special_event_id`` directly for the special-event radio,
        never through ``defaults``.
    """
    if field == "ambience":
        return list(game.ambience) if game.ambience else []
    if field == "complement":
        return game.complement or ""
    attr = _FIELD_ATTR_OVERRIDES.get(field, field)
    return getattr(game, attr, None)


def resolve_game_form_defaults(game=None, user=None, systems=None, vtts=None) -> dict:
    """Resolve every whitelisted game-form field to its starting value.

    Precedence: an existing/cloned ``game``'s own value always wins; otherwise
    a whitelisted default saved on ``user.game_defaults`` is used; otherwise
    the application-wide default. User defaults are only ever consulted for a
    brand-new game — they must never override an existing or cloned game's
    values.

    Args:
        game: Existing Game instance when editing or cloning, else None.
        user: User instance whose saved defaults may prefill a new game.
        systems: Currently available System instances/dicts (with an ``id``),
            used to drop a saved system default that no longer exists.
        vtts: Currently available Vtt instances/dicts (with an ``id``), used
            to drop a saved VTT default that no longer exists.

    Returns:
        Dict covering every field in :data:`ALL_FIELDS`, ready to plug into
        ``game_form.j2`` as e.g. ``defaults.description``.
    """
    if game is not None:
        return {field: _game_field_value(game, field) for field in ALL_FIELDS}

    resolved = {field: APP_DEFAULTS.get(field) for field in ALL_FIELDS}
    valid_ids = _valid_fk_ids(systems, vtts)
    user_defaults = getattr(user, "game_defaults", None) or {} if user is not None else {}
    for field, validate in USER_DEFAULT_FIELDS.items():
        value = _resolve_user_default(field, validate, user_defaults, valid_ids)
        if value is not None:
            resolved[field] = value

    return resolved


def _valid_fk_ids(systems, vtts) -> dict:
    """Build the set of currently valid IDs for each FK-backed default field.

    Args:
        systems: Currently available System instances/dicts (with an ``id``),
            or None.
        vtts: Currently available Vtt instances/dicts (with an ``id``), or None.

    Returns:
        Dict mapping "system"/"vtt" to their valid-ID set, or None per field
        if the corresponding collection wasn't supplied.
    """
    return {
        "system": {s.id for s in systems} if systems is not None else None,
        "vtt": {v.id for v in vtts} if vtts is not None else None,
    }


def _resolve_user_default(field, validate, user_defaults, valid_ids):
    """Validate one field's saved user default, cross-checking FK freshness.

    Args:
        field: Form field name.
        validate: The field's validator, from :data:`USER_DEFAULT_FIELDS`.
        user_defaults: Raw ``user.game_defaults`` mapping (possibly empty).
        valid_ids: Currently valid FK IDs, as returned by :func:`_valid_fk_ids`.

    Returns:
        The validated value to use, or None if unset, invalid, or a stale
        FK reference.
    """
    if field not in user_defaults:
        return None
    value = validate(user_defaults[field])
    if value is None:
        return None
    if field in _FK_FIELDS:
        allowed = valid_ids.get(field)
        if allowed is not None and value not in allowed:
            return None
    return value
