"""Tests for AppLogService (filtered listing and retention pruning)."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from tests.factories import AppLogFactory
from website.models import AppLog
from website.services import AppLogService


def _messages(pagination):
    return [log.message for log in pagination.items]


def test_list_paginated_newest_first(db_session):
    token = uuid4().hex[:10]
    now = datetime.now(timezone.utc)
    AppLogFactory(db_session, message=f"older {token}", timestamp=now - timedelta(minutes=5))
    AppLogFactory(db_session, message=f"newer {token}", timestamp=now)

    result = AppLogService().list_paginated(search=token)

    assert _messages(result) == [f"newer {token}", f"older {token}"]


def test_list_paginated_filters_by_minimum_level(db_session):
    token = uuid4().hex[:10]
    AppLogFactory(db_session, message=f"debug {token}", level="DEBUG", level_no=logging.DEBUG)
    AppLogFactory(db_session, message=f"info {token}", level="INFO", level_no=logging.INFO)
    AppLogFactory(db_session, message=f"error {token}", level="ERROR", level_no=logging.ERROR)

    result = AppLogService().list_paginated(level_no=logging.WARNING, search=token)

    assert _messages(result) == [f"error {token}"]


def test_list_paginated_filters_by_date_range(db_session):
    token = uuid4().hex[:10]
    now = datetime.now(timezone.utc)
    AppLogFactory(db_session, message=f"too old {token}", timestamp=now - timedelta(days=10))
    AppLogFactory(db_session, message=f"in range {token}", timestamp=now - timedelta(days=5))
    AppLogFactory(db_session, message=f"too new {token}", timestamp=now)

    result = AppLogService().list_paginated(
        start=now - timedelta(days=7), end=now - timedelta(days=3), search=token
    )

    assert _messages(result) == [f"in range {token}"]


def test_list_paginated_filters_by_logger(db_session):
    token = uuid4().hex[:10]
    AppLogFactory(db_session, message=f"from services {token}", logger="website.services.game")
    AppLogFactory(db_session, message=f"from views {token}", logger="website.views.games")

    result = AppLogService().list_paginated(logger="services", search=token)

    assert _messages(result) == [f"from services {token}"]


def test_list_paginated_search_matches_logger_and_trace_id(db_session):
    token = uuid4().hex[:10]
    AppLogFactory(db_session, message="by logger", logger=f"website.{token}")
    AppLogFactory(db_session, message="by trace", trace_id=token)
    AppLogFactory(db_session, message="unrelated row", logger="website.other")

    result = AppLogService().list_paginated(search=token)

    assert sorted(_messages(result)) == ["by logger", "by trace"]


def test_prune_deletes_only_rows_older_than_retention(db_session):
    token = uuid4().hex[:10]
    now = datetime.now(timezone.utc)
    old_id = AppLogFactory(
        db_session, message=f"old {token}", timestamp=now - timedelta(days=40)
    ).id
    recent_id = AppLogFactory(
        db_session, message=f"recent {token}", timestamp=now - timedelta(days=5)
    ).id

    deleted = AppLogService().prune(retention_days=30)

    assert deleted >= 1
    assert db_session.get(AppLog, old_id) is None
    assert db_session.get(AppLog, recent_id) is not None
