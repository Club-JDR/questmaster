# Client

The client layer lives in `website/client/` and provides **low-level HTTP clients** for external API integrations.

Clients:

- Handle HTTP requests, retries, and rate limiting
- Raise domain exceptions on failure (e.g. `DiscordAPIError`)
- Contain no business logic — that belongs in [services](services.md)

## Overview

| Client | Description |
| --- | --- |
| `Discord` | Low-level Discord REST API client with retry logic and rate-limit handling |

## API Reference

::: website.client
    options:
      show_root_heading: false
      members_order: source
