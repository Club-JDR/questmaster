"""Flask CLI commands for Discord slash-command management."""

import click
from flask import current_app
from flask.cli import with_appcontext

from config.constants import INFRACTION_SEVERITY_LABELS

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
