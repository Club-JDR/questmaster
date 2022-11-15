# QuestMaster

[![CI](https://github.com/Club-JDR/questmaster/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Club-JDR/questmaster/actions/workflows/ci.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Club-JDR_questmaster&metric=alert_status)](https://sonarcloud.io/dashboard?id=Club-JDR_questmaster)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

The Club JDR booking app for roleplaying sessions.

This app is meant for GMs to create new Games with all the details (name, type, number of players, date and time of the sessions etc..) and for players to be able to register for the games. It interacts with the Discord server to automatically create roles and channels for the games.

## Build, run and test

Create a `.env` to set the following variables:

```yaml
FLASK_AUTH_SECRET="topsecret"
DISCORD_CLIENT_ID="1234567890"
DISCORD_CLIENT_SECRET="987654321"
DISCORD_BOT_TOKEN="qwertyuiopasdfghjklzxcvbnm"
DISCORD_REDIRECT_URI="http://localhost:8000/callback"
DISCORD_GUILD_NAME="Club JDR TEST"
POSTGRES_USER="clubjdr"
POSTGRES_PASSWORD="topsecret"
POSTGRES_DB="clubjdr"
UNITTEST_CHANNEL_ID="123456789"
CATEGORIES_CHANNEL_ID="123456789"
DISCORD_GUILD_ID="123456789"
```

Start the complete stack:

```sh
docker-compose build
docker-compose up -d
```
