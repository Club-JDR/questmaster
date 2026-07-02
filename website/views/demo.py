"""Demo views with fake game data for preview purposes."""

from datetime import datetime, timedelta

from flask import Blueprint, render_template

demo_bp = Blueprint("demo", __name__)

today = datetime.now()
next_monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
session_start = next_monday.replace(hour=20, minute=0, second=0, microsecond=0)

fake_games = [
    {
        "name": "La Tombe de l'Annihilation",
        "gm": {"name": "Le Gob'"},
        "system": {"name": "D&D 5E (2014)"},
        "vtt": {"name": "FoundryVTT"},
        "type": "campaign",
        "length": "20+ sessions",
        "description": """Bienvenue dans la jungle!

              Une malédiction mortelle s'abat sur les morts déjà ramenés à la vie : ils se mettent à pourrir et tous les efforts déployés pour enrayer la décomposition restent vains.
              Les âmes des trépassés sont maintenant volées à leur mort, les unes après les autres, et piégées dans un artefact nécromantique.
              Ce n'est qu'en détruisant cette chose qu'elles seront libérées et que l'on pourra de nouveau ramener les défunts à la vie.
              Tous les indices mènent au Chult, un pays mystérieux fait de volcans, de jungles et des ruines de royaumes déchus, sous lequel un tombeau mortel attend ses victimes.
              
              Le piège est tendu, mordrez-vous à l'appât?""",
        "restriction": "all",
        "party_size": 4,
        "xp": "all",
        "frequency": "weekly",
        "characters": "with_gm",
        "complement": "Formulaire à remplir pour la sélection : https://questmaster.club-jdr.fr/ce-formulaire-n-existe-pas/",
        "party_selection": "on",
        "status": "open",
        "ambience": ["chill", "epic"],
        "classification": {
            "action": 2,
            "investigation": 1,
            "interaction": 2,
            "horror": 1,
        },
        "img": "https://r2.foundryvtt.com/website-uploads-public/screen/user_70/toa-banner-2025-05-13.webp",
        "date": session_start.isoformat(),
        "session_length": "3.5",
        "players": [
            {"name": "Riri", "avatar": "https://picsum.photos/id/237/200/300"},
            {"name": "Fifi", "avatar": "https://picsum.photos/id/96/367/267"},
        ],
        "sessions": [
            {
                "start": session_start.isoformat(),
                "end": (session_start + timedelta(hours=3)).isoformat(),
            },
            {
                "start": (session_start + timedelta(weeks=1)).isoformat(),
                "end": (session_start + timedelta(weeks=1, hours=3)).isoformat(),
            },
        ],
    },
    {
        "name": "Le Pensionnaire",
        "gm": {"name": "Perceval"},
        "system": {"name": "L'Appel de Cthulhu v7"},
        "vtt": {"name": "Roll20"},
        "type": "oneshot",
        "length": "1 session",
        "description": """Qu’est-il arrivé à votre calme et sympathique voisin ? Cela fait plusieurs jours que vous ne l’avez pas vu !
            Même s’il ne se montre pas toujours des plus amical, sa dévotion ne fait aucun doute, à en juger par toutes les prières qu’il psalmodie dans sa chambre le soir venu…""",
        "restriction": "18+",
        "restriction_tags": "gore, suicide, folie",
        "party_size": "4",
        "img": "https://files.d20.io/marketplace/1630181/oGojkYY7dVVWvgeTZc75GA/med.png?1613370570436",
        "date": (session_start + timedelta(days=2, hours=1)).isoformat(),
    },
    {
        "name": "La Nécropole",
        "gm": {"name": "Le Gentil MJ"},
        "system": {"name": "L'Appel de Cthulhu v7"},
        "vtt": {"name": "FoundryVTT"},
        "type": "oneshot",
        "length": "1 session",
        "description": """Quelles horreurs antiques renferme la tombe récemment découverte au cœur de la Vallée des Rois, en Égypte ?
        Debout au sommet des marches qui s’enfoncent dans les ténèbres, le moment est mal choisi pour vous laisser troubler par les superstitions locales et les malheureux incidents survenus à l’ouverture du tombeau de Toutankhamon…""",
        "restriction": "16+",
        "restriction_tags": "claustrophobie,gore",
        "party_size": "4",
        "img": "https://shop.novalisgames.com/product/image/large/escth13fr_illu1_20220112.jpg",
        "date": (session_start + timedelta(days=3, minutes=30)).isoformat(),
    },
]


