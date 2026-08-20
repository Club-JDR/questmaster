"""Game repository for data access."""

from typing import Optional

from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import joinedload, subqueryload

from config.constants import GAME_STATUS_DRAFT
from website.models import Game, GameViewer, User
from website.repositories.base import BaseRepository, Pagination, paginate_query
from website.utils.timezone import now_utc


class GameRepository(BaseRepository[Game]):
    """Repository for Game entity.

    Provides data access methods for games including queries, filtering, and search.
    All methods return models or None - exceptions for 404s should be raised by services.
    """

    model_class = Game
    search_columns = [Game.name, Game.slug]

    def base_query(self):
        """Return all games ordered by date (most recent first)."""
        return self.session.query(Game).order_by(Game.date.desc())

    def get_all_ordered(self) -> list[Game]:
        """Retrieve all games ordered by date (most recent first).

        Returns:
            List of Game instances.
        """
        return self.session.query(Game).order_by(Game.date.desc()).all()

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

    def get_by_channel(self, channel_id: str) -> Optional[Game]:
        """Get the game whose Discord channel is ``channel_id``.

        Args:
            channel_id: Discord channel ID the command was invoked in.

        Returns:
            The matching Game, or None if the channel isn't a game channel.
        """
        return self.session.query(Game).filter_by(channel=str(channel_id)).first()

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

    def find_by_viewer(self, user_id: str) -> list[Game]:
        """Find all games a user follows as a viewer (spectator).

        Args:
            user_id: Viewer's user ID.

        Returns:
            List of games this user follows as a spectator, regardless of status.
        """
        return (
            self.session.query(Game)
            .join(GameViewer, GameViewer.game_id == Game.id)
            .filter(GameViewer.user_id == user_id)
            .all()
        )

    def find_by_gm_with_relations(self, gm_id: str) -> list[Game]:
        """Return all games GMed by a user, with stats relations eager-loaded.

        Loads system, vtt, sessions and players to avoid N+1 queries when
        aggregating dashboard statistics. Draft games are excluded so unpublished
        announcements never contribute to statistics.

        Args:
            gm_id: GM user ID.

        Returns:
            List of non-draft games GMed by this user.
        """
        return (
            self.session.query(Game)
            .options(
                joinedload(Game.system),
                joinedload(Game.vtt),
                subqueryload(Game.sessions),
                subqueryload(Game.players),
            )
            .filter(Game.gm_id == gm_id, Game.status != GAME_STATUS_DRAFT)
            .all()
        )

    def find_by_player_with_relations(self, player_id: str) -> list[Game]:
        """Return all games a user plays in, with stats relations eager-loaded.

        Loads gm, system, vtt, sessions and players to avoid N+1 queries when
        aggregating dashboard statistics. Draft games are excluded so unpublished
        announcements never contribute to statistics.

        Args:
            player_id: Player user ID.

        Returns:
            List of non-draft games where the user is registered as a player.
        """
        return (
            self.session.query(Game)
            .join(Game.players)
            .options(
                joinedload(Game.gm),
                joinedload(Game.system),
                joinedload(Game.vtt),
                subqueryload(Game.sessions),
                subqueryload(Game.players),
            )
            .filter(User.id == player_id, Game.status != GAME_STATUS_DRAFT)
            .all()
        )

    def find_by_viewer_with_relations(self, user_id: str) -> list[Game]:
        """Return all games a user follows as a viewer, with stats relations eager-loaded.

        Loads gm, system, vtt, sessions and players to avoid N+1 queries when
        aggregating dashboard statistics. Draft games are excluded so unpublished
        announcements never contribute to statistics.

        Args:
            user_id: Viewer's user ID.

        Returns:
            List of non-draft games this user follows as a spectator.
        """
        return (
            self.session.query(Game)
            .join(GameViewer, GameViewer.game_id == Game.id)
            .options(
                joinedload(Game.gm),
                joinedload(Game.system),
                joinedload(Game.vtt),
                subqueryload(Game.sessions),
                subqueryload(Game.players),
            )
            .filter(GameViewer.user_id == user_id, Game.status != GAME_STATUS_DRAFT)
            .all()
        )

    def find_schedule_relevant_games(self, user_id: str) -> list[Game]:
        """Return non-draft games a user is involved in, for schedule-conflict checks.

        Includes games where the user is GM *or* a player. Only eager-loads
        ``sessions`` (needed to compute each game's occupied time windows) —
        unlike ``find_by_gm_with_relations``/``find_by_player_with_relations``,
        it skips ``gm``/``system``/``vtt``/``players``, which schedule-conflict
        checks never read, to keep this query cheap when run under a row lock.

        Args:
            user_id: User ID (GM or player).

        Returns:
            List of matching non-draft games, deduplicated.
        """
        gm_games = (
            self.session.query(Game)
            .options(subqueryload(Game.sessions))
            .filter(Game.gm_id == user_id, Game.status != GAME_STATUS_DRAFT)
            .all()
        )
        player_games = (
            self.session.query(Game)
            .join(Game.players)
            .options(subqueryload(Game.sessions))
            .filter(User.id == user_id, Game.status != GAME_STATUS_DRAFT)
            .all()
        )
        return list({g.id: g for g in (*gm_games, *player_games)}.values())

    def find_all_with_relations(self) -> list[Game]:
        """Return every game with stats relations eager-loaded.

        Loads system, vtt, sessions and players to avoid N+1 queries when
        aggregating app-wide statistics. Draft games are excluded so unpublished
        announcements never contribute to statistics.

        Returns:
            List of all non-draft games.
        """
        return (
            self.session.query(Game)
            .options(
                joinedload(Game.system),
                joinedload(Game.vtt),
                subqueryload(Game.sessions),
                subqueryload(Game.players),
            )
            .filter(Game.status != GAME_STATUS_DRAFT)
            .all()
        )

    def find_by_special_event(self, event_id: int) -> list[Game]:
        """Find all games for a special event.

        Args:
            event_id: Special event ID.

        Returns:
            List of games linked to this special event.
        """
        return self.session.query(Game).filter_by(special_event_id=event_id).all()

    def query_by_special_event(self, event_id: int) -> Optional[Game]:
        """Return a query object for games linked to a special event.

        Unlike ``find_by_special_event`` (which returns a list), this returns
        an unevaluated query suitable for further filtering and pagination.

        Args:
            event_id: Special event ID.

        Returns:
            SQLAlchemy query filtered by special_event_id.
        """
        return self.session.query(Game).filter(Game.special_event_id == event_id)

    def get_player_leaderboard_for_event(
        self, event_id: int, limit: int = 10
    ) -> list[tuple[User, int]]:
        """Get the player leaderboard for a special event.

        Ranks users by how many of the event's games they are registered in as
        a player. Only counts games whose GM actually awarded trophies when
        archiving (``trophies_awarded``) — this implies the game is archived,
        so drafts, open and closed games are excluded too, along with archived
        games the GM chose not to award trophies for.

        Args:
            event_id: Special event ID to scope the leaderboard to.
            limit: Maximum number of entries to return. Defaults to 10.

        Returns:
            List of (User, game_count) tuples ordered by game_count descending.
        """
        return (
            self.session.query(User, func.count(Game.id).label("total"))
            .join(Game.players)
            .filter(
                Game.special_event_id == event_id,
                Game.trophies_awarded.is_(True),
            )
            .group_by(User.id)
            .order_by(func.count(Game.id).desc())
            .limit(limit)
            .all()
        )

    def get_gm_leaderboard_for_event(
        self, event_id: int, limit: int = 10
    ) -> list[tuple[User, int]]:
        """Get the GM leaderboard for a special event.

        Ranks users by how many of the event's games they GMed. Only counts
        games whose trophies were actually awarded — see
        ``get_player_leaderboard_for_event``.

        Args:
            event_id: Special event ID to scope the leaderboard to.
            limit: Maximum number of entries to return. Defaults to 10.

        Returns:
            List of (User, game_count) tuples ordered by game_count descending.
        """
        return (
            self.session.query(User, func.count(Game.id).label("total"))
            .join(Game, Game.gm_id == User.id)
            .filter(
                Game.special_event_id == event_id,
                Game.trophies_awarded.is_(True),
            )
            .group_by(User.id)
            .order_by(func.count(Game.id).desc())
            .limit(limit)
            .all()
        )

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

    def _build_status_conditions(self, status: list, user_payload: Optional[dict]) -> list:
        """Build filter conditions for the status field, respecting user permissions.

        Args:
            status: List of requested statuses.
            user_payload: Optional auth payload used to gate draft visibility.

        Returns:
            List of SQLAlchemy filter expressions.
        """
        conditions = []
        for s in status:
            if s != "draft":
                conditions.append(Game.status == s)
            elif user_payload and user_payload.get("is_admin"):
                conditions.append(Game.status == "draft")
            elif user_payload:
                conditions.append(
                    and_(
                        Game.status == "draft",
                        Game.gm_id == user_payload.get("user_id"),
                    )
                )
        return conditions

    def search(
        self,
        filters: dict,
        page: int = 1,
        per_page: int = 20,
        user_payload: Optional[dict] = None,
    ) -> Pagination[Game]:
        """Search games with complex filters and pagination.

        The single query-building implementation for game search: status
        visibility, filtering, and ordering all live here so views and the API
        can't drift apart (both go through this method — see
        ``website.utils.game_filters`` for the checkbox-args-to-filters
        translation views use).

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
            Pagination of matching games.
        """
        now = now_utc()
        query = self.session.query(Game)

        # Status filter with permission check
        status = filters.get("status", ["open"])
        if status:
            status_conditions = self._build_status_conditions(status, user_payload)
            if status_conditions:
                query = query.filter(or_(*status_conditions))

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

        return paginate_query(query, page, per_page)
