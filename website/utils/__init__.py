"""Utility modules for logging, filters, and helpers."""

import os
from importlib.metadata import version


def get_app_version() -> str:
    """Return the application version.

    Reads the version from the installed package metadata (pyproject.toml),
    falling back to the TAG environment variable (set by docker-compose).

    Returns:
        The application version string, or 'dev' if neither source is available.
    """
    try:
        return version("questmaster")
    except Exception:
        pass
    tag = os.environ.get("TAG")
    if tag:
        return tag
    return "dev"
