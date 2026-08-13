"""Discord slash-command dispatch service.

Executes QuestMaster actions requested through Discord HTTP interactions
(slash commands), reusing the existing services so no business logic is
duplicated. The caller's identity comes from the Ed25519-signed interaction
payload; the game is resolved from the channel the command was run in.
"""

import re
import threading
from datetime import datetime, timedelta

from config.constants import (
    DISCORD_MESSAGE_MAX_LENGTH,
    EMBED_COLOR_RED,
    GAME_STATUS_LABELS,
    HUMAN_TIMEFORMAT,
    INFRACTION_SEVERITY_REMINDER,
    SITE_BASE_URL,
)
from website.exceptions import (
    DiscordAPIError,
    DuplicateRegistrationError,
    NotFoundError,
    PastDateError,
    QuestMasterError,
    SessionConflictError,
    ValidationError,
)
from website.models import Game, Infraction, User
from website.services.discord import DiscordService
from website.services.game import GameService
from website.services.game_session import GameSessionService
from website.services.moderation import ModerationService
from website.services.user import UserService
from website.utils.logger import log_game_event, logger

# User-facing strings (French — service exceptions never leak to Discord)
MSG_NOT_A_GAME_CHANNEL = "Ce salon n'est pas associé à une partie."
MSG_NOT_PARTICIPANT = "Vous n'êtes pas autorisé·e à effectuer cette action pour cette partie."
MSG_NOT_GM = "Seul·e le·a MJ de l'annonce peut faire cette opération."
MSG_NOT_ADMIN = "Seul·es les admins peuvent faire cette opération."
MSG_UNKNOWN_COMMAND = "Commande inconnue."
MSG_GENERIC_ERROR = "Une erreur est survenue."
MSG_ALERT_SENT = "Signalement effectué."
MSG_PLAYERS_NOTIFIED = "Joueur·euses notifié·es."
MSG_SESSION_ADDED = "Session ajoutée."
MSG_SESSION_EDITED = "Session modifiée."
MSG_SESSION_DELETED = "Session supprimée."
MSG_SESSION_NOT_FOUND = "Aucune session ne commence à cette date."
MSG_EMPTY_NOTIFICATION = "Le message de notification est vide."
MSG_BAD_DATE_FORMAT = "Format de date invalide. Utilisez JJ/MM/AAAA HH:MM."
MSG_BAD_DURATION_FORMAT = "Format de durée invalide. Utilisez par exemple 3h ou 2h30."
MSG_INVALID_SESSION_DATES = (
    "Dates de session invalides : la fin doit suivre le début "
    "et la session ne peut excéder 24 heures."
)
MSG_SESSION_CONFLICT = "Cette session chevauche une session existante."
MSG_PLAYER_REGISTERED = "Joueur·euse inscrit·e."
MSG_PLAYER_UNREGISTERED = "Joueur·euse désinscrit·e."
MSG_PLAYER_ALREADY_REGISTERED = "Cette personne est déjà inscrite à cette partie."
MSG_PLAYER_NOT_REGISTERED = "Cette personne n'est pas inscrite à cette partie."
MSG_NOT_A_PLAYER = "Cette personne n'est pas un·e joueur·euse sur le Discord."
MSG_GM_CANNOT_REGISTER = "Le·a MJ ne peut pas être inscrit·e à sa propre partie."
MSG_GAME_FULL = "La partie est complète."
MSG_GAME_OPENED_OK = "Annonce ouverte aux inscriptions."
MSG_GAME_CLOSED_OK = "Annonce fermée aux inscriptions."
MSG_NOT_CLOSED = "Cette annonce n'est pas fermée aux inscriptions."
MSG_NOT_OPEN = "Cette annonce n'est pas ouverte aux inscriptions."
MSG_ALREADY_PUBLISHED = "Cette annonce est déjà publiée."
MSG_GAME_PUBLISHED = "Annonce publiée."
MSG_PAST_DATE = (
    "La date de la partie est dans le passé. Modifiez la date ou publiez "
    "depuis le site pour confirmer."
)
MSG_NO_BADGES = "Aucun badge pour ce membre."
MSG_NO_INFRACTIONS = "Aucune infraction pour ce membre."
MSG_EMPTY_REASON = "La raison de l'infraction est vide."

