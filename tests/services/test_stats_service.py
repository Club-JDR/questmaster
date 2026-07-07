"""Tests for StatsService (per-user dashboard agenda + statistics)."""

from datetime import datetime

from config.constants import BADGE_CAMPAIGN_ID, BADGE_OS_ID, RESTRICTION_LABELS
from tests.factories import (
    GameFactory,
    GameSessionFactory,
    SystemFactory,
    UserFactory,
    UserTrophyFactory,
    VttFactory,
)
from website.services.stats import ROLE_GM, ROLE_PLAYER, StatsService

PAST = (datetime(2026, 1, 10, 20, 0), datetime(2026, 1, 10, 23, 0))
FUTURE = (datetime(2030, 1, 10, 20, 0), datetime(2030, 1, 10, 23, 0))


def _build_scenario(db_session, default_system):
    """User U is GM of a campaign and a player in a one-shot run by another GM."""
    user = UserFactory(db_session)
    other_gm = UserFactory(db_session)
    mate = UserFactory(db_session)

    gm_game = GameFactory(
        db_session, type="campaign", status="open", gm_id=user.id, system_id=default_system.id
    )
    gm_game.players.append(mate)
    GameSessionFactory(db_session, game_id=gm_game.id, start=PAST[0], end=PAST[1])
    GameSessionFactory(db_session, game_id=gm_game.id, start=FUTURE[0], end=FUTURE[1])

    player_game = GameFactory(
        db_session, type="oneshot", status="open", gm_id=other_gm.id, system_id=default_system.id
    )
    player_game.players.append(user)
    player_game.players.append(mate)
    GameSessionFactory(db_session, game_id=player_game.id, start=PAST[0], end=PAST[1])
    GameSessionFactory(db_session, game_id=player_game.id, start=FUTURE[0], end=FUTURE[1])
    GameSessionFactory(db_session, game_id=player_game.id, start=FUTURE[0], end=FUTURE[1])
    db_session.flush()

    return user, other_gm, mate


