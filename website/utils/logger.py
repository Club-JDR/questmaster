import logging
from flask import g
from website.extensions import db
from website.models import GameEvent


class RequestLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        trace_id = getattr(g, "trace_id", "no-trace-id")
        return f"[trace_id={trace_id}] {msg}", kwargs


def configure_logging(level=logging.INFO):
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    if not root_logger.handlers:
        root_logger.addHandler(handler)


logger = RequestLoggerAdapter(logging.getLogger(__name__), {})


def log_game_event(action, game_id, description=None):
    event = GameEvent(
        action=action,
        game_id=game_id,
        description=description,
    )
    db.session.add(event)
    db.session.commit()
