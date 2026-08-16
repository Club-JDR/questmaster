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
| `ChannelService` | [`ChannelRepository`](repositories.md#website.repositories.ChannelRepository) | [`Channel`](models.md#website.models.Channel) | Category management: size tracking/reconciliation, creating and auto-provisioning categories, and Discord channel cleanup |
| `DiscordService` | [`Discord`](client.md#website.client.Discord) (client) | — | Discord API wrapper with dependency injection for testability |
| `DiscordCommandService` | [`GameRepository`](repositories.md#website.repositories.GameRepository) (via `GameService`) | — | Dispatch Discord slash commands to QuestMaster actions (see [Discord Bot](../discord-bot.md)) |
| `DiscordMessageService` | [`DiscordMessageRepository`](repositories.md#website.repositories.DiscordMessageRepository) | [`DiscordMessage`](models.md#website.models.DiscordMessage) | Compose/send/edit admin Discord messages (Discord-first, then persist) |
| `GameService` | [`GameRepository`](repositories.md#website.repositories.GameRepository), [`GameViewerRepository`](repositories.md#website.repositories.GameViewerRepository) | [`Game`](models.md#website.models.Game), [`GameViewer`](models.md#website.models.GameViewer) | Complete game lifecycle — creation, publishing, registration, archival, Discord sync — plus the self-service spectator follow/unfollow toggle |
| `GameEventService` | [`GameEventRepository`](repositories.md#website.repositories.GameEventRepository) | [`GameEvent`](models.md#website.models.GameEvent) | Transaction-safe audit trail logging for games |
| `GameSessionService` | [`GameSessionRepository`](repositories.md#website.repositories.GameSessionRepository) | [`GameSession`](models.md#website.models.GameSession) | Session CRUD with conflict detection and validation |
| `PermissionService` | [`PermissionGrantRepository`](repositories.md#website.repositories.PermissionGrantRepository) | [`PermissionGrant`](models.md#website.models.PermissionGrant) | RBAC: manage capability grants and resolve a user's effective (cached) permission set |
| `StatsService` | [`GameRepository`](repositories.md#website.repositories.GameRepository) | [`Game`](models.md#website.models.Game) | Per-user dashboard agenda (MJ/joueur·euse/spectateur·ice roles) and all-time play statistics (cached, JSON-serialisable) |
| `SpecialEventService` | [`SpecialEventRepository`](repositories.md#website.repositories.SpecialEventRepository) | [`SpecialEvent`](models.md#website.models.SpecialEvent) | Special event CRUD with uniqueness validation |
| `SystemService` | [`SystemRepository`](repositories.md#website.repositories.SystemRepository), [`UserSystemInterestRepository`](repositories.md#website.repositories.UserSystemInterestRepository) | [`System`](models.md#website.models.System), [`UserSystemInterest`](models.md#website.models.UserSystemInterest) | Game system CRUD with cache invalidation, plus the public system page's matchmaking: GM run-history, declared player/GM interest lists, and the self-service interest toggle |
| `TrophyService` | [`TrophyRepository`](repositories.md#website.repositories.TrophyRepository) | [`Trophy`](models.md#website.models.Trophy) | Trophy awarding logic (unique vs. non-unique rules) and leaderboards |
| `UserService` | [`UserRepository`](repositories.md#website.repositories.UserRepository) | [`User`](models.md#website.models.User) | User retrieval, creation, Discord profile initialization, per-user game-form defaults, and admin [view-as](../admin.md#view-as-user-impersonation) target validation |
| `VttService` | [`VttRepository`](repositories.md#website.repositories.VttRepository) | [`Vtt`](models.md#website.models.Vtt) | Virtual tabletop CRUD with cache invalidation |
| `SettingsService` | [`SettingRepository`](repositories.md#website.repositories.SettingRepository) | [`AppSetting`](models.md#website.models.AppSetting) | Runtime config overrides (DB → env), the managed postable-channel list, and fully DB-managed operational settings (dashboard sizes, page size, role/category auto-provisioning thresholds, direct-permissions mode) |
| `AppLogService` | [`AppLogRepository`](repositories.md#website.repositories.AppLogRepository) | [`AppLog`](models.md#website.models.AppLog) | Browse (paginated/filtered) and prune persisted application logs for the admin log viewer |

## API Reference

::: website.services
    options:
      show_root_heading: false
      members_order: source
