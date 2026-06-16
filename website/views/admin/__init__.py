"""Custom admin blueprint (DaisyUI) replacing the legacy Flask-Admin panel.

The blueprint is mounted at ``/admin`` and exposes one sub-section per model,
each implemented as plain Flask routes that delegate to the existing service
layer. Access is gated to authenticated admins via a ``before_request`` guard.
"""

# Standard library imports

# Third-party imports
from flask import Blueprint, render_template, request, session

# Local imports
from config.constants import MSG_ADMIN_ACCESS_REQUIRED
from website.exceptions import UnauthorizedError

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Ordered list of admin sub-sections, used to render the navigation dropdown
# in the main navbar and the sidebar inside the admin layout.
ADMIN_SECTIONS = [
    {"endpoint": "admin.list_users", "label": "Utilisateurs", "icon": "ph-users"},
    {"endpoint": "admin.list_games", "label": "Annonces", "icon": "ph-scroll"},
    {"endpoint": "admin.list_special_events", "label": "Événements", "icon": "ph-sparkle"},
    {"endpoint": "admin.list_trophies", "label": "Badges", "icon": "ph-trophy"},
    {"endpoint": "admin.list_systems", "label": "Systèmes", "icon": "ph-cube"},
    {"endpoint": "admin.list_vtts", "label": "VTTs", "icon": "ph-desktop"},
    {"endpoint": "admin.list_channels", "label": "Catégories (salons)", "icon": "ph-hash"},
    {"endpoint": "admin.list_game_events", "label": "Journaux", "icon": "ph-scroll"},
    {"endpoint": "admin.edit_settings", "label": "Paramètres", "icon": "ph-sliders"},
]


def get_list_params() -> tuple[int, str | None]:
    """Parse common ``page`` and ``q`` query-string params for list views.

    Returns:
        Tuple of (page, search) where page is a 1-based int and search is the
        trimmed query string, or None when absent/empty.
    """
    page = request.args.get("page", 1, type=int)
    search = (request.args.get("q") or "").strip() or None
    return page, search


def is_admin_authenticated() -> bool:
    """Check whether the current session belongs to an authenticated admin.

    Returns:
        True if the session has a user ID and the admin flag set.
    """
    return "user_id" in session and session.get("is_admin", False)


@admin_bp.before_request
def require_admin():
    """Reject any non-admin request to the admin panel.

    Raises:
        UnauthorizedError: If the current session is not an authenticated admin.
    """
    if not is_admin_authenticated():
        raise UnauthorizedError(MSG_ADMIN_ACCESS_REQUIRED, action="admin")


@admin_bp.app_context_processor
def inject_admin_sections():
    """Expose the admin sub-section list to all templates (for the navbar).

    Returns:
        Dict with the ``admin_sections`` template variable.
    """
    return {"admin_sections": ADMIN_SECTIONS}


@admin_bp.route("/", methods=["GET"])
def index():
    """Render the admin dashboard."""
    return render_template("admin/index.html")


# Import route modules so their routes register on ``admin_bp``.
from website.views.admin import (  # noqa: E402,F401
    channels,
    game_events,
    games,
    settings,
    special_events,
    systems,
    trophies,
    users,
    vtts,
)
