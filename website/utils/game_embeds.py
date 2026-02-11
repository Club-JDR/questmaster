"""Discord embed builders for game announcements and notifications.

This module provides functions to build Discord embed dictionaries for various
game events. The embed builders return (embed_dict, target_channel_id) tuples.

Usage:
    from website.services import DiscordService

    discord = DiscordService()
    discord.send_game_embed(game, embed_type="annonce")
"""

from flask import current_app

from config.constants import (
    EMBED_COLOR_BLUE,
    EMBED_COLOR_DEFAULT,
    EMBED_COLOR_GREEN,
    EMBED_COLOR_RED,
    EMBED_COLOR_YELLOW,
    HUMAN_TIMEFORMAT,
    SITE_BASE_URL,
)
from website.models import Game


# -----------------------------------------------------------------------------
# Internal helper functions
# -----------------------------------------------------------------------------


def _build_restriction_message(game) -> str:
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


def _build_embed_title(game) -> str:
    """Return the title with emoji and completion status."""
    title = game.name
    if game.status == "closed":
        title += " (complet)"

    if game.special_event:
        emoji = game.special_event.emoji or ""
        if emoji:
            title = f"{emoji} {title} {emoji}"

    return title


def _get_session_type(game) -> str:
    """Return session type display name."""
    if game.special_event:
        return f"Événement spécial : {game.special_event.name}"
    return "Campagne" if game.type == "campaign" else "OS"


def _build_embed_fields(game, session_type: str, restriction_msg: str) -> list:
    """Return list of embed fields, applying strikethrough if closed."""
    game_url = f"{SITE_BASE_URL}/annonces/{game.slug}/"

    fields = [
        {"name": "MJ", "value": game.gm.name, "inline": True},
        {"name": "Système", "value": game.system.name, "inline": True},
        {"name": "Type de session", "value": session_type, "inline": True},
        {"name": "Date", "value": game.date.strftime(HUMAN_TIMEFORMAT), "inline": True},
        {"name": "Durée", "value": game.length, "inline": True},
        {"name": "Avertissement", "value": restriction_msg},
        {"name": "Pour s'inscrire :", "value": game_url},
    ]

    if game.status == "closed":
        for field in fields:
            field["value"] = f"~~{field['value']}~~"

    return fields


def _get_embed_color(game) -> int:
    """Return integer color code for Discord embed."""
    if game.special_event and game.special_event.color:
        color = game.special_event.color
        if isinstance(color, str):
            color = color.lstrip("#")
            try:
                return int(color, 16)
            except ValueError:
                return EMBED_COLOR_DEFAULT
        return color

    return Game.COLORS.get(game.type, EMBED_COLOR_DEFAULT)


# -----------------------------------------------------------------------------
# Embed builder functions
#
# All builders share a uniform signature so they can be called generically
# by DiscordService.send_game_embed via a dispatch dict.
# -----------------------------------------------------------------------------


def build_annonce_embed(
    game,
    start=None,
    end=None,
    player=None,
    old_start=None,
    old_end=None,
    alert_message=None,
) -> tuple[dict, str]:
    """Build a Discord embed for a game announcement.

    Args:
        game: Game instance.

    Returns:
        Tuple of (embed dict, target channel ID).
    """
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


def build_annonce_details_embed(
    game,
    start=None,
    end=None,
    player=None,
    old_start=None,
    old_end=None,
    alert_message=None,
) -> tuple[dict, str]:
    """Build the initial channel message with GM reminders.

    Args:
        game: Game instance.

    Returns:
        Tuple of (embed dict, game channel ID).
    """
    game_url = f"{SITE_BASE_URL}/annonces/{game.slug}"

    embed = {
        "title": "Tout est prêt.",
        "color": EMBED_COLOR_BLUE,
        "description": (
            f"<@{game.gm_id}> voici le salon pour ta partie {game.name} et voici le lien [vers l'annonce]({game_url}).\n"
            f"Le rôle associé est <@&{game.role}>.\n\n"
            f"Quelques petits rappels :\n"
            f"- La partie doit être **organisée et jouée sur le serveur du Club JDR** (Cf. règlement).\n"
            f"- Notifie tes joueur·euses **uniquement avec le rôle @PJ** mentionné plus haut, et non pas `@everyone`, `@here` ou `@Joueur·euses`.\n"
            f"- Toutes les sessions **jouées** doivent être ajoutées dans QuestMaster au fur et à mesure.\n"
            f"- Le bouton **Signaler** sur QuestMaster te permet de contacter les admins en cas de problème concernant la partie."
        ),
    }
    return embed, game.channel


