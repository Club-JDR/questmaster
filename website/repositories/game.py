"""Game repository for data access."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import joinedload, subqueryload

from website.models import Game, User
from website.repositories.base import BaseRepository


class GameRepository(BaseRepository[Game]):
    """Repository for Game entity.

    Provides data access methods for games including queries, filtering, and search.
    All methods return models or None - exceptions for 404s should be raised by services.
    """

    model_class = Game

    def get_by_slug(self, slug: str) -> Optional[Game]:
        """Get game by slug.

        Args:
            slug: URL-safe game identifier.

        Returns:
            Game instance or None if not found.
        """
        return self.session.query(Game).filter_by(slug=slug).first()

    def get_by_slug_or_404(self, slug: str) -> Game:
        """Get game by slug or raise 404.

        Args:
            slug: URL-safe game identifier.

        Returns:
            Game instance.

        Raises:
            NotFound: If game with slug doesn't exist.
        """
        return self.session.query(Game).filter_by(slug=slug).first_or_404()

    def get_all_slugs(self) -> set[str]:
        """Get all existing game slugs.

        Returns:
            Set of all game slugs.
        """
        return {g.slug for g in self.session.query(Game.slug).all()}

    def find_by_gm(self, gm_id: str) -> list[Game]:
        """Find all games by GM.

        Args:
            gm_id: GM user ID.

        Returns:
            List of games GMed by this user.
        """
        return self.session.query(Game).filter_by(gm_id=gm_id).all()

    def find_by_player(self, player_id: str) -> list[Game]:
        """Find all games where user is a player.

        Args:
            player_id: Player user ID.

        Returns:
            List of games where user is registered as player.
        """
        return self.session.query(Game).join(Game.players).filter(User.id == player_id).all()

    def find_by_special_event(self, event_id: int) -> list[Game]:
        """Find all games for a special event.

        Args:
            event_id: Special event ID.

        Returns:
            List of games linked to this special event.
        """
        return self.session.query(Game).filter_by(special_event_id=event_id).all()

    def get_for_update(self, game_id: int) -> Optional[Game]:
        """Get game with pessimistic lock for updates.

        Uses SELECT FOR UPDATE to prevent race conditions during registration.

        Args:
            game_id: Game ID to lock.

        Returns:
            Game instance with exclusive lock, or None if not found.
        """
        return self.session.query(Game).filter_by(id=game_id).with_for_update().first()

    def get_with_relations(self, game_id: int) -> Optional[Game]:
        """Get game with all relationships eagerly loaded.

        Prevents N+1 queries by loading gm, system, vtt, players, and sessions.

        Args:
            game_id: Game ID.

        Returns:
            Game instance with relationships loaded, or None if not found.
        """
        return (
            self.session.query(Game)
            .options(
                joinedload(Game.gm),
                joinedload(Game.system),
                joinedload(Game.vtt),
                subqueryload(Game.players),
                subqueryload(Game.sessions),
            )
            .filter_by(id=game_id)
            .first()
        )

    def delete_by_id(self, game_id: int) -> None:
        """Delete game by ID.

        Args:
            game_id: Game ID to delete.
        """
        self.session.query(Game).filter_by(id=game_id).delete()
        self.session.flush()

    def search(
        self,
        filters: dict,
        page: int = 1,
        per_page: int = 20,
        user_payload: Optional[dict] = None,
    ) -> tuple[list[Game], int]:
        """Search games with complex filters and pagination.

        Replaces the complex get_filtered_games logic from helpers.

        Args:
            filters: Dict containing:
                - status: List of statuses (open, closed, archived, draft)
                - game_type: List of types (oneshot, campaign)
                - restriction: List of restrictions (all, 16+, 18+)
                - name: Optional name search string
                - system_id: Optional system ID
                - vtt_id: Optional VTT ID
                - gm_id: Optional GM ID (for "my games" views)
                - player_id: Optional player ID (for "my games as player" views)
                - special_event_id: Optional special event ID
            page: Page number (1-indexed).
            per_page: Items per page.
            user_payload: Optional user auth payload for permission filtering.

        Returns:
            Tuple of (games list, total count).
        """
        now = datetime.now(timezone.utc)
        query = self.session.query(Game)

        # Status filter with permission check
        status = filters.get("status", ["open"])
        if status:
            status_filters = []
            for s in status:
                if s != "draft":
                    status_filters.append(Game.status == s)
                elif user_payload and user_payload.get("is_admin"):
                    status_filters.append(Game.status == "draft")
                elif user_payload:
                    status_filters.append(
                        and_(
                            Game.status == "draft",
                            Game.gm_id == user_payload.get("user_id"),
                        )
                    )
            if status_filters:
                query = query.filter(or_(*status_filters))

        # Type filter
        game_type = filters.get("game_type", ["oneshot", "campaign"])
        if game_type:
            query = query.filter(Game.type.in_(game_type))

        # Restriction filter
        restriction = filters.get("restriction", ["all", "16+", "18+"])
        if restriction:
            query = query.filter(Game.restriction.in_(restriction))

        # Name search
        if filters.get("name"):
            query = query.filter(Game.name.ilike(f"%{filters['name']}%"))

        # System filter
        if filters.get("system_id"):
            query = query.filter(Game.system_id == filters["system_id"])

        # VTT filter
        if filters.get("vtt_id"):
            query = query.filter(Game.vtt_id == filters["vtt_id"])

        # GM filter
        if filters.get("gm_id"):
            query = query.filter(Game.gm_id == filters["gm_id"])

        # Player filter
        if filters.get("player_id"):
            query = query.join(Game.players).filter(User.id == filters["player_id"])

        # Special event filter
        if filters.get("special_event_id"):
            query = query.filter(Game.special_event_id == filters["special_event_id"])

        # Sorting - same logic as original helpers.py
        status_order = case(
            (Game.status == "draft", 0),
            (Game.status == "open", 1),
            (Game.status == "closed", 2),
            (Game.status == "archived", 3),
        )
        is_future = case((Game.date >= now, 0), else_=1)
        time_distance = func.abs(func.extract("epoch", Game.date - now))

        query = query.order_by(status_order, is_future, time_distance)

        # Get total count before pagination
        total = query.count()

        # Pagination
        offset = (page - 1) * per_page
        games = query.limit(per_page).offset(offset).all()

        return games, total
