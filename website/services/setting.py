"""Settings service resolving configuration from the database, then the env.

Operational Discord identifiers (guild, role and channel IDs) may be overridden
at runtime by an admin and stored in the ``app_setting`` table. Any key that is
not overridden falls back to the environment-backed ``app.config`` value loaded
at startup. Secrets (bot token, client secret, JWT key, database URI) are never
overridable and always come from the environment.
"""

from __future__ import annotations

from flask import current_app, g, has_app_context
from sqlalchemy.exc import SQLAlchemyError

from website.exceptions import ValidationError
from website.extensions import db
from website.repositories.setting import SettingRepository
from website.utils.logger import logger

# Setting groups, used only to organise the admin settings page.
_GROUP_SERVER = "Serveur Discord"
_GROUP_ROLES = "Rôles Discord"
_GROUP_CHANNELS = "Salons Discord"

# Keys an admin may override from the database, with display metadata for the
# admin UI. The ``group`` field is only used to organise the settings page.
OVERRIDABLE_SETTINGS: list[dict[str, str]] = [
    {"key": "DISCORD_GUILD_ID", "label": "ID du serveur", "group": _GROUP_SERVER},
    {"key": "DISCORD_GUILD_NAME", "label": "Nom du serveur", "group": _GROUP_SERVER},
    {"key": "DISCORD_GM_ROLE_ID", "label": "ID du rôle MJ", "group": _GROUP_ROLES},
    {"key": "DISCORD_ADMIN_ROLE_ID", "label": "ID du rôle Admin", "group": _GROUP_ROLES},
    {"key": "DISCORD_PLAYER_ROLE_ID", "label": "ID du rôle Joueur", "group": _GROUP_ROLES},
    {"key": "POSTS_CHANNEL_ID", "label": "ID du salon des annonces", "group": _GROUP_CHANNELS},
    {"key": "ADMIN_CHANNEL_ID", "label": "ID du salon admin", "group": _GROUP_CHANNELS},
]

OVERRIDABLE_KEYS: frozenset[str] = frozenset(item["key"] for item in OVERRIDABLE_SETTINGS)

# Key under which the per-request overrides map is memoised on ``flask.g``.
_G_CACHE_KEY = "_app_setting_overrides"


class SettingsService:
    """Resolve and manage database-backed configuration overrides."""

    def __init__(self, repository: SettingRepository | None = None):
        self.repo = repository or SettingRepository()

    def _overrides(self) -> dict[str, str | None]:
        """Return the override map, memoised on the request context.

        Reading every overridable key during a request (guild id + role ids in
        templates and auth) collapses to a single query. If the overrides table
        is unreachable, an empty map is returned so callers fall back to the
        environment-backed configuration rather than failing.

        Returns:
            Mapping of stored keys to their (possibly None) override values.
        """
        in_context = has_app_context()
        if in_context:
            cached = g.get(_G_CACHE_KEY)
            if cached is not None:
                return cached

        try:
            overrides = self.repo.get_map()
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.warning(f"Could not load setting overrides, using env values: {exc}")
            overrides = {}

        if in_context:
            setattr(g, _G_CACHE_KEY, overrides)
        return overrides

    def _invalidate(self) -> None:
        """Drop the request-scoped overrides cache after a write."""
        if has_app_context():
            g.pop(_G_CACHE_KEY, None)

    def get(self, key: str, default=None):
        """Resolve a configuration value: database override, then environment.

        Args:
            key: Configuration key.
            default: Value returned when neither an override nor an env value exists.

        Returns:
            The override value if set to a non-empty string, otherwise the
            ``app.config`` value, otherwise ``default``.
        """
        if key in OVERRIDABLE_KEYS:
            override = self._overrides().get(key)
            if override:
                return override
        return current_app.config.get(key, default)

    def get_effective(self) -> list[dict]:
        """Describe every overridable setting for the admin UI.

        Returns:
            List of dicts with ``key``, ``label``, ``group``, ``env_value``
            (the environment fallback), ``override`` (the stored value or None)
            and ``effective`` (the value currently in use).
        """
        overrides = self._overrides()
        result = []
        for item in OVERRIDABLE_SETTINGS:
            key = item["key"]
            env_value = current_app.config.get(key)
            override = overrides.get(key)
            result.append(
                {
                    "key": key,
                    "label": item["label"],
                    "group": item["group"],
                    "env_value": env_value,
                    "override": override,
                    "effective": override or env_value,
                }
            )
        return result

    def set(self, key: str, value: str | None, updated_by_id: str | None = None) -> None:
        """Create, update or clear a single override.

        An empty or whitespace-only value clears the override so the key falls
        back to the environment value.

        Args:
            key: Configuration key to override.
            value: New override value, or empty/None to clear it.
            updated_by_id: Discord ID of the admin performing the change.

        Raises:
            ValidationError: If the key is not in the overridable allowlist.
        """
        if key not in OVERRIDABLE_KEYS:
            raise ValidationError(f"Setting '{key}' cannot be overridden.", field="key")

        cleaned = (value or "").strip()
        if cleaned:
            self.repo.upsert(key, cleaned, updated_by_id)
        else:
            self.repo.delete_by_key(key)
        db.session.commit()
        self._invalidate()

    def set_many(self, values: dict[str, str | None], updated_by_id: str | None = None) -> None:
        """Apply several overrides in one transaction.

        Args:
            values: Mapping of overridable keys to their new values.
            updated_by_id: Discord ID of the admin performing the change.

        Raises:
            ValidationError: If any key is not in the overridable allowlist.
        """
        unknown = set(values) - OVERRIDABLE_KEYS
        if unknown:
            raise ValidationError(
                f"Settings cannot be overridden: {', '.join(sorted(unknown))}.", field="key"
            )

        for key, value in values.items():
            cleaned = (value or "").strip()
            if cleaned:
                self.repo.upsert(key, cleaned, updated_by_id)
            else:
                self.repo.delete_by_key(key)
        db.session.commit()
        self._invalidate()
