# Repositories

The repository layer lives in `website/repositories/` and handles **data access only** — queries, CRUD, and database interactions.

Repositories:

- Never contain business logic or validation
- Never access Flask context
- Never commit transactions (services own transaction boundaries)
- Inherit from a shared `BaseRepository` for common CRUD operations

## Overview

| Repository | Model | Description |
| --- | --- | --- |
| `BaseRepository` | — | Generic CRUD operations inherited by all repositories |
| `ChannelRepository` | [`Channel`](models.md#website.models.Channel) | Discord category management and size tracking |
| `GameRepository` | [`Game`](models.md#website.models.Game) | Game queries with filtering, search, pagination, and eager loading |
| `GameEventRepository` | [`GameEvent`](models.md#website.models.GameEvent) | Game audit log entry creation |
| `GameSessionRepository` | [`GameSession`](models.md#website.models.GameSession) | Session date range queries and conflict detection |
| `SpecialEventRepository` | [`SpecialEvent`](models.md#website.models.SpecialEvent) | Themed event retrieval with active/inactive filtering |
| `SystemRepository` | [`System`](models.md#website.models.System) | RPG system lookups |
| `TrophyRepository` | [`Trophy`](models.md#website.models.Trophy), [`UserTrophy`](models.md#website.models.UserTrophy) | Achievement data and leaderboard aggregations |
| `UserRepository` | [`User`](models.md#website.models.User) | User entity retrieval |
| `VttRepository` | [`Vtt`](models.md#website.models.Vtt) | Virtual tabletop platform lookups |

## API Reference

::: website.repositories
    options:
      show_root_heading: false
      members_order: source