class TestStatsService:
    def test_counts(self, db_session, default_system):
        user, *_ = _build_scenario(db_session, default_system)
        stats = StatsService().get_dashboard_stats(user.id, 10)["stats"]

        assert stats["games_count"] == 2
        assert stats["sessions_count"] == 5  # 2 (GM) + 3 (player)

    def test_gm_also_player_of_own_game_is_not_double_counted(self, db_session, default_system):
        """A game the user GMs must count once (as GM), even if also registered as a player."""
        user, *_ = _build_scenario(db_session, default_system)
        # gm_game has 2 sessions; registering the GM as a player in their own
        # game must not inflate any headline stat.
        gm_game = GameFactory(
            db_session, type="oneshot", status="open", gm_id=user.id, system_id=default_system.id
        )
        gm_game.players.append(user)
        GameSessionFactory(db_session, game_id=gm_game.id, start=PAST[0], end=PAST[1])
        db_session.flush()

        stats = StatsService().get_dashboard_stats(user.id, 10)["stats"]
        # 2 GM games + 1 player game + the new GM game (counted once) == 3.
        assert stats["games_count"] == 3
        # 2 (campaign GM) + 3 (player OS) + 1 (new GM game) == 6, no double count.
        assert stats["sessions_count"] == 6
        # The user must not appear as one of the GMs they "played with".
        assert stats["network"]["gm_count"] == 1

    def test_draft_games_are_excluded(self, db_session, default_system):
        """Unpublished (draft) games must not contribute to a user's stats."""
        user, *_ = _build_scenario(db_session, default_system)
        draft = GameFactory(
            db_session, type="oneshot", status="draft", gm_id=user.id, system_id=default_system.id
        )
        GameSessionFactory(db_session, game_id=draft.id, start=PAST[0], end=PAST[1])
        db_session.flush()

        stats = StatsService().get_dashboard_stats(user.id, 10)["stats"]
        assert stats["games_count"] == 2  # unchanged: the draft is ignored
        assert stats["sessions_count"] == 5  # the draft's session is ignored

    def test_role_and_type_ratios(self, db_session, default_system):
        user, *_ = _build_scenario(db_session, default_system)
        stats = StatsService().get_dashboard_stats(user.id, 10)["stats"]

        # Role: GM sessions 2 vs player sessions 3 -> 40% MJ; games 1 vs 1 -> 50%.
        assert stats["role"]["sessions"] == 40
        assert stats["role"]["parties"] == 50
        # Type: OS sessions 3 vs campaign 2 -> 60% OS; games 1 vs 1 -> 50%.
        assert stats["type"]["sessions"] == 60
        assert stats["type"]["parties"] == 50

    def test_agenda_split_roles_and_order(self, db_session, default_system):
        user, *_ = _build_scenario(db_session, default_system)
        agenda = StatsService().get_dashboard_stats(user.id, 10)["agenda"]

        assert len(agenda["past"]) == 2  # one per game, capped by DASHBOARD_AGENDA_PAST(3)
        assert len(agenda["upcoming"]) == 3  # 1 (GM) + 2 (player)
        roles = {row["role"] for row in agenda["upcoming"]}
        assert roles == {ROLE_GM, ROLE_PLAYER}

    def test_agenda_limit_caps_upcoming(self, db_session, default_system):
        user, *_ = _build_scenario(db_session, default_system)
        agenda = StatsService().get_dashboard_stats(user.id, 1)["agenda"]
        assert len(agenda["upcoming"]) == 1

    def test_network(self, db_session, default_system):
        user, other_gm, mate = _build_scenario(db_session, default_system)
        network = StatsService().get_dashboard_stats(user.id, 10)["stats"]["network"]

        assert network["gm_count"] == 1  # only the other GM (of the game U plays in)
        assert network["player_count"] == 1  # only the table-mate (U excluded)
        assert network["players"][0]["name"] == mate.name

    def test_rythme_shape(self, db_session, default_system):
        user, *_ = _build_scenario(db_session, default_system)
        rythme = StatsService().get_dashboard_stats(user.id, 10)["stats"]["rythme"]

        assert len(rythme["labels"]) == 12
        assert len(rythme["sessions"]) == 12
        assert len(rythme["parties"]) == 12

    def test_badge_count(self, db_session, default_system):
        user, *_ = _build_scenario(db_session, default_system)
        # Use a seeded trophy id to avoid trophy-sequence collisions in the shared DB.
        UserTrophyFactory(db_session, user_id=user.id, trophy_id=BADGE_OS_ID, quantity=3)
        db_session.flush()

        stats = StatsService().get_dashboard_stats(user.id, 10)["stats"]
        assert stats["badges"] == 3

    def test_empty_user(self, db_session):
        user = UserFactory(db_session)
        data = StatsService().get_dashboard_stats(user.id, 10)

        assert data["agenda"]["upcoming"] == []
        assert data["stats"]["games_count"] == 0
        assert data["stats"]["role"]["sessions"] == 0


def _game_with(
    db_session,
    system,
    *,
    type="oneshot",
    restriction="all",
    vtt=None,
    players=0,
    sessions=0,
    status="open",
):
    """Build a published game with N players and N sessions, returning the flushed game.

    Defaults to a non-draft status so the game is counted by the statistics
    aggregation (drafts are excluded).
    """
    gm = UserFactory(db_session)
    game = GameFactory(
        db_session,
        type=type,
        restriction=restriction,
        status=status,
        gm_id=gm.id,
        system_id=system.id,
        vtt_id=vtt.id if vtt else None,
    )
    for _ in range(players):
        game.players.append(UserFactory(db_session))
    for _ in range(sessions):
        GameSessionFactory(db_session, game_id=game.id, start=PAST[0], end=PAST[1])
    db_session.flush()
    db_session.refresh(game)
    return game


