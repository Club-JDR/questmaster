from flask import jsonify, request
from api import app, db
from datetime import datetime
import psutil, os


def dhms_from_seconds(seconds) -> str:
    """
    Convert a datetime from seconds to d:h:m:s format.
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"


@app.route("/health/", methods=["GET"])
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
        db.session.execute("SELECT 1")
    except Exception:
        db_status = "ERROR"
    return (
        jsonify(
            {
                "title": "QuestMaster API",
                "version": 1,
                "status": "OK",
                "database": db_status,
                "uptime": uptime,
                "date": now,
            }
        ),
        200,
    )
