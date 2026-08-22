"""Public system pages: system details plus lightweight matchmaking.

Shows who already runs a system and who wants to play or run it, so a GM
can gauge demand before pitching a game. Deliberately no contact mechanism
(no DM, no messaging) is built here — the lists are purely informational; a
GM who sees demand reaches out however they already would, fully outside
the app.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from config.constants import SYSTEM_INTEREST_ROLE_GM
from website.exceptions import ValidationError
from website.services.system import SystemService
from website.views.auth import abort_if_not_gm, login_required, who

systems_bp = Blueprint("systems", __name__, url_prefix="/systemes")

system_service = SystemService()


@systems_bp.route("/", methods=["GET"])
def list_systems():
    """List all game systems, linking each to its public page."""
    systems = [s.to_dict() for s in system_service.get_all()]
    return render_template(
        "list.j2",
        items=systems,
        title="Systèmes",
        icon="ph-cube",
        detail_endpoint="systems.get_system",
    )


@systems_bp.route("/<int:system_id>/", methods=["GET"])
def get_system(system_id):
    """Display a system's public page: description/link + matchmaking lists."""
    payload = who()
    user_id = payload.get("user_id")
    page = system_service.get_public_page(system_id, user_id)

    return render_template(
        "system_details.j2",
        system=page["system"].to_dict(),
        gm_history=[u.to_dict() for u in page["gm_history"]],
        gms_interested=[i.user.to_dict() for i in page["gms_interested"]],
        players_interested=[i.user.to_dict() for i in page["players_interested"]],
        my_interests=page["my_interests"],
    )


@systems_bp.route("/<int:system_id>/interet/", methods=["POST"])
@login_required
def toggle_interest(system_id):
    """Add/remove the current user's declared interest for a system.

    Declaring GM interest requires GM access, mirroring the gate used for
    game-form preferences — a player can't signal "I want to run this".
    """
    payload = who()
    role = request.form.get("role")
    if role == SYSTEM_INTEREST_ROLE_GM:
        abort_if_not_gm(payload)

    try:
        added = system_service.toggle_interest(
            system_id, payload["user_id"], role, note=request.form.get("note") or None
        )
    except ValidationError:
        flash("Rôle d'intérêt invalide.", "danger")
        return redirect(url_for("systems.get_system", system_id=system_id))

    flash("Intérêt enregistré." if added else "Intérêt retiré.", "success")
    return redirect(url_for("systems.get_system", system_id=system_id))
