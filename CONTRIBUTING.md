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

- Format with [Black](https://github.com/psf/black): `black .`
- Sort imports with [isort](https://pycqa.github.io/isort/): `isort .`
- Lint with [flake8](https://flake8.pycqa.org/): `flake8 website/`
- Lint docstrings (google-style) with [pydoclint](https://github.com/jsh9/pydoclint): `pydoclint website/`

A [pre-commit](https://pre-commit.com/) configuration is provided. Install the hooks to run these checks automatically before each commit:

```sh
pip install pre-commit
pre-commit install
```

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
  python -m pytest tests/ -m "not integration"
  ```

## CI Pipeline

Every pull request is checked by the CI pipeline which runs:

- **Conventional commit check** — all commits must follow the [conventional commits](https://www.conventionalcommits.org/) format.
- **Linting** — import ordering with [isort](https://pycqa.github.io/isort/), formatting with [Black](https://github.com/psf/black), static analysis with [flake8](https://flake8.pycqa.org/) and docstring lint with [pydoclint](https://github.com/jsh9/pydoclint).
- **Tests and coverage** — pytest runs with coverage reported to [SonarCloud](https://sonarcloud.io/dashboard?id=Club-JDR_questmaster) for code quality analysis.

On merge to `main`, [release-please](https://github.com/googleapis/release-please) creates or updates a release PR. Merging that PR creates a GitHub release and a version tag automatically, the CI also pushes the Docker image to GHCR.

Dependencies are kept up to date by [Renovate](https://docs.renovatebot.com/), which opens PRs for new versions of Python packages, Docker base images, and GitHub Actions.

## Reporting issues

- [Bug report](https://github.com/Club-JDR/questmaster/issues/new?template=bug_report.md)
- [Feature request](https://github.com/Club-JDR/questmaster/issues/new?template=feature_request.md)