def _demo_session(day, time, name, meta, role, gtype):
    """Build one fake agenda row for the demo dashboard."""
    return {
        "dow": "sam.",
        "day": day,
        "month": "juil.",
        "time": time,
        "name": name,
        "slug": "demo",
        "meta": meta,
        "role": role,
        "type": gtype,
    }


_DEMO_AGENDA = {
    "past": [
        _demo_session(
            "05", "20h00", "La Tombe de l'Annihilation", "D&D 5E · FoundryVTT", "MJ", "campaign"
        ),
        _demo_session(
            "06", "21h00", "Le Pensionnaire", "Cthulhu v7 · Roll20", "Joueur·euse", "oneshot"
        ),
    ],
    "upcoming": [
        _demo_session(
            "12", "20h00", "La Tombe de l'Annihilation", "D&D 5E · FoundryVTT", "MJ", "campaign"
        ),
        _demo_session(
            "13", "21h00", "Le Pensionnaire", "Cthulhu v7 · Roll20", "Joueur·euse", "oneshot"
        ),
        _demo_session(
            "16", "19h30", "La Nécropole", "Cthulhu v7 · FoundryVTT", "Joueur·euse", "oneshot"
        ),
    ],
}

_DEMO_STATS = {
    "play_hours_total": 142,
    "play_hours_gm": 44,
    "play_hours_player": 98,
    "badges": 12,
    "games_count": 27,
    "sessions_count": 41,
    "role": {"sessions": 35, "parties": 22},
    "type": {"sessions": 30, "parties": 55},
    "rythme": {
        "labels": [
            "07/24",
            "08/24",
            "09/24",
            "10/24",
            "11/24",
            "12/24",
            "01/25",
            "02/25",
            "03/25",
            "04/25",
            "05/25",
            "06/25",
        ],
        "sessions": [3, 5, 6, 4, 7, 10, 5, 3, 6, 9, 5, 8],
        "parties": [1, 1, 2, 2, 3, 3, 2, 1, 2, 4, 2, 3],
    },
    "top_systems": {
        "player": {
            "sessions": [
                {"name": "D&D 5E", "n": 18},
                {"name": "Cthulhu v7", "n": 11},
                {"name": "Pathfinder 2", "n": 4},
            ],
            "parties": [
                {"name": "D&D 5E", "n": 9},
                {"name": "Cthulhu v7", "n": 6},
                {"name": "Pathfinder 2", "n": 3},
            ],
        },
        "gm": {
            "sessions": [
                {"name": "Cthulhu v7", "n": 12},
                {"name": "D&D 5E", "n": 7},
                {"name": "Lasers & Feelings", "n": 2},
            ],
            "parties": [
                {"name": "Cthulhu v7", "n": 5},
                {"name": "D&D 5E", "n": 4},
                {"name": "Lasers & Feelings", "n": 1},
            ],
        },
    },
    "network": {
        "gm_count": 3,
        "player_count": 4,
        "gms": [
            {"name": "Le Gob'", "avatar": "https://picsum.photos/id/237/64", "n": 6},
            {"name": "Perceval", "avatar": "https://picsum.photos/id/40/64", "n": 4},
            {"name": "Le Gentil MJ", "avatar": "https://picsum.photos/id/64/64", "n": 3},
        ],
        "players": [
            {"name": "Riri", "avatar": "https://picsum.photos/id/1/64", "n": 5},
            {"name": "Fifi", "avatar": "https://picsum.photos/id/2/64", "n": 5},
            {"name": "Loulou", "avatar": "https://picsum.photos/id/3/64", "n": 4},
            {"name": "Picsou", "avatar": "https://picsum.photos/id/4/64", "n": 2},
        ],
    },
}


@demo_bp.route("/demo/tableau-de-bord/", methods=["GET"])
def demo_dashboard():
    """Render the demo dashboard page (the personalised landing) with fake data."""
    return render_template(
        "dashboard.j2",
        agenda=_DEMO_AGENDA,
        stats=_DEMO_STATS,
        open_games=fake_games,
        open_hidden=5,
    )


@demo_bp.route("/demo/", methods=["GET"])
def demo_general():
    """Render the demo game list page."""
    return render_template("games.j2", title="Annonces", games=fake_games)


@demo_bp.route("/demo/inscription/", methods=["GET"])
def demo_register():
    """Render the demo registration page."""
    return render_template("game_details.j2", game=fake_games[0], is_player=False)


@demo_bp.route("/demo/poster/", methods=["GET"])
def demo_post():
    """Render the demo game creation form."""
    return render_template("game_form.j2")


@demo_bp.route("/demo/gerer/", methods=["GET"])
def demo_manage():
    """Render the demo game management page."""
    return render_template("game_details.j2", game=fake_games[0], is_player=False)
