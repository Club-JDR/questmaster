# QuestMaster

[![CI](https://github.com/Club-JDR/questmaster/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Club-JDR/questmaster/actions/workflows/ci.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Club-JDR_questmaster&metric=alert_status)](https://sonarcloud.io/dashboard?id=Club-JDR_questmaster)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

The Club JDR booking app for roleplaying sessions.

This app is meant for GMs to create new Games with all the details (name, type, number of players, date and time of the sessions etc..) and for players to be able to register for the games. It interacts with the Discord server to automatically create roles and channels for the games.

## Project structure

```text
website/              # Main Flask application
  models/             #   SQLAlchemy models with serialization support
  repositories/       #   Data access layer (queries, generic CRUD)
  services/           #   Business logic layer (transactions, validation)
  views/              #   Flask blueprints (thin controllers)
  client/             #   External service clients (Discord API)
  utils/              #   Helpers (filters, embeds, form parsers, logging)
  exceptions/         #   Structured exception hierarchy
  templates/          #   Jinja2 templates
  static/             #   CSS, JS, images
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

This roadmap isn't a Product roadmap. It doesn't include feature requests or bugfix, only tech stack improvements.

- **Logging** — improve logging for better observability and debugging.
- **Performances** — improve queries, cache and index for better performances.
- **API + frontend split** — move from a monolithic Flask app with server-rendered templates to a Flask REST API backend and a Vue.js frontend.
- **UI/UX** — Move from bootstrap to DaisyUI.
