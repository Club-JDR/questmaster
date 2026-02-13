# Exceptions

The exception hierarchy lives in `website/exceptions/` and provides structured, domain-specific errors used throughout the service layer.

## Hierarchy

```text
QuestMasterError             # Base for all application errors
  +-- NotFoundError          # Resource not found
  +-- UnauthorizedError      # Permission denied
  +-- ValidationError        # Input validation failure
  +-- DatabaseError          # Database operation failure
  +-- DiscordError           # Discord integration base error
  |     +-- DiscordAPIError  # Discord API call failure
  +-- GameError              # Game-related base error
        +-- GameFullError          # Game has no open slots
        +-- GameClosedError        # Game is not accepting registrations
        +-- DuplicateRegistrationError  # User already registered
        +-- SessionConflictError        # Session time conflict
```

## Usage

Services raise these exceptions. Views catch them and translate to appropriate HTTP responses.

```python
from website.exceptions import GameFullError

def register_player(game_id: int, user: User) -> None:
    game = game_repo.get_by_id(game_id)
    if game.is_full:
        raise GameFullError(f"Game '{game.name}' is full")
    # ...
```

## API Reference

::: website.exceptions
    options:
      show_root_heading: false
      members_order: source
