"""Admin "view-as" (user impersonation) routes.

Kept as its own blueprint — rather than living under ``admin_bp`` — because
the "stop" route must stay reachable even after the session's ``is_admin``
flag has been downgraded to the impersonated user's (no privilege
retention), which would otherwise be rejected by ``admin_bp``'s blanket
``require_admin`` guard.
"""

# Standard library imports
import logging

# Third-party imports
from flask import Blueprint, flash, redirect, request, session, url_for

# Local imports
from website.exceptions import NotFoundError, ValidationError
from website.services.user import UserService
from website.utils.logger import sanitize_log_value
from website.views.auth import admin_only, login_required, session_fields

logger = logging.getLogger(__name__)

view_as_bp = Blueprint("view_as", __name__, url_prefix="/admin/view-as")

user_service = UserService()


@view_as_bp.route("/<user_id>/", methods=["POST"])
@admin_only
def start(user_id):
    """Start impersonating another user as a superuser admin."""
    if "impersonator_id" in session:
        flash("Vous incarnez déjà un autre utilisateur.", "warning")
        return redirect(url_for("annonces.dashboard"))

    try:
        target = user_service.validate_impersonation_target(session["user_id"], user_id)
    except ValidationError:
        flash("Vous ne pouvez pas vous incarner vous-même.", "danger")
        return redirect(request.referrer or url_for("admin.list_users"))
    except NotFoundError:
        flash("Utilisateur introuvable.", "danger")
        return redirect(url_for("admin.list_users"))

    target.refresh_roles()
    impersonator_id = session["user_id"]
    impersonator_username = session.get("username")
    session["impersonator_id"] = impersonator_id
    session["impersonator_username"] = impersonator_username
    session.update(session_fields(target))
    logger.info(
        f"Admin {sanitize_log_value(impersonator_id)} started impersonating user "
        f"{sanitize_log_value(target.id)}"
    )
    flash(f"Vous incarnez maintenant {target.name}.", "success")
    return redirect(url_for("annonces.dashboard"))


@view_as_bp.route("/stop/", methods=["POST"])
@login_required
def stop():
    """Stop impersonating and restore the real admin's session."""
    impersonator_id = session.get("impersonator_id")
    if not impersonator_id:
        return redirect(url_for("annonces.dashboard"))

    impersonated_id = session.get("user_id")
    logger.info(
        f"Admin {sanitize_log_value(impersonator_id)} stopped impersonating user "
        f"{sanitize_log_value(impersonated_id)}"
    )

    try:
        admin = user_service.get_by_id(impersonator_id)
    except NotFoundError:
        # The real admin account vanished mid-impersonation; clear the
        # session entirely rather than leaving a half-restored state.
        session.clear()
        flash("Compte administrateur introuvable, session réinitialisée.", "danger")
        return redirect(url_for("annonces.dashboard"))

    admin.refresh_roles()
    session.pop("impersonator_id", None)
    session.pop("impersonator_username", None)
    session.update(session_fields(admin))
    flash("Vous avez repris votre propre compte.", "success")
    return redirect(url_for("annonces.dashboard"))
