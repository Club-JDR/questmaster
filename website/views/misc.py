from flask import Blueprint, render_template, flash, request, redirect, url_for
from config.constants import (
    BADGE_CAMPAIGN_GM_ID,
    BADGE_CAMPAIGN_ID,
    BADGE_OS_GM_ID,
    BADGE_OS_ID,
)
from website.views.auth import who
from website.extensions import cache
from website.services.system import SystemService
from website.services.vtt import VttService
from website.services.user import UserService
from website.services.trophy import TrophyService
from website.exceptions import NotFoundError

misc_bp = Blueprint("misc", __name__)


@misc_bp.route("/vtts/", methods=["GET"])
def list_vtts():
    """
    List all VTTs.
    """
    return render_template("list.j2", items=VttService().get_all(), title="Virtual TableTops")


@misc_bp.route("/systemes/", methods=["GET"])
def list_systems():
    """
    List all Systems.
    """
    return render_template("list.j2", items=SystemService().get_all(), title="Systèmes")


@misc_bp.route("/badges/", methods=["GET"])
def list_user_badges():
    """
    List all badges for the current user or for a specific user by their ID.
    """
    user_id = request.args.get("user_id")

    if not user_id:
        payload = who()
        user_id = payload["user_id"]

    try:
        user = UserService().get_by_id(user_id)
    except NotFoundError:
        flash(
            'Utilisateur introuvable. Veuillez entrer un ID valide.<br>Si vous ne savez pas comment le trouver, vous pouvez consulter <a href="https://support.discord.com/hc/fr/articles/206346498-O%C3%B9-trouver-l-ID-de-mon-compte-utilisateur-serveur-message"             target="_blank" rel="noopener noreferrer">cet article.</a>',
            "danger",
        )
        return redirect(url_for("misc.list_user_badges"))

    return render_template(
        "trophies.j2",
        trophies=user.trophy_summary,
        user_id=user.id,
        user=user,
    )


@cache.cached(timeout=3600, key_prefix="leaderboard_os")
def get_os_leaderboard():
    """Get leaderboard for one-shot player badge.

    Returns:
        List of (User, total_quantity) tuples.
    """
    return TrophyService().get_leaderboard(BADGE_OS_ID, limit=10)


@cache.cached(timeout=3600, key_prefix="leaderboard_campaign")
def get_campaign_leaderboard():
    """Get leaderboard for campaign player badge.

    Returns:
        List of (User, total_quantity) tuples.
    """
    return TrophyService().get_leaderboard(BADGE_CAMPAIGN_ID, limit=10)


@cache.cached(timeout=3600, key_prefix="leaderboard_os_gm")
def get_os_gm_leaderboard():
    """Get leaderboard for one-shot GM badge.

    Returns:
        List of (User, total_quantity) tuples.
    """
    return TrophyService().get_leaderboard(BADGE_OS_GM_ID, limit=10)


@cache.cached(timeout=3600, key_prefix="leaderboard_campaign_gm")
def get_campaign_gm_leaderboard():
    """Get leaderboard for campaign GM badge.

    Returns:
        List of (User, total_quantity) tuples.
    """
    return TrophyService().get_leaderboard(BADGE_CAMPAIGN_GM_ID, limit=10)


@misc_bp.route("/badges/classement/", methods=["GET"])
def trophies_leaderboard():
    """
    View the leaderboard for the permanent trophies.
    """
    return render_template(
        "trophies_leaderboard.j2",
        os_leaderboard=get_os_leaderboard(),
        campaign_leaderboard=get_campaign_leaderboard(),
        os_gm_leaderboard=get_os_gm_leaderboard(),
        campaign_gm_leaderboard=get_campaign_gm_leaderboard(),
    )
