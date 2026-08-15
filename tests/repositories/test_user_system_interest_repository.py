from tests.factories import SystemFactory, UserFactory
from website.models import UserSystemInterest
from website.repositories.user_system_interest import UserSystemInterestRepository


class TestUserSystemInterestRepository:
    def test_get_returns_none_when_absent(self, db_session):
        repo = UserSystemInterestRepository()
        system = SystemFactory(db_session)
        user = UserFactory(db_session)
        assert repo.get(user.id, system.id, "player") is None

    def test_get_returns_existing_interest(self, db_session):
        repo = UserSystemInterestRepository()
        system = SystemFactory(db_session)
        user = UserFactory(db_session)
        interest = UserSystemInterest(user_id=user.id, system_id=system.id, role="player")
        repo.add(interest)

        found = repo.get(user.id, system.id, "player")

        assert found is not None
        assert found.user_id == user.id
        assert found.role == "player"

    def test_get_distinguishes_role(self, db_session):
        repo = UserSystemInterestRepository()
        system = SystemFactory(db_session)
        user = UserFactory(db_session)
        repo.add(UserSystemInterest(user_id=user.id, system_id=system.id, role="player"))

        assert repo.get(user.id, system.id, "gm") is None

    def test_list_by_system_and_role(self, db_session):
        repo = UserSystemInterestRepository()
        system = SystemFactory(db_session)
        player = UserFactory(db_session, name="ZZZ Player")
        gm = UserFactory(db_session, name="AAA GM")
        repo.add(UserSystemInterest(user_id=player.id, system_id=system.id, role="player"))
        repo.add(UserSystemInterest(user_id=gm.id, system_id=system.id, role="gm"))

        players = repo.list_by_system_and_role(system.id, "player")
        gms = repo.list_by_system_and_role(system.id, "gm")

        assert [i.user_id for i in players] == [player.id]
        assert [i.user_id for i in gms] == [gm.id]

    def test_list_by_system_and_role_orders_by_name(self, db_session):
        repo = UserSystemInterestRepository()
        system = SystemFactory(db_session)
        zzz = UserFactory(db_session, name="ZZZ Late Alphabet")
        aaa = UserFactory(db_session, name="AAA Early Alphabet")
        repo.add(UserSystemInterest(user_id=zzz.id, system_id=system.id, role="player"))
        repo.add(UserSystemInterest(user_id=aaa.id, system_id=system.id, role="player"))

        interests = repo.list_by_system_and_role(system.id, "player")

        assert [i.user_id for i in interests] == [aaa.id, zzz.id]

    def test_inherits_delete(self, db_session):
        repo = UserSystemInterestRepository()
        system = SystemFactory(db_session)
        user = UserFactory(db_session)
        interest = repo.add(UserSystemInterest(user_id=user.id, system_id=system.id, role="gm"))

        repo.delete(interest)

        assert repo.get(user.id, system.id, "gm") is None
