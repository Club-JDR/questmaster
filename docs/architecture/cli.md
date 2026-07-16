# CLI Commands

QuestMaster exposes Flask CLI commands for common setup tasks. They are registered in `website/extensions.py` and `website/cli.py`, and available via `flask <command>`.

## Available Commands

| Command | Description |
| --- | --- |
| `flask seed-trophies` | Seed the database with the default set of trophies |
| `flask setup-test-db` | Initialize and seed a test database (skips if already initialized) |
| `flask sync-discord-commands` | Register/update the guild's Discord slash commands (see [Discord Bot](../discord-bot.md)) |

## Usage

```bash
# Seed trophies into the database
flask seed-trophies

# Set up a fresh test database
flask setup-test-db

# Register the Discord slash commands with the guild
flask sync-discord-commands
```
