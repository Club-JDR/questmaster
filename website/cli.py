"""Flask CLI commands for Discord slash-command management and cache maintenance."""

from collections.abc import Callable

import click
from flask import current_app
from flask.cli import with_appcontext

from config.constants import INFRACTION_SEVERITY_LABELS
from website.exceptions import ValidationError
from website.extensions import cache

# Discord application-command definitions (type 1 = CHAT_INPUT, option type 3 = STRING,
# type 4 = INTEGER, type 6 = USER).
# Guild-scoped registration is deliberate: it propagates instantly and
# QuestMaster serves a single guild.
SLASH_COMMANDS = [
    {
        "name": "info",
        "description": "Affiche les infos de la partie de ce salon",
        "type": 1,
    },
    {
        "name": "signaler",
        "description": "Signaler un problème aux MJ/admins",
        "type": 1,
        "options": [
            {"name": "message", "description": "Votre message", "type": 3, "required": True}
        ],
    },
    {
        "name": "notifier",
        "description": "Notifier les joueur·euses (MJ)",
        "type": 1,
        "options": [
            {"name": "message", "description": "Message à envoyer", "type": 3, "required": True}
        ],
    },
    {
        "name": "ajouter-session",
        "description": "Ajouter une session (MJ)",
        "type": 1,
        "options": [
            {
                "name": "debut",
                "description": "Début (JJ/MM/AAAA HH:MM)",
                "type": 3,
                "required": True,
            },
            {
                "name": "duree",
                "description": "Durée (ex. 3h ou 2h30) — défaut : durée de session de la partie",
                "type": 3,
                "required": False,
            },
            {
                "name": "fin",
                "description": "Fin (JJ/MM/AAAA HH:MM) — prioritaire sur la durée",
                "type": 3,
                "required": False,
            },
        ],
    },
    {
        "name": "editer-session",
        "description": "Modifier une session existante (MJ)",
        "type": 1,
        "options": [
            {
                "name": "debut",
                "description": "Début actuel de la session (JJ/MM/AAAA HH:MM)",
                "type": 3,
                "required": True,
            },
            {
                "name": "nouveau_debut",
                "description": "Nouveau début (JJ/MM/AAAA HH:MM)",
                "type": 3,
                "required": True,
            },
            {
                "name": "duree",
                "description": "Durée (ex. 3h ou 2h30) — défaut : durée actuelle de la session",
                "type": 3,
                "required": False,
            },
            {
                "name": "nouvelle_fin",
                "description": "Nouvelle fin (JJ/MM/AAAA HH:MM) — prioritaire sur la durée",
                "type": 3,
                "required": False,
            },
        ],
    },
    {
        "name": "supprimer-session",
        "description": "Supprimer une session (MJ)",
        "type": 1,
        "options": [
            {
                "name": "debut",
                "description": "Début de la session à supprimer (JJ/MM/AAAA HH:MM)",
                "type": 3,
                "required": True,
            },
        ],
    },
    {
        "name": "inscrire",
        "description": "Inscrire un·e joueur·euse à la partie de ce salon (MJ)",
        "type": 1,
        "options": [
            {
                "name": "membre",
                "description": "Membre à inscrire",
                "type": 6,
                "required": True,
            },
        ],
    },
    {
        "name": "desinscrire",
        "description": "Désinscrire un·e joueur·euse de la partie de ce salon (MJ)",
        "type": 1,
        "options": [
            {
                "name": "membre",
                "description": "Membre à désinscrire",
                "type": 6,
                "required": True,
            },
        ],
    },
    {
        "name": "ouvrir",
        "description": "Ouvrir les inscriptions de la partie (MJ)",
        "type": 1,
    },
    {
        "name": "fermer",
        "description": "Fermer les inscriptions de la partie (MJ)",
        "type": 1,
    },
    {
        "name": "publier",
        "description": "Publier l'annonce de la partie de ce salon (MJ)",
        "type": 1,
    },
    {
        "name": "badges",
        "description": "Afficher les badges d'un membre",
        "type": 1,
        "options": [
            {
                "name": "membre",
                "description": "Membre à consulter (vous par défaut)",
                "type": 6,
                "required": False,
            },
        ],
    },
    {
        "name": "mon-agenda",
        "description": "Affiche vos prochaines sessions (MJ, joueur·euse, spectateur·ice)",
        "type": 1,
    },
    {
        "name": "avertir",
        "description": "Enregistrer une infraction pour un membre (admin)",
        "type": 1,
        "options": [
            {
                "name": "membre",
                "description": "Membre concerné",
                "type": 6,
                "required": True,
            },
            {
                "name": "raison",
                "description": "Raison / détail de l'infraction",
                "type": 3,
                "required": True,
            },
            {
                "name": "gravite",
                "description": "Gravité — défaut : rappel à l'ordre",
                "type": 4,
                "required": False,
                "choices": [
                    {"name": label, "value": value}
                    for value, label in INFRACTION_SEVERITY_LABELS.items()
                ],
            },
            {
                "name": "article",
                "description": "Article du règlement non respecté",
                "type": 3,
                "required": False,
            },
            {
                "name": "lien",
                "description": "Lien vers le post de modération",
                "type": 3,
                "required": False,
            },
        ],
    },
    {
        "name": "infractions",
        "description": "Lister les infractions d'un membre (admin)",
        "type": 1,
        "options": [
            {
                "name": "membre",
                "description": "Membre à consulter",
                "type": 6,
                "required": True,
            },
        ],
    },
]


