# QuestMaster

[![CI](https://github.com/Club-JDR/questmaster/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Club-JDR/questmaster/actions/workflows/ci.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Club-JDR_questmaster&metric=alert_status)](https://sonarcloud.io/dashboard?id=Club-JDR_questmaster)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

The Club JDR booking app for roleplaying sessions.

This app is meant for GMs to create new Games with all the details (name, type, number of players, date and time of the sessions etc..) and for players to be able to register for the games. It interacts with the Discord server to automatically create roles and channels for the games.

## Build, run and test

Create a `.env` to set the following variables:

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
POSTGRES_HOST="db" # localhost if usgin flask outside Docker
REDIS_HOST="redis" # localhost if usgin flask outside Docker
DISCORD_GUILD_ID=""
DISCORD_GM_ROLE_ID=""
DISCORD_ADMIN_ROLE_ID=""
ADMIN_CHANNEL_ID="" 
DISCORD_PLAYER_ROLE_ID=""
POSTS_CHANNEL_ID=""
ADMIN_CHANNEL_ID=""
UNITTEST_CHANNEL_ID=""
FLASK_APP="website"
```

### Using docker compose

Start the complete stack:

```sh
docker compose up -d --build
# For the first start, you need to run the migrations to init the database:
docker compose run app flask db upgrade
```

To run the tests:

```sh
docker compose run app-test python -m pytest tests/ website
```

### Locally

Edit the `.env` to change the `POSTGRES_HOST` value to `localhost`.
Run at least the database and eventually pgadmin:

```sh
docker compose down && docker compose up -d --build db pgadmin
```

Then, you can run the migrations and start the app:

```sh
flask db upgrade
flask run -p 8000
# Or in debug if you don't want to restart it at every code change
flask --app website --debug run -p 8000
```

To run the tests:

```sh
python -m pytest tests/ website
```

### Flask shell

You can connect to a shell (to test your models, interact with the database and so on) by simply running:

```sh
# if using docker compose
docker compose run app flask shell
# if running locally
flask shell
```
