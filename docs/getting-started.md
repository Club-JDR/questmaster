# Getting Started

## Prerequisites

### Discord bot and test server

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

### Environment variables

Create a `.env` file at the root of the project with the values from the previous step:

```ini
FLASK_AUTH_SECRET=""
JWT_SECRET_KEY=""
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

Generate values for `FLASK_AUTH_SECRET` and `JWT_SECRET_KEY` using Python:

```python
import secrets
secrets.token_urlsafe(64)
```

If `JWT_SECRET_KEY` is not set, it falls back to `FLASK_AUTH_SECRET`. Using a dedicated key is recommended in production.

## Using Docker Compose (recommended)

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
# Unit tests only (no Discord credentials needed)
docker compose run app-test python -m pytest tests/ -m "not integration"

# All tests including E2E and live Discord API tests
docker compose run app-test python -m pytest tests/
```

## Local development

Edit the `.env` to change `POSTGRES_HOST` and `REDIS_HOST` to `localhost`.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it:

```sh
pip install uv
```

Install the dependencies into a local virtual environment:

```sh
uv sync --extra test --extra lint
```

This creates a `.venv` in the project root. Either activate it for the session, or prefix every command below with `uv run`:

```sh
# activate (one time per shell session)
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\Activate.ps1       # Windows PowerShell
```

Build the frontend assets (requires [Node.js](https://nodejs.org/) 22+):

```sh
npm install
npm run build       # or: npm run dev  (watch mode, rebuilds on file changes)
```

> **Docker Compose users**: skip this step — the Docker build runs `npm ci && npm run build` automatically in a dedicated `frontend-builder` stage.

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
# Unit tests only (no Discord credentials needed)
python -m pytest tests/ -m "not integration"

# All tests including E2E and live Discord API tests (requires .env with Discord credentials)
python -m pytest tests/
```

## Setup test database

The test database is automatically set up (and destroyed afterwards) when running the tests. However, you can seed the database for manual testing by running:

```sh
flask setup-test-db
```

## Building the documentation locally

Install the docs dependencies:

```sh
uv sync --extra docs
```

Serve the documentation with live reload:

```sh
mkdocs serve
```

The site will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

_Note: the same port is used for the app. Either run bot separately or change the port using `-a localhost:<port>`._
