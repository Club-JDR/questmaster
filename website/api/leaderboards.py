"""Read-only leaderboard endpoint for the QuestMaster API."""

from flask import Blueprint, jsonify

from config.constants import BADGE_CAMPAIGN_GM_ID, BADGE_CAMPAIGN_ID, BADGE_OS_GM_ID, BADGE_OS_ID
from website.api.auth import api_login_required
from website.services.trophy import TrophyService

leaderboards_bp = Blueprint("api_leaderboards", __name__)

# Service instance
trophy_service = TrophyService()


def _serialize_leaderboard(entries: list) -> list[dict]:
    """Serialize leaderboard entries to JSON-compatible dicts.

    Args:
        entries: List of (User, count) tuples from TrophyService.

    Returns:
        List of dicts with user and count keys.
    """
    return [{"user": user.to_dict(), "count": count} for user, count in entries]


@leaderboards_bp.route("/leaderboards/", methods=["GET"])
@api_login_required
def get_leaderboards():
    """Get all trophy leaderboards.

    Returns:
        JSON object with four leaderboard categories, each containing
        a list of user/count entries.
    """
    return jsonify(
        {
            "oneshot_players": _serialize_leaderboard(
                trophy_service.get_leaderboard(BADGE_OS_ID, limit=10)
            ),
            "campaign_players": _serialize_leaderboard(
                trophy_service.get_leaderboard(BADGE_CAMPAIGN_ID, limit=10)
            ),
            "oneshot_gms": _serialize_leaderboard(
                trophy_service.get_leaderboard(BADGE_OS_GM_ID, limit=10)
            ),
            "campaign_gms": _serialize_leaderboard(
                trophy_service.get_leaderboard(BADGE_CAMPAIGN_GM_ID, limit=10)
            ),
        }
    )
