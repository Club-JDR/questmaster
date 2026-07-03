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
# Each entry's ``permission`` is the capability that unlocks the section for a
# delegated (non-admin) user. ``None`` means admin-only (no capability grants it).
ADMIN_SECTIONS = [
    {
        "endpoint": "admin.list_users",
        "label": "Utilisateurs",
        "icon": "ph-users",
        "permission": "users.view",
    },
    {
        "endpoint": "admin.list_games",
        "label": "Annonces",
        "icon": "ph-scroll",
        "permission": None,
    },
    {
        "endpoint": "admin.list_special_events",
        "label": "Événements",
        "icon": "ph-sparkle",
        "permission": "special_event.manage",
    },
    {
        "endpoint": "admin.list_trophies",
        "label": "Badges",
        "icon": "ph-trophy",
        "permission": "trophy.manage",
    },
    {
        "endpoint": "admin.list_systems",
        "label": "Systèmes",
        "icon": "ph-cube",
        "permission": "system.manage",
    },
    {
        "endpoint": "admin.list_vtts",
        "label": "VTTs",
        "icon": "ph-desktop",
        "permission": "vtt.manage",
    },
    {
        "endpoint": "admin.list_channels",
        "label": "Catégories (salons)",
        "icon": "ph-hash",
        "permission": "channel.manage",
    },
    {
        "endpoint": "admin.list_game_events",
        "label": "Audit des annonces",
        "icon": "ph-scroll",
        "permission": "game_event.view",
    },
    {
        "endpoint": "admin.list_app_logs",
        "label": "Journaux applicatifs",
        "icon": "ph-terminal-window",
        "permission": "app_log.view",
    },
    {
        "endpoint": "admin.list_discord_messages",
        "label": "Messages Discord",
        "icon": "ph-paper-plane-tilt",
        "permission": "discord.send",
    },
    {
        "endpoint": "admin.list_permissions",
        "label": "Permissions",
        "icon": "ph-shield-check",
        "permission": "permissions.manage",
    },
    {
        "endpoint": "admin.edit_settings",
        "label": "Paramètres",
        "icon": "ph-sliders",
        "permission": None,
    },
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
    """Check whether the current session may reach the admin panel.

    Admins always pass; a delegated user holding at least one granted
    capability may reach the panel (per-route ``require_permission`` then
    enforces the specific capability).

    Returns:
        True if the session is an admin or holds ≥1 permission.
    """
    if "user_id" not in session:
        return False
    return bool(session.get("is_admin") or session.get("permissions"))


@admin_bp.before_request
def require_admin():
    """Reject any request to the admin panel without admin access.

    Raises:
        UnauthorizedError: If the current session is neither an admin nor holds
            any granted capability.
    """
    if not is_admin_authenticated():
        raise UnauthorizedError(MSG_ADMIN_ACCESS_REQUIRED, action="admin")


@admin_bp.app_context_processor
def inject_admin_sections():
    """Expose the (permission-filtered) admin sub-section list to templates.

    Admins see every section; a delegated user sees only the sections their
    granted capabilities unlock.

    Returns:
        Dict with the ``admin_sections`` template variable.
    """
    perms = session.get("permissions", [])
    is_admin = session.get("is_admin", False)
    visible = [
        section
        for section in ADMIN_SECTIONS
        if is_admin or (section.get("permission") and section["permission"] in perms)
    ]
    return {"admin_sections": visible}


@admin_bp.route("/", methods=["GET"])
def index():
    """Render the admin dashboard."""
    return render_template("admin/index.html")


# Import route modules so their routes register on ``admin_bp``.
from website.views.admin import (  # noqa: E402,F401
    app_logs,
    channels,
    discord_messages,
    game_events,
    games,
    permissions,
    settings,
    special_events,
    systems,
    trophies,
    users,
    vtts,
)
