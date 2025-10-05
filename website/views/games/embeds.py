from flask import current_app
from website.models import Game
from website.bot import get_bot

DEFAULT_TIMEFORMAT = "%Y-%m-%d %H:%M"
HUMAN_TIMEFORMAT = "%a %d/%m - %Hh%M"


def _build_restriction_message(game):
    """Return the formatted restriction message with tags."""
    restriction_icons = {
        "all": ":green_circle: Tout public",
        "16+": ":yellow_circle: 16+",
        "18+": ":red_circle: 18+",
    }

    base = restriction_icons.get(game.restriction, ":red_circle: 18+")
    if game.restriction_tags:
        base += f" {game.restriction_tags}"
    return base


def _build_embed_title(game):
    """Return the title with emoji and completion status."""
    title = game.name
    if game.status == "closed":
        title += " (complet)"

    if game.special_event:
        emoji = game.special_event.emoji or ""
        if emoji:
            title = f"{emoji} {title} {emoji}"

    return title


def _get_session_type(game):
    """Return session type display name."""
    if game.special_event:
        return f"Événement spécial : {game.special_event.name}"
    return "Campagne" if game.type == "campaign" else "OS"


def _build_embed_fields(game, session_type, restriction_msg):
    """Return list of embed fields, applying strikethrough if closed."""
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

    if game.status == "closed":
        for field in fields:
            field["value"] = f"~~{field['value']}~~"

    return fields


def _get_embed_color(game):
    """Return integer color code for Discord embed."""
    if game.special_event and game.special_event.color:
        color = game.special_event.color
        if isinstance(color, str):
            color = color.lstrip("#")
            try:
                return int(color, 16)
            except ValueError:
                return 0x5865F2  # fallback
        return color

    return Game.COLORS.get(game.type, 0x5865F2)


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
    """Build a Discord embed for a game announcement."""

    restriction_msg = _build_restriction_message(game)
    title = _build_embed_title(game)
    session_type = _get_session_type(game)
    fields = _build_embed_fields(game, session_type, restriction_msg)
    color = _get_embed_color(game)

    embed = {
        "title": title,
        "color": color,
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


def build_edit_session_embed(game, start, end, _, old_start, old_end, *__):
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
            f"**Signalement de <@{player}> :**\n{alert_message}\n"
            f"**Salon :**\n<#{game.channel}>\n"
            f"**Annonce :**\nhttps://questmaster.club-jdr.fr/annonces/{game.slug}\n"
        ),
    }
    return embed, current_app.config["ADMIN_CHANNEL_ID"]
