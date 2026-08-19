# CLI Commands

QuestMaster exposes Flask CLI commands for common setup tasks. They are registered in `website/extensions.py` and `website/cli.py`, and available via `flask <command>`.

## Available Commands

| Command | Description |
| --- | --- |
| `flask seed-trophies` | Seed the database with the default set of trophies |
| `flask setup-test-db` | Initialize and seed a test database (skips if already initialized) |
| `flask sync-discord-commands` | Register/update the guild's Discord slash commands (see [Discord Bot](../discord-bot.md)) |
| `flask clear-cache [target]` | Clear cached `Flask-Caching` data — the whole backend by default, or a single named target |

## Usage

```bash
# Seed trophies into the database
flask seed-trophies

# Set up a fresh test database
flask setup-test-db

# Register the Discord slash commands with the guild
flask sync-discord-commands

# Clear the entire cache backend (default target)
flask clear-cache

# Clear a single cached surface instead
flask clear-cache calendar
```

### `clear-cache` targets

Useful after a bad deploy, a manual DB fix that bypassed a service's own
`cache.delete_memoized()` calls, or during local debugging. `target` defaults
to `all` (flushes the whole configured cache backend — scoped to
QuestMaster's own keys via `CACHE_KEY_PREFIX`, so this is safe to run in
production without affecting other apps sharing the same Redis instance) or
one of:

| Target | Clears |
| --- | --- |
| `systems` | `SystemService.get_all` (the systems list) |
| `vtts` | `VttService.get_all` (the VTT list) |
| `calendar` | `GameSessionService`'s per-month stats behind `/calendrier/` |
| `badges` | The badge leaderboards (global + per-event) behind `/badges/classement/` |
| `stats` | `StatsService`'s per-user dashboard stats (all users at once) |
| `discord` | `DiscordService`'s cached guild role count |

Each target dispatches to the owning service's own `clear_cache()`/
`invalidate_all()` method (`website.cli.clear_cache_target()`), so
`website/cli.py` stays a thin caller rather than duplicating invalidation
logic. The same dispatch backs the "Cache" panel on the admin settings page
(`/admin/settings/`), for admins who'd rather not use the CLI.
