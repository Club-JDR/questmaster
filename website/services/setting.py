"""Settings service resolving configuration from the database, then the env.

Operational Discord identifiers (guild, role and channel IDs) may be overridden
at runtime by an admin and stored in the ``app_setting`` table. Any key that is
not overridden falls back to the environment-backed ``app.config`` value loaded
at startup. Secrets (bot token, client secret, JWT key, database URI) are never
overridable and always come from the environment.
"""

from __future__ import annotations

import json

from flask import current_app, g, has_app_context
from sqlalchemy.exc import SQLAlchemyError

from config.constants import (
    DASHBOARD_AGENDA_LIMIT_DEFAULT,
    DASHBOARD_LIMIT_MAX,
    DASHBOARD_OPEN_LIMIT_DEFAULT,
    DISCORD_ROLE_AUTO_THRESHOLD_DEFAULT,
)
from website.exceptions import ValidationError
from website.extensions import db
from website.repositories.setting import SettingRepository
from website.utils.logger import logger

# Key under which the admin-managed list of postable Discord channels is stored.
# Distinct from OVERRIDABLE_SETTINGS (env-backed overrides): this is a fully
# DB-managed JSON list of ``{"label": ..., "id": ...}`` entries.
POST_CHANNELS_KEY = "discord_post_channels"

# Fully DB-managed operational settings (not env-backed). When direct permissions
# are enabled, new games grant players access via per-channel permission overwrites
# instead of a dedicated role. The auto-threshold is the guild role count at which
# the scheduler turns the toggle on automatically.
DIRECT_PERMISSIONS_KEY = "discord_use_direct_permissions"
ROLE_AUTO_THRESHOLD_KEY = "discord_role_auto_threshold"