def build_add_session_embed(
    game,
    start=None,
    end=None,
    player=None,
    old_start=None,
    old_end=None,
    alert_message=None,
) -> tuple[dict, str]:
    """Build embed notifying players of a new session.

    Args:
        game: Game instance.
        start: Session start datetime or formatted string.
        end: Session end datetime or formatted string.

    Returns:
        Tuple of (embed dict, game channel ID).
    """
    game_url = f"{SITE_BASE_URL}/annonces/{game.slug}"

    embed = {
        "title": "Nouvelle session prévue",
        "color": EMBED_COLOR_GREEN,
        "description": (
            f"<@&{game.role}>\nVotre MJ a ajouté une nouvelle session : du **{start}** au **{end}**\n\n"
            f"Pour ne pas l'oublier, pensez à l'ajouter à votre calendrier depuis "
            f"[l'annonce sur QuestMaster]({game_url}).\n"
            f"Si vous avez un empêchement, prévenez votre MJ en avance."
        ),
    }
    return embed, game.channel


def build_edit_session_embed(
    game,
    start=None,
    end=None,
    player=None,
    old_start=None,
    old_end=None,
    alert_message=None,
) -> tuple[dict, str]:
    """Build embed notifying players of a rescheduled session.

    Args:
        game: Game instance.
        start: New session start datetime or formatted string.
        old_start: Previous session start for comparison.

    Returns:
        Tuple of (embed dict, game channel ID).
    """
    embed = {
        "title": "Session modifiée",
        "color": EMBED_COLOR_YELLOW,
        "description": (
            f"<@&{game.role}>\nVotre MJ a modifié la session ~~du {old_start}~~\n"
            f"La session a été décalée au **{start}**\n"
            f"Pensez à mettre à jour votre calendrier."
        ),
    }
    return embed, game.channel


def build_delete_session_embed(
    game,
    start=None,
    end=None,
    player=None,
    old_start=None,
    old_end=None,
    alert_message=None,
) -> tuple[dict, str]:
    """Build embed notifying players of a cancelled session.

    Args:
        game: Game instance.
        start: Cancelled session start datetime or formatted string.
        end: Cancelled session end datetime or formatted string.

    Returns:
        Tuple of (embed dict, game channel ID).
    """
    embed = {
        "title": "Session annulée",
        "color": EMBED_COLOR_RED,
        "description": (
            f"<@&{game.role}>\nVotre MJ a annulé la session du **{start}** au **{end}**\n"
            f"Pensez à l'enlever de votre calendrier."
        ),
    }
    return embed, game.channel


def build_register_embed(
    game,
    start=None,
    end=None,
    player=None,
    old_start=None,
    old_end=None,
    alert_message=None,
) -> tuple[dict, str]:
    """Build embed notifying the channel of a new player registration.

    Args:
        game: Game instance.
        player: Discord user ID of the registered player.

    Returns:
        Tuple of (embed dict, game channel ID).
    """
    embed = {
        "title": "Nouvelle inscription",
        "color": EMBED_COLOR_BLUE,
        "description": f"<@{player}> s'est inscrit. Bienvenue :wave:",
    }
    return embed, game.channel


def build_alert_embed(
    game,
    start=None,
    end=None,
    player=None,
    old_start=None,
    old_end=None,
    alert_message=None,
) -> tuple[dict, str]:
    """Build embed reporting an alert from a game participant.

    Args:
        game: Game instance.
        player: Discord user ID of the reporting player.
        alert_message: The alert message content.

    Returns:
        Tuple of (embed dict, admin channel ID).
    """
    game_url = f"{SITE_BASE_URL}/annonces/{game.slug}"

    embed = {
        "title": "Signalement",
        "color": EMBED_COLOR_RED,
        "description": (
            f"**Signalement de <@{player}> :**\n{alert_message}\n"
            f"**Salon :**\n<#{game.channel}>\n"
            f"**Annonce :**\n{game_url}\n"
        ),
    }
    return embed, current_app.config["ADMIN_CHANNEL_ID"]