# Input format documented in the slash-command option descriptions
SLASH_DATE_FORMAT = "%d/%m/%Y %H:%M"

# Duration option forms: "3h", "2h30", "2", "2.5" (comma accepted as decimal separator)
_DURATION_HM_RE = re.compile(r"(\d{1,2})h(\d{1,2})?")
_DURATION_HOURS_RE = re.compile(r"\d{1,2}([.]\d+)?")


class _CommandInputError(ValueError):
    """Invalid user input in a command option, carrying the French reply."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class DiscordCommandService:
    """Dispatch Discord slash commands to QuestMaster actions.

    Resolves the invoking user and the game (from the interaction channel),
    enforces the same GM/admin/participant rules as the web views, and calls
    the existing services. All replies are French strings destined for
    ephemeral Discord messages.
    """

    INLINE_COMMANDS = {"info", "badges"}

    # Commands that also work outside a game channel (game becomes None)
    CHANNEL_OPTIONAL_COMMANDS = {"signaler", "avertir", "infractions"}

    def __init__(
        self,
        game_service=None,
        session_service=None,
        discord_service=None,
        user_service=None,
        moderation_service=None,
    ):
        self.games = game_service or GameService()
        self.sessions = session_service or GameSessionService()
        self.discord = discord_service or DiscordService()
        self.users = user_service or UserService()
        self.moderation = moderation_service or ModerationService()

    # -------------------------------------------------------------------------
    # Entry points (called by the interactions blueprint)
    # -------------------------------------------------------------------------

    def is_inline(self, payload: dict) -> bool:
        """Tell whether a command is answered inline in the HTTP response.

        Args:
            payload: The interaction payload from Discord.

        Returns:
            True for fast read-only commands (no deferred ack needed).
        """
        return payload.get("data", {}).get("name") in self.INLINE_COMMANDS

    def handle_inline(self, payload: dict) -> str:
        """Execute an inline (read-only) command and return its message text.

        Args:
            payload: The interaction payload from Discord.

        Returns:
            French message text for the ephemeral reply.
        """
        name = payload.get("data", {}).get("name")
        if name == "badges":
            return self._handle_badges(payload)
        if name != "info":
            return MSG_UNKNOWN_COMMAND
        game = self._resolve_game(payload)
        if game is None:
            return MSG_NOT_A_GAME_CHANNEL
        return self._game_summary(game)

    def dispatch_async(self, app, payload: dict) -> None:
        """Run a mutating command in a background thread, then follow up.

        Args:
            app: The real Flask app object (not a proxy) whose context the
                background thread pushes for DB and config access.
            payload: The interaction payload from Discord.
        """
        threading.Thread(target=self._run_in_context, args=(app, payload), daemon=True).start()

    def _run_in_context(self, app, payload: dict) -> None:
        """Execute a command inside an app context and send the follow-up."""
        with app.app_context():
            try:
                content = self._execute(payload)
            except QuestMasterError:
                logger.exception("Discord command failed")
                content = MSG_GENERIC_ERROR
            except Exception:
                logger.exception("Discord command failed unexpectedly")
                content = MSG_GENERIC_ERROR
            try:
                self.discord.send_interaction_followup(
                    app.config["DISCORD_APP_ID"], payload["token"], content
                )
            except DiscordAPIError:
                logger.exception("Failed to send Discord interaction follow-up")

    # -------------------------------------------------------------------------
    # Dispatch
    # -------------------------------------------------------------------------

    def _execute(self, payload: dict) -> str:
        """Resolve user + game and run the matching command handler.

        Args:
            payload: The interaction payload from Discord.

        Returns:
            French message text for the ephemeral follow-up.
        """
        handlers = {
            "signaler": self._handle_alert,
            "notifier": self._handle_notify,
            "ajouter-session": self._handle_add_session,
            "editer-session": self._handle_edit_session,
            "supprimer-session": self._handle_delete_session,
            "inscrire": self._handle_register,
            "desinscrire": self._handle_unregister,
            "ouvrir": self._handle_open,
            "fermer": self._handle_close,
            "publier": self._handle_publish,
            "avertir": self._handle_warn,
            "infractions": self._handle_infractions,
        }
        name = payload.get("data", {}).get("name")
        handler = handlers.get(name)
        if handler is None:
            return MSG_UNKNOWN_COMMAND

        game = self._resolve_game(payload)
        if game is None and name not in self.CHANNEL_OPTIONAL_COMMANDS:
            return MSG_NOT_A_GAME_CHANNEL
        user = self._resolve_user(payload)
        return handler(game, user, payload)

    # -------------------------------------------------------------------------
    # Command handlers (mirror the web views, reuse the same services)
    # -------------------------------------------------------------------------

    def _handle_alert(self, game: Game | None, user: User, payload: dict) -> str:
        """``/signaler`` — send an alert to the admins.

        Inside a game channel the alert references the game (participants
        only), as the web alert button does. Anywhere else a general alert
        carrying only the caller and the message is posted.
        """
        message = self._option(payload, "message")
        if game is None:
            self._send_general_alert(user, message)
            return MSG_ALERT_SENT
        if not self._is_participant(game, user):
            return MSG_NOT_PARTICIPANT
        self.discord.send_game_embed(
            game, embed_type="alert", alert_message=message, player=user.id
        )
        log_game_event("alert", game.id, "Un signalement a été fait.")
        return MSG_ALERT_SENT

    def _send_general_alert(self, user: User, message: str) -> None:
        """Post a game-less alert embed to the admin channel.

        Args:
            user: The member sending the alert.
            message: Free-text alert message.
        """
        from website.services.setting import SettingsService

        embed = {
            "title": "Signalement",
            "color": EMBED_COLOR_RED,
            "description": f"**Signalement de <@{user.id}> :**\n{message}",
        }
        self.discord.send_embed(embed, SettingsService().get("ADMIN_CHANNEL_ID"))
        logger.info(f"General alert sent by user {user.id}")

    def _handle_notify(self, game: Game, user: User, payload: dict) -> str:
        """``/notifier`` — ping the game's players via GameService."""
        if not self._is_gm_or_admin(game, user):
            return MSG_NOT_GM
        message = self._option(payload, "message")
        try:
            self.games.notify_players(game.slug, message, user_id=user.id)
        except ValidationError:
            return MSG_EMPTY_NOTIFICATION
        return MSG_PLAYERS_NOTIFIED

    def _handle_add_session(self, game: Game, user: User, payload: dict) -> str:
        """``/ajouter-session`` — create a session and post the embed.

        The end is given as ``fin`` (datetime) or ``duree`` (duration); when
        both are omitted it defaults to the game's configured session length.
        """
        if not self._is_gm_or_admin(game, user):
            return MSG_NOT_GM
        try:
            start = self._parse_datetime(self._option(payload, "debut", ""))
            end = self._resolve_end(payload, start, timedelta(hours=float(game.session_length)))
        except _CommandInputError as exc:
            return exc.message

        start_fmt = start.strftime(HUMAN_TIMEFORMAT)
        end_fmt = end.strftime(HUMAN_TIMEFORMAT)
        try:
            self.sessions.create(game, start, end)
        except ValidationError:
            return MSG_INVALID_SESSION_DATES
        except SessionConflictError:
            return MSG_SESSION_CONFLICT

        log_game_event(
            "create-session",
            game.id,
            f"Une session a été créée du {start_fmt} au {end_fmt}.",
            user_id=user.id,
        )
        logger.info(f"Session {start}/{end} created for Game {game.id} via slash command")
        self.discord.send_game_embed(game, embed_type="add-session", start=start_fmt, end=end_fmt)
        return MSG_SESSION_ADDED

    def _handle_edit_session(self, game: Game, user: User, payload: dict) -> str:
        """``/editer-session`` — reschedule the session starting at ``debut``.

        The new end is given as ``nouvelle_fin`` (datetime) or ``duree``
        (duration); when both are omitted the session keeps its current
        duration.
        """
        if not self._is_gm_or_admin(game, user):
            return MSG_NOT_GM
        try:
            current_start = self._parse_datetime(self._option(payload, "debut", ""))
        except _CommandInputError as exc:
            return exc.message

        session = self._find_session(game, current_start)
        if session is None:
            return MSG_SESSION_NOT_FOUND

        try:
            new_start = self._parse_datetime(self._option(payload, "nouveau_debut", ""))
            new_end = self._resolve_end(
                payload, new_start, session.end - session.start, end_option="nouvelle_fin"
            )
        except _CommandInputError as exc:
            return exc.message

        old_start = session.start.strftime(HUMAN_TIMEFORMAT)
        old_end = session.end.strftime(HUMAN_TIMEFORMAT)
        try:
            self.sessions.update(session, new_start, new_end)
        except ValidationError:
            return MSG_INVALID_SESSION_DATES
        except SessionConflictError:
            return MSG_SESSION_CONFLICT

        log_game_event(
            "edit-session",
            game.id,
            f"Une session a été éditée : {old_start} → {old_end}, "
            f"remplacée par {new_start} → {new_end}.",
            user_id=user.id,
        )
        logger.info(f"Session {old_start}/{old_end} of Game {game.id} updated via slash command")
        self.discord.send_game_embed(
            game,
            embed_type="edit-session",
            start=session.start.strftime(HUMAN_TIMEFORMAT),
            end=session.end.strftime(HUMAN_TIMEFORMAT),
            old_start=old_start,
            old_end=old_end,
        )
        return MSG_SESSION_EDITED

    def _handle_delete_session(self, game: Game, user: User, payload: dict) -> str:
        """``/supprimer-session`` — remove the session starting at ``debut``."""
        if not self._is_gm_or_admin(game, user):
            return MSG_NOT_GM
        try:
            start = self._parse_datetime(self._option(payload, "debut", ""))
        except _CommandInputError as exc:
            return exc.message

        session = self._find_session(game, start)
        if session is None:
            return MSG_SESSION_NOT_FOUND

        start_fmt = session.start.strftime(HUMAN_TIMEFORMAT)
        end_fmt = session.end.strftime(HUMAN_TIMEFORMAT)
        self.sessions.delete(session)
        log_game_event(
            "delete-session",
            game.id,
            f"Une session a été supprimée du {start_fmt} au {end_fmt}.",
            user_id=user.id,
        )
        logger.info(f"Session {start_fmt}/{end_fmt} of Game {game.id} removed via slash command")
        self.discord.send_game_embed(game, embed_type="del-session", start=start_fmt, end=end_fmt)
        return MSG_SESSION_DELETED

    def _handle_register(self, game: Game, user: User, payload: dict) -> str:
        """``/inscrire <membre>`` — GM/admin registers a member to the game.

        Mirrors the web "add player" management flow: the target must hold the
        Discord player role, and the GM/admin registration is forced (bypasses
        capacity/status checks), exactly as on the website.
        """
        if not self._is_gm_or_admin(game, user):
            return MSG_NOT_GM
        target = self._resolve_target_member(payload)
        if target.id == game.gm_id:
            return MSG_GM_CANNOT_REGISTER
        if not target.is_player:
            return MSG_NOT_A_PLAYER
        try:
            self.games.register_player(game.slug, target.id, force=True)
        except DuplicateRegistrationError:
            return MSG_PLAYER_ALREADY_REGISTERED
        return MSG_PLAYER_REGISTERED

    def _handle_unregister(self, game: Game, user: User, payload: dict) -> str:
        """``/desinscrire <membre>`` — GM/admin removes a member from the game."""
        if not self._is_gm_or_admin(game, user):
            return MSG_NOT_GM
        target_id = str(self._option(payload, "membre") or "")
        if not self.games.is_player(game, target_id):
            return MSG_PLAYER_NOT_REGISTERED
        self.games.unregister_player(game.slug, target_id)
        return MSG_PLAYER_UNREGISTERED

    def _handle_open(self, game: Game, user: User, payload: dict) -> str:
        """``/ouvrir`` — reopen a closed game to registrations."""
        if not self._is_gm_or_admin(game, user):
            return MSG_NOT_GM
        if game.status != "closed":
            return MSG_NOT_CLOSED
        self.games.reopen(game.slug, user_id=user.id)
        return MSG_GAME_OPENED_OK

    def _handle_close(self, game: Game, user: User, payload: dict) -> str:
        """``/fermer`` — close an open game to registrations."""
        if not self._is_gm_or_admin(game, user):
            return MSG_NOT_GM
        if game.status != "open":
            return MSG_NOT_OPEN
        self.games.close(game.slug, user_id=user.id)
        return MSG_GAME_CLOSED_OK

    def _handle_publish(self, game: Game, user: User, payload: dict) -> str:
        """``/publier`` — publish this channel's unpublished announcement.

        Covers games whose channel exists but whose announcement was never
        posted (e.g. a silent publish). A pure draft has no channel yet, so
        it can only be published from the website.
        """
        if not self._is_gm_or_admin(game, user):
            return MSG_NOT_GM
        try:
            self.games.publish(game.slug, user_id=user.id)
        except PastDateError:
            return MSG_PAST_DATE
        except ValidationError as exc:
            return MSG_GAME_FULL if exc.field == "party_size" else MSG_ALREADY_PUBLISHED
        return MSG_GAME_PUBLISHED

    def _handle_badges(self, payload: dict) -> str:
        """``/badges [membre]`` — list a member's trophies (caller by default)."""
        member = payload.get("member") or {}
        caller = member.get("user") or payload.get("user") or {}
        target_id = str(self._option(payload, "membre") or caller.get("id", ""))
        try:
            user = self.users.get_by_id(target_id)
        except NotFoundError:
            return MSG_NO_BADGES
        summary = user.trophy_summary
        if not summary:
            return MSG_NO_BADGES
        lines = [f"**Badges de {user.name}**"]
        lines += [f"- {t['name']} ×{t['quantity']}" for t in summary]
        return "\n".join(lines)

    def _handle_warn(self, game: Game | None, user: User, payload: dict) -> str:
        """``/avertir <membre> <raison> [gravite] [article] [lien]`` — record an infraction.

        Admin-only, usable in any channel. Records the infraction through
        ``ModerationService`` exactly as the admin "Modération" page does;
        nothing is posted publicly and the target is not notified.
        """
        if not user.is_admin:
            return MSG_NOT_ADMIN
        target = self._resolve_target_member(payload)
        try:
            infraction = self.moderation.create(
                user_id=target.id,
                reason=self._option(payload, "raison", ""),
                severity=int(self._option(payload, "gravite", INFRACTION_SEVERITY_REMINDER)),
                rule_article=self._option(payload, "article"),
                message_link=self._option(payload, "lien"),
                admin_id=user.id,
            )
        except ValidationError as exc:
            return MSG_EMPTY_REASON if exc.field == "reason" else MSG_GENERIC_ERROR
        total = len(self.moderation.list_for_user(target.id))
        return (
            f"Infraction enregistrée pour <@{target.id}> — "
            f"{infraction.severity_label} ({total} au total)."
        )

    def _handle_infractions(self, game: Game | None, user: User, payload: dict) -> str:
        """``/infractions <membre>`` — list a member's infractions (admin-only).

        Mirrors the historical Mee6 ``!infractions`` output; the list is
        truncated to fit Discord's message length limit, newest first.
        """
        if not user.is_admin:
            return MSG_NOT_ADMIN
        target_id = str(self._option(payload, "membre") or "")
        infractions = self.moderation.list_for_user(target_id)
        if not infractions:
            return MSG_NO_INFRACTIONS

        header = f"**Infractions de <@{target_id}>** ({len(infractions)})"
        lines = [header]
        length = len(header)
        # Keep room for the "… et N de plus" note added when the list is cut.
        budget = DISCORD_MESSAGE_MAX_LENGTH - 40
        shown = 0
        for infraction in infractions:
            line = self._format_infraction(infraction)
            if length + 1 + len(line) > budget:
                break
            lines.append(line)
            length += 1 + len(line)
            shown += 1
        if shown < len(infractions):
            lines.append(f"… et {len(infractions) - shown} de plus")
        return "\n".join(lines)

    @staticmethod
    def _format_infraction(infraction: Infraction) -> str:
        """Build the one-line French summary of an infraction.

        Args:
            infraction: Infraction to format.

        Returns:
            ``- date — gravité — article — raison — par admin (lien)`` with the
            optional parts omitted when absent.
        """
        parts = [infraction.created_at.strftime("%d/%m/%Y"), infraction.severity_label]
        if infraction.rule_article:
            parts.append(infraction.rule_article)
        parts.append(infraction.reason)
        if infraction.admin_id:
            parts.append(f"par <@{infraction.admin_id}>")
        line = "- " + " — ".join(parts)
        if infraction.message_link:
            line += f" ({infraction.message_link})"
        return line

    # -------------------------------------------------------------------------
    # Resolution + authorization helpers
    # -------------------------------------------------------------------------

    def _resolve_user(self, payload: dict) -> User:
        """Get-or-create the QuestMaster user from the signed interaction caller.

        Args:
            payload: The interaction payload from Discord.

        Returns:
            The resolved User with roles freshly refreshed.
        """
        member = payload.get("member") or {}
        discord_user = member.get("user") or payload.get("user") or {}
        user, created = self.users.get_or_create(
            user_id=str(discord_user["id"]),
            name=discord_user.get("global_name") or discord_user.get("username", "Inconnu"),
            username=discord_user.get("username"),
        )
        if created:
            logger.info(f"User {user.id} created from a Discord interaction")
        user.refresh_roles()
        return user

    def _resolve_target_member(self, payload: dict) -> User:
        """Get-or-create the user targeted by a ``membre`` command option.

        Args:
            payload: The interaction payload from Discord.

        Returns:
            The target User with roles freshly refreshed.
        """
        target_id = str(self._option(payload, "membre") or "")
        target, created = self.users.get_or_create(target_id)
        if created:
            logger.info(f"User {target.id} created from a Discord interaction option")
        target.refresh_roles()
        return target

    def _resolve_game(self, payload: dict) -> Game | None:
        """Resolve the game from the channel the command ran in.

        Args:
            payload: The interaction payload from Discord.

        Returns:
            The matching Game, or None if the channel isn't a game channel.
        """
        channel_id = payload.get("channel_id")
        if not channel_id:
            return None
        return self.games.get_by_channel(channel_id)

    def _is_participant(self, game: Game, user: User) -> bool:
        """Tell whether the user is the GM, an admin, or a registered player.

        Args:
            game: Game the command targets.
            user: Invoking user (roles refreshed).

        Returns:
            True if the user may run participant-level commands.
        """
        return game.gm_id == user.id or user.is_admin or self.games.is_player(game, user.id)

    @staticmethod
    def _is_gm_or_admin(game: Game, user: User) -> bool:
        """Tell whether the user is the game's GM or an admin.

        Args:
            game: Game the command targets.
            user: Invoking user (roles refreshed).

        Returns:
            True if the user may run GM-level commands.
        """
        return game.gm_id == user.id or user.is_admin

    @staticmethod
    def _parse_datetime(raw: str) -> datetime:
        """Parse a ``JJ/MM/AAAA HH:MM`` option value.

        Args:
            raw: Raw option string.

        Returns:
            The parsed datetime.

        Raises:
            _CommandInputError: If the value doesn't match the format.
        """
        try:
            return datetime.strptime(raw, SLASH_DATE_FORMAT)
        except ValueError:
            raise _CommandInputError(MSG_BAD_DATE_FORMAT)

    @staticmethod
    def _parse_duration(raw: str) -> timedelta:
        """Parse a duration option value such as ``3h``, ``2h30`` or ``2.5``.

        Args:
            raw: Raw option string (comma accepted as decimal separator).

        Returns:
            The parsed duration.

        Raises:
            _CommandInputError: If the value doesn't match a supported form.
        """
        cleaned = raw.strip().lower().replace(",", ".").replace(" ", "")
        match = _DURATION_HM_RE.fullmatch(cleaned)
        if match:
            return timedelta(hours=int(match[1]), minutes=int(match[2] or 0))
        if _DURATION_HOURS_RE.fullmatch(cleaned):
            return timedelta(hours=float(cleaned))
        raise _CommandInputError(MSG_BAD_DURATION_FORMAT)

    def _resolve_end(
        self,
        payload: dict,
        start: datetime,
        default_duration: timedelta,
        end_option: str = "fin",
    ) -> datetime:
        """Compute a session end from the ``fin``/``duree`` options.

        Precedence: explicit end datetime, then explicit duration, then
        ``default_duration`` added to ``start``.

        Args:
            payload: The interaction payload from Discord.
            start: Session start the duration is added to.
            default_duration: Fallback when neither option is provided.
            end_option: Name of the end-datetime option (``fin`` or
                ``nouvelle_fin``).

        Returns:
            The resolved session end datetime.

        Raises:
            _CommandInputError: If a provided option value is malformed.
        """
        end_raw = self._option(payload, end_option)
        if end_raw:
            return self._parse_datetime(end_raw)
        duration_raw = self._option(payload, "duree")
        if duration_raw:
            return start + self._parse_duration(duration_raw)
        return start + default_duration

    @staticmethod
    def _find_session(game: Game, start: datetime):
        """Find the game session that starts exactly at ``start``.

        Args:
            game: Game whose sessions are searched.
            start: Session start datetime (as parsed from the command option).

        Returns:
            The matching GameSession, or None.
        """
        return next((s for s in game.sessions if s.start == start), None)

    @staticmethod
    def _option(payload: dict, name: str, default=None):
        """Read a slash-command option value from the interaction payload.

        Args:
            payload: The interaction payload from Discord.
            name: Option name to look up.
            default: Value returned when the option is absent.

        Returns:
            The option value, or ``default`` when missing.
        """
        for option in payload.get("data", {}).get("options") or []:
            if option.get("name") == name:
                return option.get("value", default)
        return default

    # -------------------------------------------------------------------------
    # Formatting
    # -------------------------------------------------------------------------

    @staticmethod
    def _game_summary(game: Game) -> str:
        """Build the compact French summary returned by ``/info``.

        Args:
            game: Game to summarize.

        Returns:
            Multi-line summary: name, announcement URL, role (or the player
            list when the game has no dedicated role), next session, status.
        """
        from website.utils.game_embeds import player_mentions

        lines = [
            f"**{game.name}**",
            f"Annonce : {SITE_BASE_URL}/annonces/{game.slug}/",
        ]
        if game.role:
            lines.append(f"Rôle : <@&{game.role}>")
        else:
            mentions = player_mentions(game)
            lines.append(f"Joueur·euses : {mentions}" if mentions else "Joueur·euses : aucun·e")
        upcoming = [s.start for s in game.sessions if s.start >= datetime.now()]
        lines.append(
            f"Prochaine session : {min(upcoming).strftime(HUMAN_TIMEFORMAT)}"
            if upcoming
            else "Prochaine session : aucune"
        )
        lines.append(f"Statut : {GAME_STATUS_LABELS.get(game.status, game.status)}")
        return "\n".join(lines)
