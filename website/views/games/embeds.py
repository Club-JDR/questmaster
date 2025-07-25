from flask import current_app
from website.models import Game
from website.bot import get_bot

DEFAULT_TIMEFORMAT = "%Y-%m-%d %H:%M"
HUMAN_TIMEFORMAT = "%a %d/%m - %Hh%M"


def send_discord_embed(
    game,
    type="annonce",
    start=None,
    end=None,
    player=None,
    old_start=None,
    old_end=None,
    alert_message=None,
):
    bot = get_bot()

    embed_builders = {
        "annonce": build_annonce_embed,
        "annonce_details": build_annonce_details_embed,
        "add-session": build_add_session_embed,
        "edit-session": build_edit_session_embed,
        "del-session": build_delete_session_embed,
        "register": build_register_embed,
        "alert": build_alert_embed,
    }

    if type not in embed_builders:
        raise ValueError(f"Unknown embed type: {type}")

    embed, target = embed_builders[type](
        game, start, end, player, old_start, old_end, alert_message
    )

    if type == "annonce" and game.msg_id:
        response = bot.edit_embed_message(game.msg_id, embed, target)
    else:
        response = bot.send_embed_message(embed, target)
    return response["id"]


def build_annonce_embed(game, *_):
    session_type = "Campagne" if game.type == "campaign" else "OS"

    restriction_icons = {
        "all": ":green_circle: Tout public",
        "16+": ":yellow_circle: 16+",
        "18+": ":red_circle: 18+",
    }
    restriction = restriction_icons.get(game.restriction, ":red_circle: 18+")

    restriction_msg = restriction
    if game.restriction_tags:
        restriction_msg += f" {game.restriction_tags}"

    # Add "(complet)" in the title if the game is closed
    title = game.name
    if game.status == "closed":
        title += " (complet)"

    # Build normal fields
    fields = [
        {"name": "MJ", "value": game.gm.name, "inline": True},
        {"name": "Système", "value": game.system.name, "inline": True},
        {"name": "Type de session", "value": session_type, "inline": True},
        {"name": "Date", "value": game.date.strftime(HUMAN_TIMEFORMAT), "inline": True},
        {"name": "Durée", "value": game.length, "inline": True},
        {"name": "Avertissement", "value": restriction_msg},
        {
            "name": "Pour s'inscrire :",
            "value": f"https://questmaster.club-jdr.fr/annonces/{game.slug}/",
        },
    ]

    # Apply strikethrough if closed
    if game.status == "closed":
        for field in fields:
            field["value"] = f"~~{field['value']}~~"

    embed = {
        "title": title,
        "color": Game.COLORS[game.type],
        "fields": fields,
        "image": {"url": game.img},
        "footer": {},
    }

    return embed, current_app.config["POSTS_CHANNEL_ID"]


def build_annonce_details_embed(game, *_):
    embed = {
        "title": "Tout est prêt.",
        "color": 0x2196F3,  # blue
        "description": (
            f"<@{game.gm_id}> voici ton salon de partie.\nLe rôle associé est <@&{game.role}>\n"
            f"Et voici le lien vers [la page de ton annonce](https://questmaster.club-jdr.fr/annonces/{game.slug}).\n"
        ),
    }
    return embed, game.channel


def build_add_session_embed(game, start, end, *_):
    embed = {
        "title": "Nouvelle session prévue",
        "color": 0x4CB944,  # green
        "description": (
            f"<@&{game.role}>\nVotre MJ a ajouté une nouvelle session : du **{start}** au **{end}**\n\n"
            f"Pour ne pas l'oublier, pensez à l'ajouter à votre calendrier depuis "
            f"[l'annonce sur QuestMaster](https://questmaster.club-jdr.fr/annonces/{game.slug}).\n"
            f"Si vous avez un empêchement, prévenez votre MJ en avance."
        ),
    }
    return embed, game.channel


def build_edit_session_embed(game, start, end, _, old_start, old_end):
    embed = {
        "title": "Session modifiée",
        "color": 0xFFCF48,  # yellow
        "description": (
            f"<@&{game.role}>\nVotre MJ a modifié la session ~~du {old_start} au {old_end}~~\n"
            f"La session a été décalée du **{start}** au **{end}**\n"
            f"Pensez à mettre à jour votre calendrier."
        ),
    }
    return embed, game.channel


def build_delete_session_embed(game, start, end, *_):
    embed = {
        "title": "Session annulée",
        "color": 0xF34242,  # red
        "description": (
            f"<@&{game.role}>\nVotre MJ a annulé la session du **{start}** au **{end}**\n"
            f"Pensez à l'enlever de votre calendrier."
        ),
    }
    return embed, game.channel


def build_register_embed(game, _, __, player, *___):
    embed = {
        "title": "Nouvelle inscription",
        "color": 0x2196F3,  # blue
        "description": f"<@{player}> s'est inscrit. Bienvenue :wave:",
    }
    return embed, game.channel


def build_alert_embed(game, _, __, player, ___, ____, alert_message):
    embed = {
        "title": "Signalement",
        "color": 0xF34242,  # red
        "description": (
            f"<@{player}> a fait un signalement concernant l'annonce "
            f"https://questmaster.club-jdr.fr/annonces/{game.slug}\n"
            f"**Signalement :**\n{alert_message}"
        ),
    }
    return embed, current_app.config["ADMIN_CHANNEL_ID"]
