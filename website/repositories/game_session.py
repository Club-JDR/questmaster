from website.models import GameSession
from website.repositories.base import BaseRepository


class GameSessionRepository(BaseRepository[GameSession]):
    model_class = GameSession

    def find_in_range(self, start, end) -> list[GameSession]:
        return (
            self.session.query(GameSession)
            .filter(GameSession.start >= start, GameSession.end <= end)
            .all()
        )
