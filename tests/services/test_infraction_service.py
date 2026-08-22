"""Tests for ModerationService (in-app infractions)."""

from datetime import datetime, timezone

import pytest

from config.constants import (
    INFRACTION_SEVERITY_REMINDER,
    INFRACTION_SEVERITY_WARNING,
)
from tests.factories import InfractionFactory, UserFactory
from website.exceptions import NotFoundError, ValidationError
from website.models import Infraction
from website.services.moderation import ModerationService


class TestModerationService:
    def test_create(self, db_session):
        """create persists a infraction with trimmed fields and defaults."""
        service = ModerationService()
        user = UserFactory(db_session)
        admin = UserFactory(db_session)

        infraction = service.create(
            user.id,
            {
                "reason": "  Comportement inapproprié  ",
                "severity": INFRACTION_SEVERITY_WARNING,
                "rule_article": " Art. 3 ",
                "message_link": " https://discord.com/channels/1/2/3 ",
                "admin_id": admin.id,
            },
        )

        assert infraction.id is not None
        assert infraction.reason == "Comportement inapproprié"
        assert infraction.rule_article == "Art. 3"
        assert infraction.message_link == "https://discord.com/channels/1/2/3"
        assert infraction.severity == INFRACTION_SEVERITY_WARNING
        assert infraction.admin_id == admin.id
        assert infraction.created_at is not None

    def test_create_defaults_severity_to_reminder(self, db_session):
        """create defaults to the reminder severity."""
        service = ModerationService()
        user = UserFactory(db_session)

        infraction = service.create(user.id, {"reason": "Test"})

        assert infraction.severity == INFRACTION_SEVERITY_REMINDER

    def test_create_backfilled_date(self, db_session):
        """create honours an explicit created_at for backfilling history."""
        service = ModerationService()
        user = UserFactory(db_session)
        past = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)

        infraction = service.create(user.id, {"reason": "Old", "created_at": past})

        assert infraction.created_at == past

    def test_create_empty_reason_raises(self, db_session):
        """create rejects an empty/whitespace reason."""
        service = ModerationService()
        user = UserFactory(db_session)

        with pytest.raises(ValidationError):
            service.create(user.id, {"reason": "   "})

    def test_create_unknown_severity_raises(self, db_session):
        """create rejects a severity outside the catalog."""
        service = ModerationService()
        user = UserFactory(db_session)

        with pytest.raises(ValidationError):
            service.create(user.id, {"reason": "Test", "severity": 99})

    def test_create_unknown_user_raises(self, db_session):
        """create rejects a infraction for a non-existent user."""
        service = ModerationService()

        with pytest.raises(NotFoundError):
            service.create("000000000000000000", {"reason": "Test"})

    def test_list_for_user(self, db_session):
        """list_for_user returns a user's infractions, newest first."""
        service = ModerationService()
        user = UserFactory(db_session)
        older = InfractionFactory(
            db_session,
            user_id=user.id,
            created_at=datetime(2021, 1, 1, tzinfo=timezone.utc),
        )
        newer = InfractionFactory(
            db_session,
            user_id=user.id,
            created_at=datetime(2022, 1, 1, tzinfo=timezone.utc),
        )
        # A infraction for another user must not appear.
        InfractionFactory(db_session)

        infractions = service.list_for_user(user.id)

        assert [w.id for w in infractions] == [newer.id, older.id]

    def test_get_by_id_not_found(self, db_session):
        """get_by_id raises NotFoundError for an unknown id."""
        service = ModerationService()
        with pytest.raises(NotFoundError):
            service.get_by_id(-999)

    def test_update(self, db_session):
        """update mutates provided fields and validates them."""
        service = ModerationService()
        infraction = InfractionFactory(db_session, reason="Initial", severity=1)

        updated = service.update(
            infraction.id,
            {
                "reason": " Corrigé ",
                "severity": INFRACTION_SEVERITY_WARNING,
                "rule_article": "Art. 1",
            },
        )

        assert updated.reason == "Corrigé"
        assert updated.severity == INFRACTION_SEVERITY_WARNING
        assert updated.rule_article == "Art. 1"

    def test_update_empty_reason_raises(self, db_session):
        """update rejects clearing the reason."""
        service = ModerationService()
        infraction = InfractionFactory(db_session)

        with pytest.raises(ValidationError):
            service.update(infraction.id, {"reason": "  "})

    def test_delete(self, db_session):
        """delete removes the infraction."""
        service = ModerationService()
        infraction = InfractionFactory(db_session)
        infraction_id = infraction.id

        service.delete(infraction_id)

        assert db_session.get(Infraction, infraction_id) is None

    def test_delete_not_found_raises(self, db_session):
        """delete raises NotFoundError for an unknown id."""
        service = ModerationService()
        with pytest.raises(NotFoundError):
            service.delete(-999)

    def test_list_paginated_search(self, db_session):
        """list_paginated filters by reason via search."""
        service = ModerationService()
        user = UserFactory(db_session)
        InfractionFactory(db_session, user_id=user.id, reason="Triche flagrante")

        result = service.list_paginated(search="flagrante")

        assert any("flagrante" in w.reason for w in result.items)
