"""Miscellaneous views for VTTs, systems, badges, and leaderboards."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from markupsafe import Markup

from config.constants import BADGE_CAMPAIGN_GM_ID, BADGE_CAMPAIGN_ID, BADGE_OS_GM_ID, BADGE_OS_ID
from website.exceptions import NotFoundError
from website.extensions import cache
from website.services.special_event import SpecialEventService
from website.services.trophy import TrophyService
from website.services.user import UserService
from website.services.vtt import VttService
from website.views.auth import login_required, who

misc_bp = Blueprint("misc", __name__)

# Service instances
vtt_service = VttService()
user_service = UserService()
trophy_service = TrophyService()
special_event_service = SpecialEventService()


@misc_bp.route("/aide/commandes-discord/", methods=["GET"])
def discord_commands_help():
    """Render the help page for the Discord slash commands."""
    return render_template("discord_commands.j2")


@misc_bp.route("/vtts/", methods=["GET"])
def list_vtts():
    """List all VTTs."""
    vtts = [v.to_dict() for v in vtt_service.get_all()]
    return render_template("list.j2", items=vtts, title="Virtual TableTops", icon="ph-desktop")


@misc_bp.route("/badges/", methods=["GET"])
@login_required
def list_user_badges():
    """List all badges for the current user or for a specific user by ID."""
    user_id = request.args.get("user_id")

    if not user_id:
        payload = who()
        user_id = payload["user_id"]

    try:
        user = user_service.get_by_id(user_id)
    except NotFoundError:
        # Markup: static, developer-authored HTML — flash messages are
        # autoescaped like everything else.
        flash(
            Markup(
                "Utilisateur introuvable. Veuillez entrer un ID valide.<br>"
                "Si vous ne savez pas comment le trouver, vous pouvez consulter "
                '<a href="https://support.discord.com/hc/fr/articles/'
                "206346498-O%C3%B9-trouver-l-ID-de-mon-compte-utilisateur-"
                'serveur-message" target="_blank" rel="noopener noreferrer">'
                "cet article.</a>"
            ),
            "danger",
        )
        return redirect(url_for("misc.list_user_badges"))

    return render_template(
        "trophies.j2",
        trophies=user.trophy_summary,
        user_id=user.id,
        user=user.to_dict(),
    )


@cache.cached(timeout=3600, key_prefix="leaderboard_os")
def get_os_leaderboard():
    """Get leaderboard for one-shot player badge.

    Returns:
        List of (User, total_quantity) tuples.
    """
    return trophy_service.get_leaderboard(BADGE_OS_ID, limit=10)


@cache.cached(timeout=3600, key_prefix="leaderboard_campaign")
def get_campaign_leaderboard():
    """Get leaderboard for campaign player badge.

    Returns:
        List of (User, total_quantity) tuples.
    """
    return trophy_service.get_leaderboard(BADGE_CAMPAIGN_ID, limit=10)


@cache.cached(timeout=3600, key_prefix="leaderboard_os_gm")
def get_os_gm_leaderboard():
    """Get leaderboard for one-shot GM badge.

    Returns:
        List of (User, total_quantity) tuples.
    """
    return trophy_service.get_leaderboard(BADGE_OS_GM_ID, limit=10)


@cache.cached(timeout=3600, key_prefix="leaderboard_campaign_gm")
def get_campaign_gm_leaderboard():
    """Get leaderboard for campaign GM badge.

    Returns:
        List of (User, total_quantity) tuples.
    """
    return trophy_service.get_leaderboard(BADGE_CAMPAIGN_GM_ID, limit=10)


def clear_leaderboard_cache() -> None:
    """Drop every cached badge leaderboard (global tabs + per-event).

    The four global leaderboards are plain view functions cached under a
    fixed ``key_prefix``, not memoized service methods, so they're cleared by
    exact key rather than ``delete_memoized``. Used by ``flask clear-cache
    badges`` and after an admin manually awards/revokes a trophy.
    """
    cache.delete("leaderboard_os")
    cache.delete("leaderboard_campaign")
    cache.delete("leaderboard_os_gm")
    cache.delete("leaderboard_campaign_gm")
    cache.delete_memoized(get_event_leaderboard)


def _serialize_leaderboard(entries):
    """Convert (User, count) tuples to (dict, count) tuples."""
    return [(user.to_dict(), count) for user, count in entries]


@cache.memoize(timeout=3600)
def get_event_leaderboard(event_id: int) -> dict | None:
    """Get the player/GM leaderboards for a special event, memoized per event.

    Args:
        event_id: Special event ID.

    Returns:
        Dict with keys ``event``, ``player_leaderboard``, ``gm_leaderboard``
        (see ``SpecialEventService.get_leaderboard``), or None if the event
        doesn't exist.
    """
    try:
        return special_event_service.get_leaderboard(event_id)
    except NotFoundError:
        return None


@misc_bp.route("/badges/classement/", methods=["GET"])
def trophies_leaderboard():
    """Render the trophy leaderboard page.

    Includes a "Global" tab (badge-based leaderboards) and an "Événements"
    tab where a dropdown selects any special event (active or past) to see
    its own player/GM leaderboard, scoped by game count.
    """
    event_id = request.args.get("event", type=int)
    event_leaderboard = None
    if event_id is not None:
        result = get_event_leaderboard(event_id)
        if result is None:
            flash("Événement introuvable.", "warning")
        else:
            event_leaderboard = {
                "event": result["event"].to_dict(),
                "player_leaderboard": _serialize_leaderboard(result["player_leaderboard"]),
                "gm_leaderboard": _serialize_leaderboard(result["gm_leaderboard"]),
            }

    return render_template(
        "trophies_leaderboard.j2",
        os_leaderboard=_serialize_leaderboard(get_os_leaderboard()),
        campaign_leaderboard=_serialize_leaderboard(get_campaign_leaderboard()),
        os_gm_leaderboard=_serialize_leaderboard(get_os_gm_leaderboard()),
        campaign_gm_leaderboard=_serialize_leaderboard(get_campaign_gm_leaderboard()),
        special_events=[e.to_dict() for e in special_event_service.get_all()],
        selected_event_id=event_id,
        event_leaderboard=event_leaderboard,
    )
