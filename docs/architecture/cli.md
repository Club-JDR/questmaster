# CLI Commands

QuestMaster exposes Flask CLI commands for common setup tasks. They are registered in `website/extensions.py` and available via `flask <command>`.

## Available Commands

| Command | Description |
| --- | --- |
| `flask seed-trophies` | Seed the database with the default set of trophies |
| `flask setup-test-db` | Initialize and seed a test database (skips if already initialized) |

## Usage

```bash
# Seed trophies into the database
flask seed-trophies

# Set up a fresh test database
flask setup-test-db
```
