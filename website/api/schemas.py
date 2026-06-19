"""Marshmallow schemas for validating API request bodies."""

from marshmallow import EXCLUDE, Schema, fields, validate

from config.constants import (
    AMBIENCES,
    GAME_CHAR,
    GAME_FREQUENCIES,
    GAME_TYPES,
    GAME_XP,
    RESTRICTIONS,
)


class GameSchema(Schema):
    """Validate the editable fields of a game.

    Used for both creation (full body) and updates (``partial=True``).
    The output uses clean field names (``system_id``, ``classification``
    as an object, ``ambience`` as a list); the view layer maps these onto
    the form-shaped dict that :class:`~website.services.game.GameService`
    consumes.
    """

    class Meta:
        """Ignore unknown keys (e.g. client-only fields)."""

        unknown = EXCLUDE

    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    type = fields.String(required=True, validate=validate.OneOf(GAME_TYPES))
    special_event_id = fields.Integer(allow_none=True)
    system_id = fields.Integer(required=True)
    vtt_id = fields.Integer(allow_none=True)
    description = fields.String(required=True, validate=validate.Length(min=1))
    restriction = fields.String(required=True, validate=validate.OneOf(RESTRICTIONS))
    restriction_tags = fields.String(allow_none=True)
    party_size = fields.Integer(required=True, validate=validate.Range(min=1))
    party_selection = fields.Boolean(load_default=False)
    xp = fields.String(required=True, validate=validate.OneOf(GAME_XP))
    date = fields.DateTime(required=True)
    length = fields.String(required=True, validate=validate.Length(min=1))
    session_length = fields.Decimal(required=True, places=1, validate=validate.Range(min=0))
    frequency = fields.String(allow_none=True, validate=validate.OneOf(GAME_FREQUENCIES))
    characters = fields.String(required=True, validate=validate.OneOf(GAME_CHAR))
    classification = fields.Dict(keys=fields.String(), values=fields.Integer(), load_default=dict)
    ambience = fields.List(fields.String(validate=validate.OneOf(AMBIENCES)), load_default=list)
    complement = fields.String(allow_none=True)
    img = fields.String(allow_none=True)


game_schema = GameSchema()
