"""AppSetting repository for configuration override data access."""

from website.models import AppSetting
from website.repositories.base import BaseRepository


class SettingRepository(BaseRepository[AppSetting]):
    """Repository for AppSetting (runtime config override) entities."""

    model_class = AppSetting

    def get_by_key(self, key: str) -> AppSetting | None:
        """Retrieve a setting override by its key.

        Args:
            key: Configuration key.

        Returns:
            AppSetting instance, or None if no override exists.
        """
        return self.session.get(AppSetting, key)

    def get_map(self) -> dict[str, str | None]:
        """Return all overrides as a ``{key: value}`` mapping.

        Returns:
            Dictionary mapping each stored key to its override value.
        """
        return {setting.key: setting.value for setting in self.get_all()}

    def upsert(self, key: str, value: str | None, updated_by_id: str | None = None) -> AppSetting:
        """Create or update a setting override.

        Args:
            key: Configuration key.
            value: Override value, or None.
            updated_by_id: Discord ID of the admin performing the change.

        Returns:
            The persisted AppSetting instance.
        """
        setting = self.get_by_key(key)
        if setting is None:
            setting = AppSetting(key=key, value=value, updated_by_id=updated_by_id)
            self.session.add(setting)
        else:
            setting.value = value
            setting.updated_by_id = updated_by_id
        self.session.flush()
        return setting

    def delete_by_key(self, key: str) -> None:
        """Delete a setting override by key, if present.

        Args:
            key: Configuration key to remove.
        """
        setting = self.get_by_key(key)
        if setting is not None:
            self.session.delete(setting)
            self.session.flush()
