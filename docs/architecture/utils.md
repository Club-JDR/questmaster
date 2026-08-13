# Utils

The utils layer lives in `website/utils/` and provides **helper functions** shared across the application.

## Overview

| Module | Description |
| --- | --- |
| `form_parsers` | Extract classification scores, ambience, and restriction tags from Flask forms |
| `game_embeds` | Build Discord embed dictionaries for announcements, sessions, registrations, and alerts |
| `game_filters` | Paginated game search with multi-checkbox filters and status-based visibility rules |
| `game_form_defaults` | Whitelist/validators for per-user game-form defaults and the existing/cloned-game > user default > app default resolver |
| `logger` | Request-aware logging with trace IDs and game event convenience wrapper |
| `markdown` | Render Markdown (description/complement) to sanitized HTML (`markdown-it-py` + `nh3`) |

## API Reference

::: website.utils
    options:
      show_root_heading: false
      members_order: source
