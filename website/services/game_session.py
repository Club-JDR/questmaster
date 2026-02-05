from website.extensions import db
from website.models import GameSession
from website.exceptions import ValidationError, SessionConflictError
from website.repositories.game_session import GameSessionRepository
from website.utils.logger import logger


class GameSessionService:
    def __init__(self, repository=None):
        self.repo = repository or GameSessionRepository()

    def create(self, game, start, end) -> GameSession:
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
        game_id = session.game_id
        start = session.start
        end = session.end
        self.repo.delete(session)
        db.session.commit()
        logger.info(f"Session removed for game {game_id} from {start} to {end}")

    def find_in_range(self, start, end) -> list[GameSession]:
        return self.repo.find_in_range(start, end)

    @staticmethod
    def _has_conflict(game, start_dt, end_dt, exclude_session_id=None):
        for s in game.sessions:
            if exclude_session_id and s.id == exclude_session_id:
                continue
            if not (end_dt <= s.start or start_dt >= s.end):
                return True
        return False
