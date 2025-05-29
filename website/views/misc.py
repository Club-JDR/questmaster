from flask import (
    Blueprint,
    render_template,
)
from website.models import Vtt, System
from website.views.auth import who

misc_bp = Blueprint("misc", __name__)


@misc_bp.route("/vtts/", methods=["GET"])
def list_vtts():
    """
    List all VTTs.
    """
    v = Vtt.query.all()
    return render_template(
        "list.j2", payload=who(), items=v, item="vtts", title="Virtual TableTops"
    )


@misc_bp.route("/systemes/", methods=["GET"])
def list_systems():
    """
    List all Systems.
    """
    s = System.query.all()
    return render_template(
        "list.j2", payload=who(), items=s, item="systems", title="Systèmes"
    )
