"""System repository for game system data access."""

from sqlalchemy.orm import subqueryload

from config.constants import (
    GAME_STATUS_DRAFT,
    GAME_TYPE_CAMPAIGN,
    GAME_TYPE_ONESHOT,
    USER_PLACEHOLDER_NAME,
)
from website.models import Game, System, User
from website.repositories.base import BaseRepository


class SystemRepository(BaseRepository[System]):
    """Repository for System entities."""

    model_class = System
    search_columns = [System.id, System.name]

    def base_query(self):
        """Return all systems ordered by name."""
        return self.session.query(System).order_by(System.name)

    def get_all_ordered(self) -> list[System]:
        """Retrieve all systems ordered by name.

        Returns:
            List of System instances sorted alphabetically.
        """
        return self.session.query(System).order_by(System.name).all()

    def get_by_name(self, name: str) -> System | None:
        """Find a system by its name.

        Args:
            name: System name to search for.

        Returns:
            System instance if found, None otherwise.
        """
        return self.session.query(System).filter_by(name=name).first()

    def get_gm_history(self, system_id: int) -> list[User]:
        """Return distinct GMs who have run this system, from actual game history.

        Only non-draft games count, so unpublished announcements never
        contribute to this "who's already run it" signal. Placeholder users
        (unresolved Discord profiles) are excluded since they aren't a real
        person to recommend as a contact.

        Args:
            system_id: System ID.

        Returns:
            List of User instances ordered by name.
        """
        return (
            self.session.query(User)
            .join(Game, Game.gm_id == User.id)
            .filter(
                Game.system_id == system_id,
                Game.status != GAME_STATUS_DRAFT,
                User.name != USER_PLACEHOLDER_NAME,
            )
            .distinct()
            .order_by(User.name)
            .all()
        )

    def get_gm_stats(self, gm_id: str, system_id: int) -> dict:
        """Return a GM's non-draft game/session tally for a system.

        Args:
            gm_id: GM user ID.
            system_id: System ID.

        Returns:
            Dict with "oneshots", "campaigns" and "sessions" counts.
        """
        games = (
            self.session.query(Game)
            .options(subqueryload(Game.sessions))
            .filter(
                Game.gm_id == gm_id,
                Game.system_id == system_id,
                Game.status != GAME_STATUS_DRAFT,
            )
            .all()
        )
        return self._summarize_games(games)

    def get_player_stats(self, player_id: str, system_id: int) -> dict:
        """Return a player's non-draft game/session tally for a system.

        Args:
            player_id: Player user ID.
            system_id: System ID.

        Returns:
            Dict with "oneshots", "campaigns" and "sessions" counts.
        """
        games = (
            self.session.query(Game)
            .join(Game.players)
            .options(subqueryload(Game.sessions))
            .filter(
                User.id == player_id,
                Game.system_id == system_id,
                Game.status != GAME_STATUS_DRAFT,
            )
            .all()
        )
        return self._summarize_games(games)

    @staticmethod
    def _summarize_games(games: list[Game]) -> dict:
        """Tally a list of games into oneshot/campaign/session counts."""
        return {
            "oneshots": sum(1 for g in games if g.type == GAME_TYPE_ONESHOT),
            "campaigns": sum(1 for g in games if g.type == GAME_TYPE_CAMPAIGN),
            "sessions": sum(len(g.sessions) for g in games),
        }
