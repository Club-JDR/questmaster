from flask import (
    Blueprint,
    render_template,
)
from website.models import Vtt, System, User
from website.extensions import db
from website.views.auth import who

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
def list_badges():
    """
    List all Badges for current user.
    """
    payload = who()
    return render_template(
        "trophies.j2",
        payload=payload,
        trophies=db.get_or_404(User, str(payload["user_id"])).trophy_summary,
    )
