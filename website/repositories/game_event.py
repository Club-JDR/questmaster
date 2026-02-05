from website.models import GameEvent
from website.repositories.base import BaseRepository


class GameEventRepository(BaseRepository[GameEvent]):
    model_class = GameEvent

    def log(self, action: str, game_id: int, description: str = None) -> GameEvent:
        event = GameEvent(
            action=action,
            game_id=game_id,
            description=description,
        )
        return self.add(event)
