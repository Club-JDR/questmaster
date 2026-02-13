# Services

The service layer lives in `website/services/` and contains **all business logic**. Services are the primary place for new logic in QuestMaster.

Services:

- Own transaction boundaries
- Perform validation and enforce business rules
- Raise domain-specific exceptions from `website.exceptions`
- Call repositories for data access
- Never access Flask `request` or `session` directly

## Overview

| Service | Repository | Model | Description |
| --- | --- | --- | --- |
| `ChannelService` | [`ChannelRepository`](repositories.md#website.repositories.ChannelRepository) | [`Channel`](models.md#website.models.Channel) | Category size management and Discord channel cleanup |
| `DiscordService` | [`Discord`](client.md#website.client.Discord) (client) | — | Discord API wrapper with dependency injection for testability |
| `GameService` | [`GameRepository`](repositories.md#website.repositories.GameRepository) | [`Game`](models.md#website.models.Game) | Complete game lifecycle — creation, publishing, registration, archival, Discord sync |
| `GameEventService` | [`GameEventRepository`](repositories.md#website.repositories.GameEventRepository) | [`GameEvent`](models.md#website.models.GameEvent) | Transaction-safe audit trail logging for games |
| `GameSessionService` | [`GameSessionRepository`](repositories.md#website.repositories.GameSessionRepository) | [`GameSession`](models.md#website.models.GameSession) | Session CRUD with conflict detection and validation |
| `SpecialEventService` | [`SpecialEventRepository`](repositories.md#website.repositories.SpecialEventRepository) | [`SpecialEvent`](models.md#website.models.SpecialEvent) | Special event CRUD with uniqueness validation |
| `SystemService` | [`SystemRepository`](repositories.md#website.repositories.SystemRepository) | [`System`](models.md#website.models.System) | Game system CRUD with cache invalidation |
| `TrophyService` | [`TrophyRepository`](repositories.md#website.repositories.TrophyRepository) | [`Trophy`](models.md#website.models.Trophy) | Trophy awarding logic (unique vs. non-unique rules) and leaderboards |
| `UserService` | [`UserRepository`](repositories.md#website.repositories.UserRepository) | [`User`](models.md#website.models.User) | User retrieval, creation, and Discord profile initialization |
| `VttService` | [`VttRepository`](repositories.md#website.repositories.VttRepository) | [`Vtt`](models.md#website.models.Vtt) | Virtual tabletop CRUD with cache invalidation |

## API Reference

::: website.services
    options:
      show_root_heading: false
      members_order: source
