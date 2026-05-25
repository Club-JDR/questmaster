"""Vite manifest helper for resolving hashed static asset URLs."""

import json
from functools import lru_cache
from pathlib import Path

from flask import current_app

_MANIFEST = Path(__file__).parent.parent / "static" / "dist" / ".vite" / "manifest.json"


@lru_cache(maxsize=None)
def _load_manifest() -> dict:
    """Load and cache the Vite manifest.json from the build output.

    Returns:
        Parsed manifest as a dictionary mapping source paths to build outputs.

    Raises:
        FileNotFoundError: If the manifest does not exist (assets not built yet).
    """
    if not _MANIFEST.exists():
        raise FileNotFoundError(f"Vite manifest not found at {_MANIFEST}. Run 'npm run build'.")
    with _MANIFEST.open() as f:
        return json.load(f)


def asset_css(filename: str) -> list[str]:
    """Return CSS side-effect URLs for a JS entry from the Vite manifest.

    Args:
        filename: JS entry key as declared in vite.config.js input.

    Returns:
        List of /static/dist/-rooted URL paths for associated CSS files.
    """
    if current_app.debug:
        _load_manifest.cache_clear()
    return ["/static/dist/" + f for f in _load_manifest()[filename].get("css", [])]


def asset(filename: str) -> str:
    """Resolve a hashed asset URL from the Vite manifest.

    In debug mode the manifest cache is cleared on every call so changes
    from watch mode are reflected immediately without restarting Flask.

    Args:
        filename: Source asset key as declared in vite.config.js input
            (e.g. "assets/css/main.css" or "assets/js/main.js").

    Returns:
        URL path to the hashed file under /static/dist/.

    Raises:
        KeyError: If filename is not found in the manifest.
        FileNotFoundError: If the Vite manifest has not been built yet.
    """
    if current_app.debug:
        _load_manifest.cache_clear()
    return "/static/dist/" + _load_manifest()[filename]["file"]
