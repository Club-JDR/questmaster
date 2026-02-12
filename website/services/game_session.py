"""GameSession service for play session management."""

from website.exceptions import SessionConflictError, ValidationError
from website.extensions import db
from website.models import GameSession
from website.repositories.game_session import GameSessionRepository
from website.utils.logger import logger


class GameSessionService:
    """Service layer for GameSession operations.

    Handles session creation, deletion, updates, and conflict detection.
    """

    def __init__(self, repository=None):
        self.repo = repository or GameSessionRepository()

    def create(self, game, start, end) -> GameSession:
        """Create a new game session.

        Args:
            game: Game instance to add the session to.
            start: Session start datetime.
            end: Session end datetime.

        Returns:
            Created GameSession instance.

        Raises:
            ValidationError: If start >= end.
            SessionConflictError: If the session overlaps with an existing one.
        """
        if start >= end:
            raise ValidationError("Session start must be before end time.")

        if self._has_conflict(game, start, end):
            raise SessionConflictError(
                "Session overlaps with an existing session.", game_id=game.id
            )

        session = GameSession(start=start, end=end)
        self.repo.add(session)
        game.sessions.append(session)
        db.session.commit()
        logger.info(f"Session added for game {game.id} from {start} to {end}")
        return session

    def delete(self, session) -> None:
        """Delete a game session.

        Args:
            session: GameSession instance to delete.
        """
        game_id = session.game_id
        start = session.start
        end = session.end
        self.repo.delete(session)
        db.session.commit()
        logger.info(f"Session removed for game {game_id} from {start} to {end}")

    def update(self, session, new_start, new_end) -> GameSession:
        """Update a session's start/end times.

        Args:
            session: Existing GameSession instance.
            new_start: New start datetime.
            new_end: New end datetime.

        Returns:
            Updated GameSession instance.

        Raises:
            ValidationError: If new_start >= new_end.
            SessionConflictError: If new times overlap another session.
        """
        if new_start >= new_end:
            raise ValidationError("Session start must be before end time.")

        game = session.game
        if self._has_conflict(game, new_start, new_end, exclude_session_id=session.id):
            raise SessionConflictError(
                "Session overlaps with an existing session.", game_id=game.id
            )

        session.start = new_start
        session.end = new_end
        db.session.commit()
        logger.info(f"Session {session.id} updated to {new_start} - {new_end}")
        return session

    def get_by_id_or_404(self, session_id) -> GameSession:
        """Get session by ID or abort with 404.

        Args:
            session_id: Session ID.

        Returns:
            GameSession instance.

        Raises:
            NotFound: Flask 404 error.
        """
        return self.repo.get_by_id_or_404(session_id)

    def find_in_range(self, start, end) -> list[GameSession]:
        """Find all sessions within a date range.

        Args:
            start: Range start datetime.
            end: Range end datetime.

        Returns:
            List of GameSession instances within the range.
        """
        return self.repo.find_in_range(start, end)

    @staticmethod
    def _has_conflict(game, start_dt, end_dt, exclude_session_id=None):
        for s in game.sessions:
            if exclude_session_id and s.id == exclude_session_id:
                continue
            if not (end_dt <= s.start or start_dt >= s.end):
                return True
        return False
