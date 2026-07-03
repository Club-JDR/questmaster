"""AppLog model persisting application log records."""

from datetime import datetime, timezone

from website.extensions import db
from website.models.base import SerializableMixin


class AppLog(db.Model, SerializableMixin):
    """A single application log record written by ``DatabaseLogHandler``.

    ``user_id`` is intentionally *not* a foreign key: log writes must stay
    decoupled from the rest of the schema so a failed lookup can never block
    (or be blocked by) logging.

    Attributes:
        id: Primary key.
        timestamp: When the record was emitted (UTC).
        level: Level name (INFO, WARNING, ...).
        level_no: Numeric level, enabling "this level and above" filtering.
        logger: Dotted logger name.
        message: Redacted, fully interpolated log message.
        trace_id: Request trace ID, when emitted inside a request.
        user_id: Session user ID of the acting user (no FK on purpose).
        username: Session username of the acting user, when available.
        endpoint: Flask endpoint handling the request, when available.
        module: Python module that emitted the record.
        func: Function that emitted the record.
        line: Source line number.
    """

    __tablename__ = "app_log"

    _exclude_fields = []
    _relationship_fields = []

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    level = db.Column(db.String(16), nullable=False)
    level_no = db.Column(db.Integer, nullable=False)
    logger = db.Column(db.String(128))
    message = db.Column(db.Text)
    trace_id = db.Column(db.String(36), nullable=True)
    user_id = db.Column(db.String(), nullable=True)
    username = db.Column(db.String(128), nullable=True)
    endpoint = db.Column(db.String(128), nullable=True)
    module = db.Column(db.String(128), nullable=True)
    func = db.Column(db.String(128), nullable=True)
    line = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        db.Index("ix_app_log_timestamp", "timestamp"),
        db.Index("ix_app_log_level", "level"),
    )

    def __repr__(self):
        return f"<AppLog id={self.id} level='{self.level}' logger='{self.logger}'>"
