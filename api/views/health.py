from flask import jsonify
from api import app
from datetime import datetime
import psutil, os, time


def dhms_from_seconds(seconds) -> str:
    """
    Convert a datetime from seconds to d:h:m:s format.
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"


@app.route("/health/")
def health():
    """
    Health endpoint
    """
    start_time = psutil.Process(os.getpid()).create_time()
    delta = datetime.now() - datetime.fromtimestamp(start_time)
    uptime = dhms_from_seconds(delta.seconds)
    now = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
    return (
        jsonify(
            {
                "title": "QuestMaster API",
                "version": 1,
                "status": "OK",
                "uptime": uptime,
                "date": now,
            }
        ),
        200,
    )
