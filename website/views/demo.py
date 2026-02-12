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
        "date": session_start,
        "session_length": "3.5",
        "players": [
            {"name": "Riri", "avatar": "https://picsum.photos/id/237/200/300"},
            {"name": "Fifi", "avatar": "https://picsum.photos/id/96/367/267"},
        ],
        "sessions": [
            {"start": session_start, "end": session_start + timedelta(hours=3)},
            {
                "start": session_start + timedelta(weeks=1),
                "end": session_start + timedelta(weeks=1, hours=3),
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
        "date": session_start + timedelta(days=2, hours=1),
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
        "date": session_start + timedelta(days=3, minutes=30),
    },
]


@demo_bp.route("/demo/")
def demo_general():
    return render_template("games.j2", title="Annonces", games=fake_games)


@demo_bp.route("/demo/inscription/")
def demo_register():
    return render_template("game_details.j2", game=fake_games[0], is_player=False)


@demo_bp.route("/demo/poster/")
def demo_post():
    return render_template("game_form.j2")


@demo_bp.route("/demo/gerer/")
def demo_manage():
    return render_template("game_details.j2", game=fake_games[0], is_player=False)
