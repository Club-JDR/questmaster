# QuestMaster

[![CI](https://github.com/Club-JDR/questmaster/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Club-JDR/questmaster/actions/workflows/ci.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Club-JDR_questmaster&metric=alert_status)](https://sonarcloud.io/dashboard?id=Club-JDR_questmaster)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The Club JDR booking app for roleplaying sessions.

This app is meant for GMs to create new Games with all the details (name, type, number of players, date and time of the sessions etc..) and for players to be able to register for the games. It interacts with the Discord server to automatically create roles and channels for the games.

## Build, run and test

Create a `.env` to set the following variables:

```yaml
QUESTMASTER_PORT=8000
QUESTMASTER_HOST=0.0.0.0
QUESTMASTER_DB_USER=root
QUESTMASTER_DB_PASSWORD=topsecret
QUESTMASTER_DB_HOST=localhost
```

Start the complete stack:

```sh
docker-compose build api
docker-compose up -d
```

Run tests:

```sh
docker exec -t questmaster_api_1  npm run test
```

Manually run the api on dev mode:

```sh
# stop the containerized api
docker stop questmaster_api_1
# then
cd api/
npm install && npm run dev
# in another terminal you can run the tests locally too:
npm run test
```
