from flask import jsonify, Blueprint
from website.extensions import db
from datetime import datetime
from sqlalchemy.sql import text
import psutil, os


health_bp = Blueprint("health", __name__)


def dhms_from_seconds(seconds) -> str:
    """
    Convert a datetime from seconds to d:h:m:s format.
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"


@health_bp.route("/health/", methods=["GET"])
def health():
    """
    Health endpoint
    """
    start_time = psutil.Process(os.getpid()).create_time()
    delta = datetime.now() - datetime.fromtimestamp(start_time)
    uptime = dhms_from_seconds(delta.seconds)
    now = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
    db_status = "OK"
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db_status = "ERROR"
    return (
        jsonify(
            {
                "title": "QuestMaster",
                "version": 1,
                "status": "OK",
                "database": db_status,
                "uptime": uptime,
                "date": now,
            }
        ),
        200,
    )
