"""API error handling.

JSON error responses for API routes are handled centrally in
``website.views.errors`` via the ``_wants_json()`` guard, which checks
``request.path.startswith("/api/")``.

This module is reserved for any future API-specific error utilities.
"""