class TestGlobalStats:
    """Pure aggregation helpers run on a controlled game list (DB-independent)."""

    def test_role_ratios_count_engagements(self, db_session, default_system):
        # 1 GM slot + 2 player slots -> GM share 33%; sessions 2 GM vs 2*2 player -> 33%.
        game = _game_with(db_session, default_system, players=2, sessions=2)
        role = StatsService()._global_role_ratios([game])
        assert role["parties"] == 33
        assert role["sessions"] == 33

    def test_global_top_ranks_by_games_split_by_type(self, db_session, default_system):
        popular = SystemFactory(db_session)
        niche = SystemFactory(db_session)
        games = [
            _game_with(db_session, popular, type="oneshot"),
            _game_with(db_session, popular, type="oneshot"),
            _game_with(db_session, popular, type="campaign"),
            _game_with(db_session, niche, type="oneshot"),
        ]
        top = StatsService()._global_top(games, lambda g: g.system.name)

        assert top["all"][0] == {"name": popular.name, "n": 3}
        assert {r["name"]: r["n"] for r in top["all"]} == {popular.name: 3, niche.name: 1}
        assert {r["name"]: r["n"] for r in top["oneshot"]} == {popular.name: 2, niche.name: 1}
        assert top["campaign"] == [{"name": popular.name, "n": 1}]

    def test_global_top_skips_missing_key(self, db_session, default_system):
        vtt = VttFactory(db_session)
        games = [
            _game_with(db_session, default_system, vtt=vtt),
            _game_with(db_session, default_system, vtt=None),  # no VTT
        ]
        top = StatsService()._global_top(games, lambda g: g.vtt.name if g.vtt else None)
        assert top["all"] == [{"name": vtt.name, "n": 1}]

    def test_play_hours_sum_ended_sessions(self, db_session, default_system):
        game = _game_with(db_session, default_system, sessions=2)  # two ended 3h sessions
        play = StatsService()._global_play_hours([game], datetime(2027, 1, 1))
        assert play == {"hours": 6, "sessions": 2}

    def test_restriction_split(self, db_session, default_system):
        games = [
            _game_with(db_session, default_system, restriction="all"),
            _game_with(db_session, default_system, restriction="all"),
            _game_with(db_session, default_system, restriction="18+"),
        ]
        split = StatsService()._restriction_split(games)
        rows = {r["label"]: r for r in split["rows"]}

        assert split["total"] == 3
        assert len(split["rows"]) == len(RESTRICTION_LABELS)
        assert rows["Tout public"]["n"] == 2
        assert rows["Tout public"]["pct"] == 67
        assert rows["18 ans et +"]["n"] == 1

    def test_catalogue_trophies_counts_awarded_not_types(self, db_session, default_system):
        """The catalogue trophy tile counts trophies granted to players, not definitions."""
        user = UserFactory(db_session)
        # 3 of one badge + 2 of another == 5 awarded, across 2 trophy *types*.
        UserTrophyFactory(db_session, user_id=user.id, trophy_id=BADGE_OS_ID, quantity=3)
        UserTrophyFactory(db_session, user_id=user.id, trophy_id=BADGE_CAMPAIGN_ID, quantity=2)
        db_session.flush()

        catalogue = StatsService().get_global_stats()["catalogue"]
        assert catalogue["trophies"] >= 5  # awarded quantities, not the ~2 types

    def test_global_stats_exclude_draft_games(self, db_session, default_system):
        """Draft games must not appear in the app-wide statistics aggregation."""
        from website.repositories.game import GameRepository

        published = _game_with(db_session, default_system, sessions=1, status="open")
        draft = _game_with(db_session, default_system, sessions=1, status="draft")
        db_session.flush()

        ids = {g.id for g in GameRepository().find_all_with_relations()}
        assert published.id in ids
        assert draft.id not in ids

    def test_get_global_stats_shape(self, db_session, default_system):
        _game_with(db_session, default_system, players=2, sessions=2)
        data = StatsService().get_global_stats()

        assert set(data) == {
            "catalogue",
            "play",
            "type",
            "role",
            "top_systems",
            "top_vtts",
            "rythme",
            "restriction",
        }
        assert len(data["rythme"]["labels"]) == 12
        assert len(data["restriction"]["rows"]) == len(RESTRICTION_LABELS)
        assert set(data["top_systems"]) == {"all", "oneshot", "campaign"}
        assert len(data["top_systems"]["all"]) <= 10
        assert set(data["play"]) == {"hours", "sessions"}
        # Catalogue values are integers reflecting at least the rows we created.
        assert data["catalogue"]["games"] >= 1
        assert data["catalogue"]["systems"] >= 1
        assert all(isinstance(v, int) for v in data["catalogue"].values())
