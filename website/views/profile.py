"""User preferences views: personal defaults for the game creation form."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from website.services.system import SystemService
from website.services.user import UserService
from website.services.vtt import VttService
from website.utils.form_parsers import get_ambience
from website.views.auth import abort_if_not_gm, login_required, who

profile_bp = Blueprint("profile", __name__)

user_service = UserService()
system_service = SystemService()
vtt_service = VttService()


@profile_bp.route("/preferences/", methods=["GET"])
@login_required
def preferences():
    """Show the current user's saved game-form default preferences.

    GM-only: these defaults only ever prefill the game creation form.
    """
    payload = who()
    abort_if_not_gm(payload)
    user = user_service.get_by_id(payload["user_id"])
    return render_template(
        "user_preferences.j2",
        game_defaults=user.game_defaults or {},
        systems=system_service.get_all(),
        vtts=vtt_service.get_all(),
    )


@profile_bp.route("/preferences/", methods=["POST"])
@login_required
def update_preferences():
    """Save the current user's game-form default preferences.

    GM-only: these defaults only ever prefill the game creation form.
    """
    payload = who()
    abort_if_not_gm(payload)
    data = request.values.to_dict()
    data["ambience"] = get_ambience(data)
    user_service.update_game_defaults(payload["user_id"], data)
    flash("Préférences mises à jour.", "success")
    return redirect(url_for("profile.preferences"))