@click.command("sync-discord-commands")
@with_appcontext
def sync_discord_commands():
    """Register/update the guild's slash commands with Discord."""
    from website.services import DiscordService

    DiscordService().register_guild_commands(current_app.config["DISCORD_APP_ID"], SLASH_COMMANDS)
    click.echo(f"Registered {len(SLASH_COMMANDS)} commands.")


# Named cache targets, each backed by the owning service's own invalidation
# method (see each service's `clear_cache`/`invalidate_all`) — kept here as a
# single shared dispatch table so both `flask clear-cache` and the admin
# settings page's cache panel stay thin callers instead of duplicating it.
CACHE_TARGETS = ("systems", "vtts", "calendar", "badges", "stats", "discord")


def _cache_target_handlers() -> dict[str, Callable[[], None]]:
    """Build the TARGET -> invalidation-callable mapping.

    Deferred imports keep this out of the module's import-time footprint
    (mirrors ``sync_discord_commands`` above) and sidestep the circular
    import that a top-level ``website.views.misc`` import would create.

    Returns:
        Dict mapping each name in ``CACHE_TARGETS`` to a zero-argument
        callable that clears that surface.
    """
    from website.services.discord import DiscordService
    from website.services.game_session import GameSessionService
    from website.services.stats import StatsService
    from website.services.system import SystemService
    from website.services.vtt import VttService
    from website.views.misc import clear_leaderboard_cache

    return {
        "systems": SystemService.clear_cache,
        "vtts": VttService.clear_cache,
        "calendar": GameSessionService.clear_cache,
        "badges": clear_leaderboard_cache,
        "stats": StatsService.invalidate_all,
        "discord": DiscordService.clear_cache,
    }


def clear_cache_target(target: str) -> None:
    """Clear one named cached surface, or the whole cache backend for ``"all"``.

    Shared by the ``clear-cache`` CLI command and the admin settings page's
    cache-maintenance panel.

    Args:
        target: ``"all"``, or one of ``CACHE_TARGETS``.

    Raises:
        ValidationError: If target is neither ``"all"`` nor a known target.
    """
    if target == "all":
        cache.clear()
        return
    handlers = _cache_target_handlers()
    if target not in handlers:
        raise ValidationError("Unknown cache target.", field="target", details={"value": target})
    handlers[target]()


@click.command("clear-cache")
@click.argument("target", default="all", type=click.Choice(("all", *CACHE_TARGETS)))
@with_appcontext
def clear_cache(target: str):
    """Clear cached Flask-Caching data.

    Defaults to ``all`` (flushes the whole configured cache backend — safe to
    run in production, since ``CACHE_KEY_PREFIX`` scopes it to QuestMaster's
    own keys). Pass a specific TARGET to clear a single cached surface instead
    (e.g. after a manual DB fix that bypassed a service's own invalidation).
    """
    clear_cache_target(target)
    click.echo(f"Cache cleared: {target}.")
