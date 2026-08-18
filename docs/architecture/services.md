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
| `GameService` | [`GameRepository`](repositories.md#website.repositories.GameRepository), [`GameViewerRepository`](repositories.md#website.repositories.GameViewerRepository) | [`Game`](models.md#website.models.Game), [`GameViewer`](models.md#website.models.GameViewer) | Complete game lifecycle — creation, publishing, registration, archival, Discord sync — plus the self-service spectator follow/unfollow toggle. "Branching" a campaign into a quick replacement one-shot (see below) is pure composition over `create()`/`publish()`/`register_player()`; no dedicated method |
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

## Branching a campaign into a one-shot

A GM whose campaign is paused (one player unavailable) can create a quick
replacement table for the rest of the group instead of retyping a new
announcement and the roster by hand. This is a GM-facing workflow on the
game detail page (`website/views/games.py`), not a new service method — it
composes existing `GameService` calls:

1. **Entry point**: the game detail page's "Cloner" action is replaced by
   "One-shot ponctuel" for a published (non-draft, non-archived) campaign —
   see `_redirect_unless_branchable`. A one-shot never shows it (branching a
   one-shot into another one-shot is just "Cloner" with extra steps).
2. **Minimal form**: `get_branch_form` renders `game_form.j2` in "new game"
   mode (`game` is *not* passed) — so it does **not** reuse the campaign's
   own content, unlike "Cloner". Only structural defaults are seeded onto
   `resolve_game_form_defaults()`'s result: `type="oneshot"`, the campaign's
   `system`/`vtt`, `party_selection=True` (GM-curated, not open
   self-registration), and `party_size` defaulted to the campaign's current
   headcount (falling back to the normal default when it has none).
3. **Creation**: `create_branch_game` calls `GameService.create()` (draft)
   then immediately `GameService.publish(..., silent=True)` — resources
   (channel, role, first session) exist, but nothing is posted to the public
   announcements channel and the game lands `closed` to registration. The
   GM decides when to actually open/announce it.
4. **Roster carry-over**: the redirect appends `?branch_from=<source_slug>`
   to the new game's own detail-page URL. `get_game_details` resolves that
   (GM/admin only, via `_resolve_branch_roster`) into a `branch_roster`
   context consumed by `game_details.j2` to auto-open a checklist modal —
   the same avatar/checkbox pattern as "Gérer" — pre-checked with the
   campaign's current players. Confirming calls `register_player(...,
   force=True, skip_schedule_check=True)` for each kept player; resources
   already exist at this point, so they get real Discord channel access,
   not just a database record.

No new model, migration, or service method — see
`improvements/CONSOLIDATED_PLAN.md` (item I) for the original design notes.

## API Reference

::: website.services
    options:
      show_root_heading: false
      members_order: source
