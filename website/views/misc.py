from flask import Blueprint, render_template, flash, request, redirect, url_for
from website.models import Vtt, System, User, UserTrophy
from website.models.trophy import (
    BADGE_CAMPAIGN_GM_ID,
    BADGE_CAMPAIGN_ID,
    BADGE_OS_GM_ID,
    BADGE_OS_ID,
)
from website.extensions import db
from website.views.auth import who
from website.extensions import cache

misc_bp = Blueprint("misc", __name__)


@misc_bp.route("/vtts/", methods=["GET"])
def list_vtts():
    """
    List all VTTs.
    """
    return render_template(
        "list.j2", payload=who(), items=Vtt.query.all(), title="Virtual TableTops"
    )


@misc_bp.route("/systemes/", methods=["GET"])
def list_systems():
    """
    List all Systems.
    """
    return render_template(
        "list.j2", payload=who(), items=System.query.all(), title="Systèmes"
    )


@misc_bp.route("/badges/", methods=["GET"])
def list_user_badges():
    """
    List all badges for the current user or for a specific user by their ID.
    """
    user_id = request.args.get("user_id")

    if not user_id:
        payload = who()
        user_id = payload["user_id"]

    user = User.query.get(user_id)
    if not user:
        flash(
            'Utilisateur introuvable. Veuillez entrer un ID valide.<br>Si vous ne savez pas comment le trouver, vous pouvez consulter <a href="https://support.discord.com/hc/fr/articles/206346498-O%C3%B9-trouver-l-ID-de-mon-compte-utilisateur-serveur-message"             target="_blank" rel="noopener noreferrer">cet article.</a>',
            "danger",
        )
        return redirect(url_for("misc.list_user_badges"))

    return render_template(
        "trophies.j2",
        payload=who(),
        trophies=user.trophy_summary,
        user_id=user.id,
        user=user,
    )


@misc_bp.route("/badges/classement/", methods=["GET"])
@cache.cached()
def trophies_leaderboard():
    """
    View the leaderboard for the permanent trophies.
    """
    os_leaderboard = (
        db.session.query(User, db.func.sum(UserTrophy.quantity).label("total"))
        .join(UserTrophy)
        .filter(UserTrophy.trophy_id == BADGE_OS_ID)
        .group_by(User)
        .order_by(db.func.sum(UserTrophy.quantity).desc())
        .limit(10)
        .all()
    )

    campaign_leaderboard = (
        db.session.query(User, db.func.sum(UserTrophy.quantity).label("total"))
        .join(UserTrophy)
        .filter(UserTrophy.trophy_id == BADGE_CAMPAIGN_ID)
        .group_by(User)
        .order_by(db.func.sum(UserTrophy.quantity).desc())
        .limit(10)
        .all()
    )

    os_gm_leaderboard = (
        db.session.query(User, db.func.sum(UserTrophy.quantity).label("total"))
        .join(UserTrophy)
        .filter(UserTrophy.trophy_id == BADGE_OS_GM_ID)
        .group_by(User)
        .order_by(db.func.sum(UserTrophy.quantity).desc())
        .limit(10)
        .all()
    )

    campaign_gm_leaderboard = (
        db.session.query(User, db.func.sum(UserTrophy.quantity).label("total"))
        .join(UserTrophy)
        .filter(UserTrophy.trophy_id == BADGE_CAMPAIGN_GM_ID)
        .group_by(User)
        .order_by(db.func.sum(UserTrophy.quantity).desc())
        .limit(10)
        .all()
    )

    return render_template(
        "trophies_leaderboard.j2",
        os_leaderboard=os_leaderboard,
        campaign_leaderboard=campaign_leaderboard,
        os_gm_leaderboard=os_gm_leaderboard,
        campaign_gm_leaderboard=campaign_gm_leaderboard,
    )
