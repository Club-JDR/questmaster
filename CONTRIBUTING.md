# Contributing to QuestMaster

Thanks for your interest in contributing! Here's how to get started.

## Getting started

1. Fork the repo and create a branch from `main`.
2. Set up your local environment — see the [Getting Started Guide](docs/getting-started.md) for instructions.
3. Make your changes, following the guidelines below.
4. Open a pull request against `main`.

## Commit messages

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) format. Examples:

- `feat: add trophy leaderboard`
- `fix: prevent duplicate session registrations`
- `refactor: extract game validation into service layer`
- `docs: update local setup instructions`
- `test: add unit tests for UserService`

## Code style

- Format with [Ruff](https://docs.astral.sh/ruff/): `ruff format .`
- Lint and sort imports with [Ruff](https://docs.astral.sh/ruff/): `ruff check .`
- Lint docstrings (google-style) with [pydoclint](https://github.com/jsh9/pydoclint): `pydoclint website/`

A [pre-commit](https://pre-commit.com/) configuration is provided. Install the hooks to run these checks automatically before each commit:

```sh
uv tool install pre-commit
pre-commit install
```

### Frontend

Templates use [DaisyUI v5](https://daisyui.com/) + [Tailwind v4](https://tailwindcss.com/), built with [Vite](https://vitejs.dev/). Source lives in `assets/`; built output goes to `website/static/dist/` (gitignored).

```sh
npm install
npm run build   # production build
npm run dev     # watch mode — rebuilds on changes to assets/
```

Docker Compose users don't need to run this locally — the Docker build handles it automatically in a dedicated `frontend-builder` stage.

## Architecture

The codebase follows a layered architecture. When adding or modifying code, respect these boundaries:

| Layer | Location | Responsibility | Rules |
|---|---|---|---|
| **Models** | `website/models/` | SQLAlchemy models, relationships, constraints | No business logic, no Flask imports |
| **Repositories** | `website/repositories/` | Data access (queries, CRUD) | No validation, no business rules, no Flask context |
| **Services** | `website/services/` | Business logic, validation, transactions | No direct Flask request/session access |
| **Views** | `website/views/` | HTTP handling (parse input, call services, return response) | No business logic |

New logic should go in the **service layer**. Views should stay thin.

## Tests

- Use `pytest`
- Add or update tests when changing service logic
- Mock external services (Discord, VTT APIs)
- Run the test suite before pushing:

  ```sh
  uv run pytest tests/ -m "not integration"
  ```

### Test database lifecycle

Tests run against a real (PostgreSQL) database. Reference data is seeded
idempotently, so the suite can run safely against a database that already
contains data — re-runs won't fail on duplicate keys.

By default, tables are **not** dropped on teardown, so your local test
database is left intact between runs. Pass `--drop-db` to wipe all tables
after the run (used by CI for a guaranteed clean slate):

```sh
uv run pytest tests/ --drop-db
```

Setting the `CI` environment variable has the same effect as `--drop-db`.

## CI Pipeline

Every pull request is checked by the CI pipeline which runs:

- **Conventional commit check** — all commits must follow the [conventional commits](https://www.conventionalcommits.org/) format.
- **Linting** — formatting, import ordering, and static analysis with [Ruff](https://docs.astral.sh/ruff/) and docstring lint with [pydoclint](https://github.com/jsh9/pydoclint).
- **Frontend build** — `npm ci && npm run build` runs in a dedicated Docker stage; built assets are copied into the app image. No Node.js setup is needed in CI.
- **Tests and coverage** — pytest runs with coverage reported to [SonarCloud](https://sonarcloud.io/dashboard?id=Club-JDR_questmaster) for code quality analysis.

On merge to `main`, [release-please](https://github.com/googleapis/release-please) creates or updates a release PR. Merging that PR creates a GitHub release and a version tag automatically, the CI also pushes the Docker image to GHCR.

Dependencies are kept up to date by [Renovate](https://docs.renovatebot.com/), which opens PRs for new versions of Python packages, Docker base images, and GitHub Actions.

## Reporting issues

- [Bug report](https://github.com/Club-JDR/questmaster/issues/new?template=bug_report.md)
- [Feature request](https://github.com/Club-JDR/questmaster/issues/new?template=feature_request.md)
