from website.extensions import db
from website.models import GameEvent
from website.repositories.game_event import GameEventRepository


class GameEventService:
    def __init__(self, repository=None):
        self.repo = repository or GameEventRepository()

    def log_event(
        self, action: str, game_id: int, description: str = None
    ) -> GameEvent:
        event = self.repo.log(action, game_id, description)
        db.session.commit()
        return event