# Fully DB-managed dashboard sizes.
DASHBOARD_AGENDA_LIMIT_KEY = "dashboard_agenda_limit"
DASHBOARD_OPEN_LIMIT_KEY = "dashboard_open_limit"

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

    def _read_post_channels(self) -> list[dict]:
        """Read and normalise the stored postable-channel list.

        Returns:
            List of ``{"label": str, "id": str}`` dicts. Invalid or missing
            data yields an empty list.
        """
        setting = self.repo.get_by_key(POST_CHANNELS_KEY)
        if setting is None or not setting.value:
            return []
        try:
            items = json.loads(setting.value)
        except ValueError, TypeError:
            logger.warning("Stored post channels are not valid JSON; ignoring.")
            return []
        return [
            {"label": str(item.get("label") or item["id"]), "id": str(item["id"])}
            for item in items
            if isinstance(item, dict) and item.get("id")
        ]

    def _write_post_channels(self, channels: list[dict], updated_by_id: str | None) -> None:
        """Persist the postable-channel list as JSON and commit.

        Args:
            channels: List of ``{"label", "id"}`` dicts.
            updated_by_id: Discord ID of the admin performing the change.
        """
        self.repo.upsert(POST_CHANNELS_KEY, json.dumps(channels), updated_by_id)
        db.session.commit()
        self._invalidate()

    def get_post_channels(self) -> list[dict]:
        """Return the admin-managed Discord channels an admin may post into.

        Returns:
            List of dicts with ``label`` and ``channel_id``.
        """
        return [{"label": c["label"], "channel_id": c["id"]} for c in self._read_post_channels()]

    def is_post_channel(self, channel_id: str) -> bool:
        """Check whether a Discord channel ID is a configured postable channel.

        Args:
            channel_id: Discord channel ID.

        Returns:
            True if the channel is in the managed postable list.
        """
        return any(c["id"] == channel_id for c in self._read_post_channels())

    def get_post_channel_label(self, channel_id: str) -> str | None:
        """Return the human label for a postable channel ID, if configured.

        Args:
            channel_id: Discord channel ID.

        Returns:
            The channel label, or None if not configured.
        """
        for c in self._read_post_channels():
            if c["id"] == channel_id:
                return c["label"]
        return None

    def add_post_channel(
        self, label: str, channel_id: str, updated_by_id: str | None = None
    ) -> None:
        """Add a channel to the managed postable list.

        Args:
            label: Human-friendly channel name shown in the compose dropdown.
            channel_id: Discord channel ID to post into.
            updated_by_id: Discord ID of the admin performing the change.

        Raises:
            ValidationError: If the ID is missing or already present.
        """
        channel_id = (channel_id or "").strip()
        label = (label or "").strip()
        if not channel_id:
            raise ValidationError("Channel ID is required.", field="channel_id")
        channels = self._read_post_channels()
        if any(c["id"] == channel_id for c in channels):
            raise ValidationError("Channel already added.", field="channel_id")
        channels.append({"label": label or channel_id, "id": channel_id})
        self._write_post_channels(channels, updated_by_id)

    def remove_post_channel(self, channel_id: str, updated_by_id: str | None = None) -> None:
        """Remove a channel from the managed postable list.

        Args:
            channel_id: Discord channel ID to remove.
            updated_by_id: Discord ID of the admin performing the change.
        """
        channels = [c for c in self._read_post_channels() if c["id"] != channel_id]
        self._write_post_channels(channels, updated_by_id)

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

    def is_direct_permissions_enabled(self) -> bool:
        """Return whether new games should use direct per-player channel permissions.

        When enabled, games are created without a dedicated Discord role; players are
        granted channel access via individual permission overwrites instead.

        Returns:
            True if the direct-permission mode is enabled.
        """
        setting = self.repo.get_by_key(DIRECT_PERMISSIONS_KEY)
        return bool(setting and setting.value == "true")

    def set_direct_permissions(self, enabled: bool, updated_by_id: str | None = None) -> None:
        """Enable or disable direct per-player channel permissions for new games.

        Args:
            enabled: Whether direct-permission mode should be on.
            updated_by_id: Discord ID of the admin performing the change (or None when
                set automatically by the role-count monitor).
        """
        self.repo.upsert(DIRECT_PERMISSIONS_KEY, "true" if enabled else "false", updated_by_id)
        db.session.commit()
        self._invalidate()

    def get_role_auto_threshold(self) -> int:
        """Return the guild role count at which direct permissions auto-enable.

        Returns:
            The configured threshold, or :data:`DISCORD_ROLE_AUTO_THRESHOLD_DEFAULT`
            when unset or invalid.
        """
        setting = self.repo.get_by_key(ROLE_AUTO_THRESHOLD_KEY)
        if setting and setting.value:
            try:
                return int(setting.value)
            except ValueError:
                logger.warning("Stored role auto-threshold is not an integer; using default.")
        return DISCORD_ROLE_AUTO_THRESHOLD_DEFAULT

    def set_role_auto_threshold(self, threshold: int, updated_by_id: str | None = None) -> None:
        """Set the guild role count at which direct permissions auto-enable.

        Args:
            threshold: Role count threshold (must be a positive integer).
            updated_by_id: Discord ID of the admin performing the change.

        Raises:
            ValidationError: If the threshold is not a positive integer.
        """
        try:
            value = int(threshold)
        except TypeError, ValueError:
            raise ValidationError("Threshold must be an integer.", field="threshold")
        if value <= 0:
            raise ValidationError("Threshold must be a positive integer.", field="threshold")
        self.repo.upsert(ROLE_AUTO_THRESHOLD_KEY, str(value), updated_by_id)
        db.session.commit()
        self._invalidate()

    def _get_positive_int(self, key: str, default: int) -> int:
        """Return a stored positive-integer setting, falling back to a default.

        Args:
            key: Setting key to read.
            default: Value returned when the setting is unset or not an integer.

        Returns:
            The stored integer, or ``default`` when unset or invalid.
        """
        setting = self.repo.get_by_key(key)
        if setting and setting.value:
            try:
                return int(setting.value)
            except ValueError:
                logger.warning("Stored %s is not an integer; using default.", key)
        return default

    def _set_bounded_int(
        self, key: str, value, maximum: int, field: str, updated_by_id: str | None
    ) -> None:
        """Validate and persist a bounded positive-integer setting.

        Args:
            key: Setting key to write.
            value: Raw value to parse and store.
            maximum: Inclusive upper bound for the value.
            field: Field name attached to a raised ``ValidationError``.
            updated_by_id: Discord ID of the admin performing the change.

        Raises:
            ValidationError: If the value is not an integer within ``1..maximum``.
        """
        try:
            parsed = int(value)
        except TypeError, ValueError:
            raise ValidationError("La valeur doit être un entier.", field=field)
        if parsed <= 0 or parsed > maximum:
            raise ValidationError(
                f"La valeur doit être comprise entre 1 et {maximum}.", field=field
            )
        self.repo.upsert(key, str(parsed), updated_by_id)
        db.session.commit()
        self._invalidate()

    def get_dashboard_agenda_limit(self) -> int:
        """Return the number of upcoming sessions listed in the dashboard agenda.

        Returns:
            The stored value, or :data:`DASHBOARD_AGENDA_LIMIT_DEFAULT` when unset
            or invalid.
        """
        return self._get_positive_int(DASHBOARD_AGENDA_LIMIT_KEY, DASHBOARD_AGENDA_LIMIT_DEFAULT)

    def set_dashboard_agenda_limit(self, value, updated_by_id: str | None = None) -> None:
        """Set the number of upcoming sessions listed in the dashboard agenda.

        Args:
            value: Session count (1..:data:`DASHBOARD_LIMIT_MAX`).
            updated_by_id: Discord ID of the admin performing the change.

        Raises:
            ValidationError: If the value is not an integer within bounds.
        """
        self._set_bounded_int(
            DASHBOARD_AGENDA_LIMIT_KEY,
            value,
            DASHBOARD_LIMIT_MAX,
            "dashboard_agenda_limit",
            updated_by_id,
        )

    def get_dashboard_open_limit(self) -> int:
        """Return the number of open announcements previewed on the dashboard.

        Returns:
            The stored value, or :data:`DASHBOARD_OPEN_LIMIT_DEFAULT` when unset
            or invalid.
        """
        return self._get_positive_int(DASHBOARD_OPEN_LIMIT_KEY, DASHBOARD_OPEN_LIMIT_DEFAULT)

    def set_dashboard_open_limit(self, value, updated_by_id: str | None = None) -> None:
        """Set the number of open announcements previewed on the dashboard.

        Args:
            value: Card count (1..:data:`DASHBOARD_LIMIT_MAX`).
            updated_by_id: Discord ID of the admin performing the change.

        Raises:
            ValidationError: If the value is not an integer within bounds.
        """
        self._set_bounded_int(
            DASHBOARD_OPEN_LIMIT_KEY,
            value,
            DASHBOARD_LIMIT_MAX,
            "dashboard_open_limit",
            updated_by_id,
        )
