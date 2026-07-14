# QuestMaster

[![CI](https://github.com/Club-JDR/questmaster/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Club-JDR/questmaster/actions/workflows/ci.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Club-JDR_questmaster&metric=alert_status)](https://sonarcloud.io/dashboard?id=Club-JDR_questmaster)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

The Club JDR booking app for roleplaying sessions.

This app is meant for GMs to create new Games with all the details (name, type, number of players, date and time of the sessions etc..) and for players to be able to register for the games. It interacts with the Discord server to automatically create roles and channels for the games.

## Project structure

```text
assets/               # Frontend source (CSS, JS entry points — built by Vite)
website/              # Main Flask application
  models/             #   SQLAlchemy models with serialization support
  repositories/       #   Data access layer (queries, generic CRUD)
  services/           #   Business logic layer (transactions, validation)
  views/              #   Flask blueprints (thin controllers)
  client/             #   External service clients (Discord API)
  utils/              #   Helpers (filters, embeds, form parsers, logging)
  exceptions/         #   Structured exception hierarchy
  templates/          #   Jinja2 templates
  static/             #   Images and legacy JS; built assets output to static/dist/
  extensions.py       #   Flask extensions (db, migrate, csrf, cache, discord)
  scheduler.py        #   APScheduler background jobs
  bot.py              #   Discord bot instance
tests/                # Pytest test suite (mirrors website/ structure)
migrations/           # Alembic database migrations
config/               # App configuration
  settings.py         #   Flask settings (from environment variables)
  constants.py        #   Enums, Discord settings, pagination, routes
questmaster.py        # Entry point
```

## Documentation

Full documentation is available at [club-jdr.github.io/questmaster](https://club-jdr.github.io/questmaster/), including a [getting started guide](https://club-jdr.github.io/questmaster/getting-started/) for setting up a local development environment.

To preview the docs locally:

```sh
pip install -e ".[docs]"
mkdocs serve
```

## Contributing

Contributions are welcome! You can help by:

- Opening a [bug report](https://github.com/Club-JDR/questmaster/issues/new?template=bug_report.md) or a [feature request](https://github.com/Club-JDR/questmaster/issues/new?template=feature_request.md).
- Picking up an open issue and submitting a pull request.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on code style, architecture, and submitting changes.

If you're just looking to play tabletop RPGs with us, that's also fine, just head over to [club-jdr.fr](https://club-jdr.fr).

## Roadmap

This roadmap isn't a Product roadmap. It doesn't include feature requests or bugfixes, only
tech stack improvements.

The **North Star** is an **API-first backend with a Vue.js frontend**: move the UI out of Flask
into a standalone Vue.js SPA that consumes the `/api/v1/` REST API, leaving Flask as an
API-only backend once the SPA reaches feature parity with the server-rendered templates.

- **Logging** — persistent app logs with an admin browsing page and redaction. ✅ _Done._
- **REST API write layer** — complete the write API (game lifecycle & registration, admin
  endpoints) on top of the existing read-only API, then document and test it (OpenAPI, ~90%
  coverage). Game CRUD is done; lifecycle, admin, and API docs remain.
- **Vue.js frontend** — scaffold the SPA (Vite, shared Tailwind v4 + DaisyUI v5 tokens), port
  views to parity with the Jinja2 UI, then cut over and retire the server-rendered templates.
- **Full-stack E2E testing** — run the complete stack via docker-compose and drive it with a
  browser E2E suite (Playwright) wired into CI.
- **Performances** — eliminate N+1 queries, add indexes, and layer caching (repository →
  service → view) before the SPA drives heavier API traffic.

Smaller self-contained improvements (Discord role/channel colour on game-type change, a Discord
slash-command "sidekick" bot) can ship alongside the roadmap above.
