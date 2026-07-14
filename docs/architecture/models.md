# Models

The model layer lives in `website/models/` and contains SQLAlchemy models only — no business logic.

Models define:

- Database columns and types
- Relationships and foreign keys
- Constraints (unique, not null, etc.)
- Serialization via `SerializableMixin`

## Overview

| Model | Description |
| --- | --- |
| `Game` | A tabletop RPG game (one-shot or campaign) |
| `GameSession` | A scheduled session belonging to a game |
| `GameEvent` | Audit trail entry for game lifecycle events |
| `User` | A Discord-authenticated user |
| `Trophy` | An achievement definition |
| `UserTrophy` | A trophy awarded to a user |
| `System` | A tabletop RPG system (e.g. D&D 5e, Pathfinder) |
| `Channel` | A Discord channel category managed by the app |
| `SpecialEvent` | A special community event (e.g. Halloween, Christmas) |
| `Vtt` | A virtual tabletop tool (e.g. Foundry, Roll20) |
| `AppSetting` | A runtime configuration override (and the managed postable-channel list) |
| `DiscordMessage` | A message (content, embeds and/or link buttons) sent to Discord from the admin panel |
| `PermissionGrant` | An RBAC grant: one capability granted to a Discord role or an individual user |
| `AppLog` | A persisted application log record written by the database log handler |

## API Reference

::: website.models
    options:
      show_root_heading: false
      members_order: source
