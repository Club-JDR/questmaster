"""Per-user dashboard statistics and agenda aggregation.

Computes the data behind the dashboard's "Mes prochaines sessions" agenda and
"Mes statistiques" panel. All public results are plain, JSON-serialisable dicts
(no ORM instances) so they can be safely memoised in the request/Redis cache,
keyed by user — repeated dashboard loads do not re-hit the database.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from dateutil.relativedelta import relativedelta

from config.constants import (
    DASHBOARD_AGENDA_PAST,
    DASHBOARD_RYTHME_MONTHS,
    DASHBOARD_STATS_CACHE_TIMEOUT,
    DASHBOARD_TOP_SYSTEMS,
    DEFAULT_AVATAR,
    GAME_TYPE_CAMPAIGN,
    GAME_TYPE_ONESHOT,
    RESTRICTION_LABELS,
    STATS_TOP_GLOBAL,
)
from website.extensions import cache, db
from website.models import User
from website.repositories.game import GameRepository
from website.repositories.system import SystemRepository
from website.repositories.trophy import TrophyRepository
from website.repositories.user import UserRepository
from website.repositories.vtt import VttRepository
from website.utils.logger import logger

ROLE_GM = "MJ"
ROLE_PLAYER = "Joueur·euse"


class StatsService:
    """Aggregate a user's agenda and all-time play statistics."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"

    def __init__(self, repository: GameRepository | None = None):
        self.repo = repository or GameRepository()

    def get_dashboard_stats(self, user_id: str, agenda_limit: int) -> dict:
        """Return the agenda and all-time stats for a user.

        The heavy aggregation is memoised per user (independent of
        ``agenda_limit``); only the cheap final slice of the upcoming agenda is
        applied per call.

        Args:
            user_id: Discord user ID.
            agenda_limit: Maximum number of upcoming sessions to list.

        Returns:
            Dict with ``agenda`` (``past`` / ``upcoming`` row lists) and ``stats``
            (headline numbers, ratios, rhythm, top systems and network), all as
            plain serialisable values.
        """
        data = self._compute_data(user_id)
        agenda = data["agenda"]
        return {
            "agenda": {"past": agenda["past"], "upcoming": agenda["upcoming"][:agenda_limit]},
            "stats": data["stats"],
        }

    def get_global_stats(self) -> dict:
        """Return app-wide platform statistics for the public ``/stats`` page.

        Aggregates catalogue sizes, the game-type and role repartition, the top
        systems and VTTs, the 12-month activity rhythm and the age-restriction
        split across **all** games. Mirrors :meth:`get_dashboard_stats` but
        without the per-user filter, returning plain serialisable dicts (no ORM)
        so the result can render directly in the template.

        Returns:
            Dict with ``catalogue``, ``type``, ``role``, ``top_systems``,
            ``top_vtts``, ``rythme`` and ``restriction`` entries.
        """
        now = datetime.now()
        games = self.repo.find_all_with_relations()
        tagged = [(g, None) for g in games]
        return {
            "catalogue": self._catalogue(games),
            "play": self._global_play_hours(games, now),
            "type": self._type_ratios(tagged),
            "role": self._global_role_ratios(games),
            "top_systems": self._global_top(games, lambda g: g.system.name if g.system else None),
            "top_vtts": self._global_top(games, lambda g: g.vtt.name if g.vtt else None),
            "rythme": self._rythme(tagged, now),
            "restriction": self._restriction_split(games),
        }

    def invalidate(self, user_id: str) -> None:
        """Drop the cached dashboard data for a single user.

        Call after a change that affects the user's sessions, games, registrations
        or trophies so their next dashboard load recomputes fresh data.

        Args:
            user_id: Discord user ID whose cached stats should be invalidated.
        """
        # Invalidation runs after a successful write; never let a cache backend
        # hiccup bubble up and fail the user's action (the entry expires via TTL).
        try:
            cache.delete_memoized(self._compute_data, user_id)
        except Exception as exc:  # noqa: BLE001 - best-effort cache invalidation
            logger.warning("Failed to invalidate dashboard stats for %s: %s", user_id, exc)

    def invalidate_for_game(self, game) -> None:
        """Invalidate the cached stats of everyone involved in a game (GM + players).

        Args:
            game: Game whose GM and registered players should be invalidated.
        """
        self.invalidate(game.gm_id)
        for player in game.players:
            self.invalidate(player.id)

    @cache.memoize(timeout=DASHBOARD_STATS_CACHE_TIMEOUT)
    def _compute_data(self, user_id: str) -> dict:
        now = datetime.now()
        gm_games = self.repo.find_by_gm_with_relations(user_id)
        player_games = self.repo.find_by_player_with_relations(user_id)

        return {
            "agenda": self._build_agenda(gm_games, player_games, now),
            "stats": self._build_stats(user_id, gm_games, player_games, now),
        }

    # ------------------------------------------------------------------ agenda

    def _build_agenda(self, gm_games, player_games, now) -> dict:
        """Build the chronological agenda (recent past + all upcoming sessions).

        The upcoming list is returned in full; the caller slices it to the
        configured display limit so the cache stays limit-independent.
        """
        rows = []
        for game, role in self._iter_with_role(gm_games, player_games):
            for session in game.sessions:
                rows.append((session.start, self._session_row(session, game, role)))

        past = sorted((r for r in rows if r[0] < now), key=lambda r: r[0])
        upcoming = sorted((r for r in rows if r[0] >= now), key=lambda r: r[0])

        return {
            "past": [r[1] for r in past[-DASHBOARD_AGENDA_PAST:]],
            "upcoming": [r[1] for r in upcoming],
        }

    @staticmethod
    def _session_row(session, game, role) -> dict:
        """Serialise a single agenda row for the template."""
        vtt = game.vtt.name if game.vtt else None
        meta = f"{game.system.name} · {vtt}" if vtt else game.system.name
        return {
            "dow": session.start.strftime("%a"),
            "day": session.start.strftime("%d"),
            "month": session.start.strftime("%b"),
            "time": session.start.strftime("%Hh%M"),
            "name": game.name,
            "slug": game.slug,
            "meta": meta,
            "role": role,
            "type": game.type,
        }

    # ------------------------------------------------------------------- stats

    def _build_stats(self, user_id, gm_games, player_games, now) -> dict:
        """Compute the all-time statistics panel."""
        gm_sessions = self._all_sessions(gm_games)
        player_sessions = self._all_sessions(player_games)
        all_games = [(g, ROLE_GM) for g in gm_games] + [(g, ROLE_PLAYER) for g in player_games]

        gm_hours = self._played_hours(gm_sessions, now)
        player_hours = self._played_hours(player_sessions, now)

        return {
            "play_hours_total": round(gm_hours + player_hours),
            "play_hours_gm": round(gm_hours),
            "play_hours_player": round(player_hours),
            "badges": self._badge_count(user_id),
            "games_count": len(gm_games) + len(player_games),
            "sessions_count": len(gm_sessions) + len(player_sessions),
            "role": {
                "sessions": self._pct(len(gm_sessions), len(player_sessions)),
                "parties": self._pct(len(gm_games), len(player_games)),
            },
            "type": self._type_ratios(all_games),
            "rythme": self._rythme(all_games, now),
            "top_systems": {
                "player": self._top_systems(player_games),
                "gm": self._top_systems(gm_games),
            },
            "network": self._network(user_id, gm_games, player_games),
        }

    @staticmethod
    def _iter_with_role(gm_games, player_games):
        for g in gm_games:
            yield g, ROLE_GM
        for g in player_games:
            yield g, ROLE_PLAYER

    @staticmethod
    def _all_sessions(games) -> list:
        return [s for g in games for s in g.sessions]

    @staticmethod
    def _played_hours(sessions, now) -> float:
        """Sum the duration (hours) of sessions that have already ended."""
        total = 0.0
        for s in sessions:
            if s.end and s.end <= now:
                total += (s.end - s.start).total_seconds() / 3600
        return total

    @staticmethod
    def _pct(a_count: int, b_count: int) -> int:
        """Return ``a`` as a whole-percent share of ``a + b`` (0 when empty)."""
        total = a_count + b_count
        return round(a_count / total * 100) if total else 0

    def _type_ratios(self, all_games) -> dict:
        os_sessions = sum(len(g.sessions) for g, _ in all_games if g.type == "oneshot")
        camp_sessions = sum(len(g.sessions) for g, _ in all_games if g.type == "campaign")
        os_games = sum(1 for g, _ in all_games if g.type == "oneshot")
        camp_games = sum(1 for g, _ in all_games if g.type == "campaign")
        return {
            "sessions": self._pct(os_sessions, camp_sessions),
            "parties": self._pct(os_games, camp_games),
        }

    def _rythme(self, all_games, now) -> dict:
        """Sessions and distinct games per month over the last N months."""
        months_meta = []
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        for i in range(DASHBOARD_RYTHME_MONTHS - 1, -1, -1):
            d = start - relativedelta(months=i)
            months_meta.append((d.year, d.month))

        index = {ym: i for i, ym in enumerate(months_meta)}
        sessions = [0] * DASHBOARD_RYTHME_MONTHS
        games_per_month = [set() for _ in range(DASHBOARD_RYTHME_MONTHS)]

        for game, _ in all_games:
            for s in game.sessions:
                key = (s.start.year, s.start.month)
                i = index.get(key)
                if i is not None:
                    sessions[i] += 1
                    games_per_month[i].add(game.id)

        return {
            "labels": [f"{m:02d}/{y % 100:02d}" for y, m in months_meta],
            "sessions": sessions,
            "parties": [len(s) for s in games_per_month],
        }

    @staticmethod
    def _top_systems(games) -> dict:
        """Top systems for a set of games, by sessions and by game count."""
        by_sessions: Counter = Counter()
        by_games: Counter = Counter()
        for g in games:
            name = g.system.name
            by_sessions[name] += len(g.sessions)
            by_games[name] += 1
        return {
            "sessions": [
                {"name": n, "n": c} for n, c in by_sessions.most_common(DASHBOARD_TOP_SYSTEMS)
            ],
            "parties": [
                {"name": n, "n": c} for n, c in by_games.most_common(DASHBOARD_TOP_SYSTEMS)
            ],
        }

    # ------------------------------------------------------------ global stats

    @staticmethod
    def _catalogue(games) -> dict:
        """Headline catalogue sizes across the whole platform."""
        return {
            "systems": SystemRepository().count(),
            "vtts": VttRepository().count(),
            "trophies": TrophyRepository().count(),
            "users": UserRepository().count(),
            "games": len(games),
            "sessions": sum(len(g.sessions) for g in games),
        }

    @staticmethod
    def _global_play_hours(games, now) -> dict:
        """Total elapsed game time across the platform (ended sessions only).

        Sums the real duration of every session that has already happened — the
        actual hours of play that took place at the tables. Counted once per
        session (not per participant), so the figure is wall-clock game time.

        Args:
            games: Games to aggregate (sessions eager-loaded).
            now: Current time; only sessions that have already ended count.

        Returns:
            Dict with the rounded total ``hours`` and the number of ended
            ``sessions`` that contributed to it.
        """
        hours = 0.0
        sessions = 0
        for g in games:
            for s in g.sessions:
                if s.end and s.end <= now:
                    hours += (s.end - s.start).total_seconds() / 3600
                    sessions += 1
        return {"hours": round(hours), "sessions": sessions}

    def _global_role_ratios(self, games) -> dict:
        """GM vs player engagement share across the platform.

        Each game has one GM and several player registrations; the share counts
        engagements (not distinct people): GM slots vs player slots, by sessions
        and by games.
        """
        gm_games = len(games)
        player_games = sum(len(g.players) for g in games)
        gm_sessions = sum(len(g.sessions) for g in games)
        player_sessions = sum(len(g.sessions) * len(g.players) for g in games)
        return {
            "sessions": self._pct(gm_sessions, player_sessions),
            "parties": self._pct(gm_games, player_games),
        }

    def _global_top(self, games, key) -> dict:
        """Top ``STATS_TOP_GLOBAL`` entries by game count, split by game type.

        The ranking is independent of the sessions/annonces toggle (it always
        ranks by number of games); the breakdown lets the UI switch between all
        games, one-shots only and campaigns only.

        Args:
            games: Games to rank.
            key: Callable mapping a game to its grouping name (``None`` skips it).

        Returns:
            Dict with ``all``, ``oneshot`` and ``campaign`` ranked-list values,
            each a list of ``{"name", "n"}`` dicts.
        """
        return {
            "all": self._top_ranked(games, key),
            "oneshot": self._top_ranked([g for g in games if g.type == GAME_TYPE_ONESHOT], key),
            "campaign": self._top_ranked([g for g in games if g.type == GAME_TYPE_CAMPAIGN], key),
        }

    @staticmethod
    def _top_ranked(games, key) -> list[dict]:
        """Return the top ``STATS_TOP_GLOBAL`` groups by game count.

        Args:
            games: Games to rank.
            key: Callable mapping a game to its grouping name (``None`` skips it).

        Returns:
            Ranked list of ``{"name", "n"}`` dicts (most games first).
        """
        by_games: Counter = Counter()
        for g in games:
            name = key(g)
            if name:
                by_games[name] += 1
        return [{"name": n, "n": c} for n, c in by_games.most_common(STATS_TOP_GLOBAL)]

    @staticmethod
    def _restriction_split(games) -> dict:
        """Age-restriction repartition (Tout public / 16+ / 18+) over all games."""
        counter = Counter(g.restriction for g in games)
        total = len(games)
        rows = [
            {
                "value": value,
                "label": label,
                "n": counter.get(value, 0),
                "pct": round(counter.get(value, 0) / total * 100) if total else 0,
            }
            for value, label in RESTRICTION_LABELS.items()
        ]
        return {"rows": rows, "total": total}

    def _network(self, user_id, gm_games, player_games) -> dict:
        """Distinct GMs played with and distinct table-mates met."""
        gm_counter: Counter = Counter()
        gm_meta = {}
        for g in player_games:
            if g.gm:
                gm_counter[g.gm.id] += 1
                gm_meta[g.gm.id] = g.gm

        mate_counter: Counter = Counter()
        mate_meta = {}
        for g, _ in self._iter_with_role(gm_games, player_games):
            for p in g.players:
                if p.id != user_id:
                    mate_counter[p.id] += 1
                    mate_meta[p.id] = p

        return {
            "gm_count": len(gm_counter),
            "player_count": len(mate_counter),
            "gms": self._people(gm_counter, gm_meta),
            "players": self._people(mate_counter, mate_meta),
        }

    @staticmethod
    def _people(counter, meta) -> list[dict]:
        return [
            {
                "name": meta[uid].name,
                "avatar": getattr(meta[uid], "avatar", DEFAULT_AVATAR),
                "n": n,
            }
            for uid, n in counter.most_common()
        ]

    @staticmethod
    def _badge_count(user_id) -> int:
        user = db.session.get(User, user_id)
        if not user:
            return 0
        return sum(ut.quantity for ut in user.trophies)
