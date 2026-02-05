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
website/            # Main Flask application
  models/           # SQLAlchemy models with serialization support
    base.py         #   SerializableMixin (to_dict, from_dict, update_from_dict)
    game.py         #   Game (oneshot or campaign)
    game_session.py #   GameSession (individual session dates)
    game_event.py   #   GameEvent (audit trail of game actions)
    user.py         #   User (Discord-authenticated users)
    system.py       #   System (game systems, e.g. D&D 5e)
    vtt.py          #   Vtt (virtual tabletop tools)
    trophy.py       #   Trophy, UserTrophy (achievements)
    channel.py      #   Channel (Discord channels)
    special_event.py#   SpecialEvent (themed events)
  repositories/     # Data access layer (queries, no business logic)
    base.py         #   BaseRepository[T] with generic CRUD
    system.py       #   SystemRepository
    vtt.py          #   VttRepository
    channel.py      #   ChannelRepository
    game_event.py   #   GameEventRepository
  services/         # Business logic layer (owns transaction boundary)
    system.py       #   SystemService
    vtt.py          #   VttService
    channel.py      #   ChannelService
    game_event.py   #   GameEventService
  views/            # Flask blueprints (auth, games, admin, health, etc.)
  utils/            # Helpers (Discord API, logging)
  templates/        # Jinja2 templates
  static/           # CSS, JS, images
  exceptions/       # Structured exception hierarchy
    base.py         #   QuestMasterError, NotFoundError, UnauthorizedError
    validation.py   #   ValidationError
    database.py     #   DatabaseError
    discord.py      #   DiscordError, DiscordAPIError
    business.py     #   GameError, GameFullError, GameClosedError, etc.
  extensions.py     # Flask extensions (db, migrate, csrf, cache, discord)
  scheduler.py      # APScheduler background jobs
  bot.py            # Discord bot instance
tests/              # Pytest test suite
migrations/         # Alembic database migrations
config/             # App configuration
  settings.py       #   Flask settings (from environment variables)
  constants.py      #   Game enums, Discord settings, pagination, routes
questmaster.py      # Entry point
```

## Getting started

### Prerequisites

#### Discord bot and test server

The app authenticates users via Discord OAuth2 and interacts with a Discord server to manage roles and channels. You need:

1. **A Discord application** — create one at the [Discord Developer Portal](https://discord.com/developers/applications):
   - Under **OAuth2**, note the **Client ID** and **Client Secret**.
   - Add `http://localhost:8000/callback` as a redirect URI.
   - Under **Bot**, create a bot and copy its **Token**.
   - The bot needs the **Manage Roles** and **Manage Channels** permissions.

2. **A test Discord server** with:
   - Three roles: one for admins, one for GMs, and one for players.
   - Three text channels: one for game posts, one for admin notifications, and one for unit test output.
   - Invite your bot to this server with the permissions above.

You can get the IDs of the server, roles, and channels by enabling **Developer Mode** in Discord settings (App Settings > Advanced), then right-clicking on the relevant item and selecting **Copy ID**.

#### Environment

Create a `.env` file at the root of the project with the values from the previous step:

```ini
FLASK_AUTH_SECRET=""
DISCORD_CLIENT_ID=""
DISCORD_CLIENT_SECRET=""
DISCORD_BOT_TOKEN=""
DISCORD_REDIRECT_URI="http://localhost:8000/callback"
DISCORD_GUILD_NAME="Club JDR TEST"
POSTGRES_USER="clubjdr"
POSTGRES_PASSWORD=""
POSTGRES_DB="clubjdr"
POSTGRES_HOST="db" # localhost if using flask outside Docker
REDIS_HOST="redis" # localhost if using flask outside Docker
DISCORD_GUILD_ID=""
DISCORD_GM_ROLE_ID=""
DISCORD_ADMIN_ROLE_ID=""
DISCORD_PLAYER_ROLE_ID=""
POSTS_CHANNEL_ID=""
ADMIN_CHANNEL_ID=""
UNITTEST_CHANNEL_ID=""
FLASK_APP="website"
```

### Using Docker Compose (recommended)

Build and start the complete stack:

```sh
docker compose up -d --build
```

On the first start, run the migrations to initialize the database:

```sh
docker compose run app flask db upgrade
```

Run the tests:

```sh
docker compose run app-test python -m pytest tests/
```

### Local development

Edit the `.env` to change `POSTGRES_HOST` and `REDIS_HOST` to `localhost`.

Install the dependencies:

```sh
pip install -e ".[test,lint]"
```

Start the database and redis:

```sh
docker compose up -d db redis
```

Run the migrations and start the app:

```sh
flask db upgrade
flask run -p 8000
```

To run in debug mode (auto-reload on code changes):

```sh
flask --app website --debug run -p 8000
```

Run the tests:

```sh
python -m pytest tests/
```

### Flask shell

Connect to an interactive shell to inspect models and query the database:

```sh
# if using Docker Compose
docker compose run app flask shell
# if running locally
flask shell
```

## CI and tooling

Every pull request is checked by the CI pipeline which runs:

- **Conventional commit check** — all commits must follow the [conventional commits](https://www.conventionalcommits.org/) format.
- **Linting** — code is formatted with [Black](https://github.com/psf/black).
- **Tests and coverage** — pytest runs with coverage reported to [SonarCloud](https://sonarcloud.io/dashboard?id=Club-JDR_questmaster) for code quality analysis.

On merge to `main`, the CI also pushes the Docker image to GHCR and [release-please](https://github.com/googleapis/release-please) creates or updates a release PR. Merging that PR creates a GitHub release and a version tag automatically.

Dependencies are kept up to date by [Renovate](https://docs.renovatebot.com/), which opens PRs for new versions of Python packages, Docker base images, and GitHub Actions.

## Contributing

1. Fork the repo and create a branch from `main`.
2. Use [conventional commits](https://www.conventionalcommits.org/) for all commit messages. Examples:
   - `feat: add trophy leaderboard`
   - `fix: prevent duplicate session registrations`
   - `docs: update local setup instructions`
3. Format your code with [Black](https://github.com/psf/black) before pushing:

   ```sh
   black .
   ```

4. Make sure tests pass:

   ```sh
   python -m pytest tests/
   ```

5. Open a pull request against `main`.

## Roadmap

The project is evolving toward a cleaner architecture:

- **Repository + service layers** — decouple data access and business logic from Flask views using a repository layer (queries) and a service layer (transactions, validation). Being rolled out incrementally as vertical slices.
- **API + frontend split** — move from a monolithic Flask app with server-rendered templates to a Flask REST API backend and a Vue.js frontend.

## Join us

Contributions are welcome! You can help by:

- Opening a [bug report](https://github.com/Club-JDR/questmaster/issues/new?template=bug_report.md) or a [feature request](https://github.com/Club-JDR/questmaster/issues/new?template=feature_request.md).
- Picking up an open issue and submitting a pull request.

If you're just looking to play tabletop RPGs with us, head over to [club-jdr.fr](https://club-jdr.fr).
