"""Game service for business logic."""

from datetime import datetime, timedelta
from typing import Optional

from slugify import slugify
from sqlalchemy.exc import SQLAlchemyError

from config.constants import (
    BADGE_CAMPAIGN_GM_ID,
    BADGE_CAMPAIGN_ID,
    BADGE_OS_GM_ID,
    BADGE_OS_ID,
    PLAYER_ROLE_PERMISSION,
    SITE_BASE_URL,
)
from website.exceptions import (
    DiscordAPIError,
    DuplicateRegistrationError,
    GameClosedError,
    GameFullError,
    NotFoundError,
    ValidationError,
)
from website.extensions import db
from website.models import Game, User
from website.repositories.game import GameRepository
from website.services.channel import ChannelService
from website.services.game_session import GameSessionService
from website.services.trophy import TrophyService
from website.services.user import UserService
from website.utils.logger import log_game_event, logger


class GameService:
    """Service layer for Game business logic.

    Handles game creation, updates, status transitions, player registration,
    and Discord integration. Owns transaction boundaries (commits).
    """

    def __init__(
        self,
        repository=None,
        user_service=None,
        channel_service=None,
        session_service=None,
        trophy_service=None,
        discord_service=None,
        settings_service=None,
    ):
        from website.services.discord import DiscordService
        from website.services.setting import SettingsService

        self.repo = repository or GameRepository()
        self.user_service = user_service or UserService()
        self.channel_service = channel_service or ChannelService()
        self.session_service = session_service or GameSessionService()
        self.trophy_service = trophy_service or TrophyService()
        self.discord = discord_service or DiscordService()
        self.settings_service = settings_service or SettingsService()

    def list_all(self) -> list[Game]:
        """List all games ordered by date (most recent first).

        Intended for the admin panel.

        Returns:
            List of Game instances.
        """
        return self.repo.get_all_ordered()

    def get_open_preview(self, user_payload: dict) -> dict:
        """Return the dashboard's "Annonces ouvertes" preview.

        Previews the latest open announcements, capped at the admin-configurable
        ``dashboard_open_limit`` setting. ``open_hidden`` is how many further open
        games exist beyond the preview (drives the "Voir tout" link).

        Args:
            user_payload: Auth payload (used only for draft visibility rules; the
                open-status query never exposes drafts). May be anonymous.

        Returns:
            Dict with ``open_games`` (a list of Game models) and ``open_hidden``
            (int count of open games beyond the preview).
        """
        open_limit = self.settings_service.get_dashboard_open_limit()
        open_games, open_total = self.repo.search(
            {"status": ["open"]}, page=1, per_page=open_limit, user_payload=user_payload
        )
        return {
            "open_games": open_games,
            "open_hidden": max(open_total - len(open_games), 0),
        }

    @staticmethod
    def _invalidate_dashboard_stats(*user_ids: str) -> None:
        """Drop cached dashboard stats for the given users (ignoring falsy IDs)."""
        from website.services.stats import StatsService

        stats_service = StatsService()
        for user_id in user_ids:
            if user_id:
                stats_service.invalidate(user_id)

    def list_paginated(self, page: int = 1, per_page: int = 25, search: str | None = None):
        """List games (all statuses) paginated, for the admin panel.

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            search: Optional term matched against game name and slug.

        Returns:
            Pagination result of Game instances ordered by date (newest first).
        """
        return self.repo.paginate(page=page, per_page=per_page, search=search)

    def list_by_gm(self, gm_id: str) -> list[Game]:
        """List all games run by a given GM.

        Args:
            gm_id: GM user ID.

        Returns:
            List of Game instances GMed by this user.
        """
        return self.repo.find_by_gm(gm_id)

    def list_by_player(self, player_id: str) -> list[Game]:
        """List all games a given user is registered to as a player.

        Args:
            player_id: Player user ID.

        Returns:
            List of Game instances where the user is a registered player.
        """
        return self.repo.find_by_player(player_id)

    def list_by_special_event(self, event_id: int) -> list[Game]:
        """List all games linked to a given special event.

        Args:
            event_id: Special event ID.

        Returns:
            List of Game instances linked to this special event.
        """
        return self.repo.find_by_special_event(event_id)

    def admin_update(self, game_id: int, data: dict) -> Game:
        """Update a game's fields directly from the admin panel.

        Unlike :meth:`update`, this performs a direct field assignment of any
        provided column (including ``slug``, ``status``, and Discord identifiers)
        without slug regeneration, draft-only guards, or Discord embed syncing.
        It mirrors the behaviour of the previous Flask-Admin model editor.

        Args:
            game_id: Game ID.
            data: Dictionary of fields to update.

        Returns:
            Updated Game instance.

        Raises:
            NotFoundError: If the game doesn't exist.
            ValidationError: If a field value is invalid.
        """
        game = self.get_by_id(game_id)

        try:
            # Slug is protected by update_from_dict; the admin may edit it explicitly.
            if "slug" in data:
                game.slug = data["slug"]
            game.update_from_dict(data)
            db.session.commit()
            logger.info(f"Game {game.id} updated via admin panel")
            return game
        except ValidationError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to admin-update game {game_id}: {e}", exc_info=True)
            raise

    def get_by_id(self, game_id: int) -> Game:
        """Get game by ID.

        Args:
            game_id: Game ID.

        Returns:
            Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
        """
        game = self.repo.get_by_id(game_id)
        if not game:
            raise NotFoundError(
                f"Game with id {game_id} not found",
                resource_type="Game",
                resource_id=game_id,
            )
        return game

    def get_by_slug(self, slug: str) -> Game:
        """Get game by slug.

        Args:
            slug: URL-safe game identifier.

        Returns:
            Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
        """
        game = self.repo.get_by_slug(slug)
        if not game:
            raise NotFoundError(
                f"Game with slug '{slug}' not found",
                resource_type="Game",
                resource_id=slug,
            )
        return game

    def get_by_slug_or_404(self, slug: str) -> Game:
        """Get game by slug or raise 404 (for Flask routes).

        Args:
            slug: URL-safe game identifier.

        Returns:
            Game instance.

        Raises:
            NotFound: Flask 404 error.
        """
        return self.repo.get_by_slug_or_404(slug)

    def generate_slug(self, name: str, gm_name: str, exclude_slug: str | None = None) -> str:
        """Generate unique slug for a game.

        Args:
            name: Game name.
            gm_name: GM stable username (preferred) or display name (fallback).
            exclude_slug: Slug to exclude from uniqueness check (used when renaming a game).

        Returns:
            Unique URL-safe slug.
        """
        existing_slugs = self.repo.get_all_slugs()
        if exclude_slug:
            existing_slugs.discard(exclude_slug)
        base_slug = slugify(f"{name}-par-{gm_name}")
        slug = base_slug
        i = 2
        while slug in existing_slugs:
            slug = f"{base_slug}-{i}"
            i += 1
        return slug

    def parse_game_type(self, type_value: str) -> tuple[str, Optional[int]]:
        """Parse game type value from form.

        Args:
            type_value: Type string, possibly "specialevent-<id>".

        Returns:
            Tuple of (game_type, special_event_id).
        """
        special_event_id = None
        game_type = type_value

        if type_value and type_value.startswith("specialevent-"):
            try:
                special_event_id = int(type_value.split("-", 1)[1])
            except (ValueError, IndexError):
                special_event_id = None
            game_type = "oneshot"  # all special events are treated as oneshots

        return game_type, special_event_id

    def create(
        self,
        data: dict,
        gm_id: str,
        status: str = "draft",
        create_resources: bool = False,
    ) -> Game:
        """Create a new game.

        Args:
            data: Game data dictionary from form.
            gm_id: GM user ID.
            status: Initial status (draft, open, closed).
            create_resources: Whether to create Discord resources (role, channel).

        Returns:
            Created Game instance.

        Raises:
            ValidationError: If data is invalid.
            DiscordAPIError: If Discord resource creation fails.
        """
        from website.utils.form_parsers import (
            get_ambience,
            get_classification,
            parse_restriction_tags,
        )

        try:
            # Parse special fields
            game_type, special_event_id = self.parse_game_type(data["type"])

            # Get GM name for slug
            gm = self.user_service.get_by_id(gm_id)

            # Create game instance
            game = Game(
                name=data["name"],
                type=game_type,
                special_event_id=special_event_id,
                length=data["length"],
                gm_id=gm_id,
                system_id=data["system"],
                vtt_id=data.get("vtt") or None,
                description=data["description"],
                restriction=data["restriction"],
                party_size=data["party_size"],
                xp=data["xp"],
                date=datetime.fromisoformat(data["date"].replace("T", " ")[:16]),
                session_length=data["session_length"],
                frequency=data.get("frequency") or None,
                characters=data["characters"],
                classification=get_classification(data),
                ambience=get_ambience(data),
                complement=data.get("complement"),
                status=status,
                img=data.get("img"),
                party_selection="party_selection" in data,
                restriction_tags=parse_restriction_tags(data),
            )

            # Generate unique slug
            game.slug = self.generate_slug(data["name"], gm.slug_name)

            # Add to session
            self.repo.add(game)
            db.session.flush()  # Ensure game.id is available

            logger.info(f"Game object created: {game.name} with slug {game.slug}")

            # Create Discord resources if requested
            if create_resources:
                self._setup_game_resources(game)
                logger.info("Game post-creation setup completed.")

            db.session.commit()
            log_game_event(
                "create",
                game.id,
                f"Annonce créée avec le statut {game.status}.",
                user_id=game.gm_id,
            )
            logger.info(f"Game saved in DB with ID: {game.id}")

            self._invalidate_dashboard_stats(game.gm_id)
            return game

        except ValidationError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create game: {e}", exc_info=True)
            # Rollback Discord resources if they were created
            if create_resources and hasattr(game, "role"):
                self._rollback_discord_resources(game)
            raise

    def _setup_game_resources(self, game: Game) -> None:
        """Set up Discord resources for a game (role, channel, session, channel message).

        Args:
            game: Game instance.

        Raises:
            DiscordAPIError: If Discord operations fail.
        """
        # Create initial game session
        self.session_service.create(
            game,
            game.date,
            game.date + timedelta(hours=float(game.session_length)),
        )
        logger.info("Initial game session created.")

        # In direct-permission mode, skip role creation: players are granted channel
        # access via per-member permission overwrites instead of a dedicated role.
        direct_permissions = self.settings_service.is_direct_permissions_enabled()
        if direct_permissions:
            logger.info("Direct-permission mode: skipping role creation for game.")
        else:
            game.role = self.discord.create_role(
                name="PJ_" + game.slug,
                permissions=PLAYER_ROLE_PERMISSION,
                color=Game.COLORS[game.type],
            )["id"]
            logger.info(f"Role created with ID: {game.role}")

        # Create Discord channel (without a player-role overwrite in direct mode)
        category = self.channel_service.get_category(game.type)
        game.channel = self.discord.create_channel(
            name=game.slug.lower(),
            parent_id=category.id,
            role_id=game.role,
            gm_id=game.gm_id,
        )["id"]
        logger.info(f"Channel created with ID: {game.channel} under category: {category.id}")

        self.channel_service.increment_size(category)

        # Post and pin initial message in the game channel
        msg_id = self.discord.send_game_embed(game, embed_type="annonce_details")
        self.discord.pin_message(msg_id, game.channel)
        logger.info("Initial channel message posted and pinned.")

    def _rollback_discord_resources(self, game: Game) -> None:
        """Rollback Discord resources on error.

        Args:
            game: Game instance with potentially created resources.
        """
        if game.channel:
            self.discord.delete_channel(game.channel)
            logger.info(f"Channel {game.channel} deleted")
        if game.role:
            self.discord.delete_role(game.role)
            logger.info(f"Role {game.role} deleted")

    def update(self, slug: str, data: dict, user_id: str | None = None) -> Game:
        """Update an existing game.

        Args:
            slug: Game slug.
            data: Updated game data.
            user_id: ID of the user performing the update.

        Returns:
            Updated Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
            ValidationError: If data is invalid.
        """
        from website.utils.form_parsers import (
            get_ambience,
            get_classification,
            parse_restriction_tags,
        )

        game = self.get_by_slug(slug)

        try:
            # Only allow type/name changes if game is draft
            if game.status == "draft":
                game_type, special_event_id = self.parse_game_type(data["type"])
                game.type = game_type
                game.special_event_id = special_event_id
                if data["name"] != game.name:
                    gm = self.user_service.get_by_id(game.gm_id)
                    game.slug = self.generate_slug(
                        data["name"], gm.slug_name, exclude_slug=game.slug
                    )
                game.name = data["name"]

            # Update fields
            game.system_id = data["system"]
            game.vtt_id = data.get("vtt") or None
            game.description = data["description"]
            game.date = datetime.fromisoformat(data["date"].replace("T", " ")[:16])
            game.length = data["length"]
            game.party_size = data["party_size"]
            game.party_selection = "party_selection" in data
            game.xp = data["xp"]
            game.session_length = data["session_length"]
            game.frequency = data.get("frequency") or None
            game.characters = data["characters"]
            game.classification = get_classification(data)
            game.ambience = get_ambience(data)
            game.complement = data.get("complement")
            game.img = data.get("img")
            game.restriction = data["restriction"]
            game.restriction_tags = parse_restriction_tags(data)

            db.session.commit()
            log_game_event(
                "edit", game.id, "Le contenu de l'annonce a été édité.", user_id=user_id
            )
            logger.info(f"Game {game.id} changes saved")

            # Update Discord embed if message exists
            if game.msg_id:
                try:
                    self.discord.send_game_embed(game, embed_type="annonce")
                    logger.info(f"Embed updated for game {game.id}")
                except DiscordAPIError as e:
                    logger.warning(f"Failed to update Discord embed for game {game.id}: {e}")

            return game

        except ValidationError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update game {game.id}: {e}", exc_info=True)
            raise

    def publish(self, slug: str, silent: bool = False, user_id: str | None = None) -> Game:
        """Publish a draft game to Discord.

        Args:
            slug: Game slug.
            silent: If True, don't send announcement (set to closed instead of open).
            user_id: ID of the user performing the publish.

        Returns:
            Published Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
            ValidationError: If game is already published or is full.
            DiscordAPIError: If Discord operations fail.
        """
        game = self.get_by_slug(slug)

        if game.msg_id:
            raise ValidationError("Game is already published.", field="status")

        if len(game.players) >= game.party_size:
            raise ValidationError("Cannot publish a full game.", field="party_size")

        try:
            game.status = "closed" if silent else "open"

            # Set up resources if not already created
            if not game.role or not game.channel:
                self._setup_game_resources(game)

            # Send Discord announcement if not silent
            if not silent:
                game.msg_id = self.discord.send_game_embed(game, embed_type="annonce")
                logger.info(f"Discord embed sent with message ID: {game.msg_id}")

            db.session.commit()
            log_game_event(
                "edit",
                game.id,
                (
                    "L'annonce a été publiée et ouverte."
                    if not silent
                    else "L'annonce a été ouverte silencieusement."
                ),
                user_id=user_id,
            )
            logger.info(
                f"Game {game.id} published and {'opened' if not silent else 'opened silently'}."
            )

            return game

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to publish game {game.id}: {e}", exc_info=True)
            # Rollback Discord resources if they were just created
            if not game.role or not game.channel:
                self._rollback_discord_resources(game)
            raise

    def close(self, slug: str, user_id: str | None = None) -> Game:
        """Close a game to new registrations.

        Args:
            slug: Game slug.
            user_id: ID of the user performing the close.

        Returns:
            Updated Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
        """
        game = self.get_by_slug(slug)
        game.status = "closed"

        db.session.commit()
        log_game_event(
            "edit", game.id, "L'annonce a été fermée aux inscriptions.", user_id=user_id
        )
        logger.info(f"Game status for {game.id} has been updated to closed")

        # Update Discord embed
        if game.msg_id:
            try:
                self.discord.send_game_embed(game, embed_type="annonce")
                logger.info(f"Embed updated due to status change for game {game.id}")
            except DiscordAPIError as e:
                logger.warning(f"Failed to update embed on status change for game {game.id}: {e}")

        return game

    def reopen(self, slug: str, user_id: str | None = None) -> Game:
        """Reopen a closed game.

        Args:
            slug: Game slug.
            user_id: ID of the user performing the reopen.

        Returns:
            Updated Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
        """
        game = self.get_by_slug(slug)
        game.status = "open"

        db.session.commit()
        log_game_event(
            "edit", game.id, "L'annonce a été ouverte aux inscriptions.", user_id=user_id
        )
        logger.info(f"Game status for {game.id} has been updated to open")

        # Update Discord embed
        if game.msg_id:
            try:
                self.discord.send_game_embed(game, embed_type="annonce")
                logger.info(f"Embed updated due to status change for game {game.id}")
            except DiscordAPIError as e:
                logger.warning(f"Failed to update embed on status change for game {game.id}: {e}")

        return game

    def archive(self, slug: str, award_trophies: bool = True, user_id: str | None = None) -> None:
        """Archive a game and clean up Discord resources.

        Args:
            slug: Game slug.
            award_trophies: Whether to award trophies to participants.
            user_id: ID of the user performing the archive.

        Raises:
            NotFoundError: If game doesn't exist.

        Note:
            Idempotent: calling on an already-archived game is a no-op, preventing
            double trophy awards on duplicate form submissions or browser retries.
        """
        game = self.get_by_slug(slug)
        if game.status == "archived":
            return
        game.status = "archived"

        db.session.commit()
        log_game_event("edit", game.id, "L'annonce a été archivée.", user_id=user_id)
        logger.info(f"Game status for {game.id} has been updated to archived")

        # Award trophies
        msg = "Annonce archivée."
        if award_trophies:
            self._award_game_trophies(game)
            msg += " Badges distribués."
        else:
            msg += " Badges non-distribués."

        # Clean up Discord resources
        self._cleanup_discord_resources(game)
        self._delete_game_message(game)

        log_game_event("delete", game.id, msg, user_id=user_id)

        # Awarded badges + a now-archived game change everyone's stats.
        self._invalidate_dashboard_stats(game.gm_id, *(p.id for p in game.players))

    def _award_game_trophies(self, game: Game) -> None:
        """Award trophies to GM and players.

        Args:
            game: Game instance.
        """
        trophy_map = {
            "oneshot": (BADGE_OS_GM_ID, BADGE_OS_ID),
            "campaign": (BADGE_CAMPAIGN_GM_ID, BADGE_CAMPAIGN_ID),
        }
        gm_trophy, player_trophy = trophy_map.get(game.type, (None, None))
        if gm_trophy:
            try:
                self.trophy_service.award(user_id=game.gm.id, trophy_id=gm_trophy)
                for user in game.players:
                    self.trophy_service.award(user_id=user.id, trophy_id=player_trophy)
            except Exception as e:
                logger.error(f"Failed to award trophies for game {game.id}: {e}")

    def _cleanup_discord_resources(self, game: Game) -> None:
        """Clean up Discord resources for a game.

        Args:
            game: Game instance.
        """
        self.channel_service.adjust_category_size(self.discord, game)

        try:
            self.discord.delete_channel(game.channel)
            logger.info(f"Game {game.id} channel {game.channel} has been deleted")
        except DiscordAPIError as e:
            logger.warning(f"Failed to delete channel for game {game.id}: {e}")

        # Direct-permission games have no role (per-member overwrites are removed
        # with the channel), so only delete a role when one exists.
        if game.role:
            try:
                self.discord.delete_role(game.role)
                logger.info(f"Game {game.id} role {game.role} has been deleted")
            except DiscordAPIError as e:
                logger.warning(f"Failed to delete role for game {game.id}: {e}")

    def _auto_close_if_full(self, game: Game) -> None:
        """Close the game and update the Discord embed if it has reached capacity.

        Args:
            game: Locked game instance.
        """
        if len(game.players) < game.party_size or game.party_selection:
            return

        game.status = "closed"
        if game.msg_id:
            try:
                self.discord.send_game_embed(game, embed_type="annonce")
                logger.info(f"Embed updated due to status change for game {game.id}")
            except DiscordAPIError as e:
                logger.warning(f"Failed to update embed on status change for game {game.id}: {e}")
        log_game_event(
            "edit",
            game.id,
            "Annonce fermée automatiquement après avoir atteint le nombre "
            f"max de joueur·euses ({game.party_size}).",
        )
        logger.info(f"Game status for {game.id} has been updated to closed")

    def _auto_reopen_if_space(self, game: Game) -> bool:
        """Reopen a game that was auto-closed once a seat frees up.

        Mirror of :meth:`_auto_close_if_full`. Party-selection games are never
        reopened automatically (the GM curates the roster).

        Args:
            game: Game instance a player was just removed from.

        Returns:
            True if the game was reopened, False otherwise.
        """
        if game.status != "closed" or len(game.players) >= game.party_size or game.party_selection:
            return False

        game.status = "open"
        log_game_event(
            "edit",
            game.id,
            "Annonce rouverte automatiquement après désinscription.",
        )
        return True

    def _validate_registration(self, game: Game, user: User, force: bool) -> None:
        """Validate that a user may register for a game.

        Args:
            game: Locked game instance.
            user: User attempting to register.
            force: If True, bypass capacity and status checks.

        Raises:
            DuplicateRegistrationError: If the user is already registered.
            GameFullError: If the game is at capacity and force is False.
            GameClosedError: If the game is closed and force is False.
        """
        if user in game.players:
            raise DuplicateRegistrationError(
                "User is already registered for this game.",
                game_id=game.id,
                user_id=user.id,
            )

        if len(game.players) >= game.party_size and not force:
            raise GameFullError(
                "Game is full.",
                game_id=game.id,
                max_players=game.party_size,
            )

        if game.status == "closed" and not force:
            raise GameClosedError(
                "Game is closed for registration.",
                game_id=game.id,
            )

    def _log_registration_event(self, game: Game, user: User, force: bool) -> None:
        """Log a registration event, distinguishing self-registration from a GM add.

        Args:
            game: Game the user was registered to.
            user: User that was registered.
            force: If True, the player was added by the GM.
        """
        msg = (
            "Le·a joueur·euse a été ajouté·e à la partie par le MJ."
            if force
            else "Le·a joueur·euse s'est inscrit·e sur l'annonce."
        )
        log_game_event("register", game.id, msg, user_id=user.id)

    def _delete_game_message(self, game: Game) -> None:
        """Delete Discord announcement message.

        Args:
            game: Game instance.
        """
        if not game.msg_id:
            return

        try:
            self.discord.delete_message(game.msg_id, self.settings_service.get("POSTS_CHANNEL_ID"))
            game.msg_id = None
            db.session.commit()
            logger.info(f"Discord embed message deleted for archived game {game.id}")
        except DiscordAPIError as e:
            logger.warning(f"Failed to delete message for archived game {game.id}: {e}")

    def delete(self, slug: str) -> None:
        """Delete a game permanently.

        Args:
            slug: Game slug.

        Raises:
            NotFoundError: If game doesn't exist.
        """
        game = self.get_by_slug(slug)
        affected = [game.gm_id, *(p.id for p in game.players)]
        self.repo.delete_by_id(game.id)
        db.session.commit()
        logger.info(f"Game {game.id} has been deleted.")
        self._invalidate_dashboard_stats(*affected)

    def register_player(self, slug: str, user_id: str, force: bool = False) -> Game:
        """Register a player to a game (concurrent-safe).

        Args:
            slug: Game slug.
            user_id: User ID to register.
            force: If True, bypass capacity and status checks.

        Returns:
            Updated Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
            DuplicateRegistrationError: If user is already registered.
            GameFullError: If game is at capacity and force is False.
            GameClosedError: If game is closed and force is False.
        """
        game = self.get_by_slug(slug)
        user = self.user_service.get_by_id(user_id)

        try:
            # Lock the game row for update
            locked_game = self.repo.get_for_update(game.id)
            if not locked_game:
                raise NotFoundError(
                    f"Game with id {game.id} not found",
                    resource_type="Game",
                    resource_id=game.id,
                )

            self._validate_registration(locked_game, user, force)

            locked_game.players.append(user)
            self._auto_close_if_full(locked_game)

            db.session.commit()

            self._log_registration_event(locked_game, user, force)
            logger.info(f"User {user.id} registered to Game {locked_game.id}")

            # Grant channel access: dedicated role, or a per-member permission
            # overwrite when the game runs in direct-permission mode (no role).
            if locked_game.role:
                self.discord.add_role_to_user(user.id, locked_game.role)
                logger.info(f"Role {locked_game.role} added to user {user.id}")
            elif locked_game.channel:
                self.discord.set_channel_permission(
                    locked_game.channel, user.id, PLAYER_ROLE_PERMISSION
                )
                logger.info(
                    f"Channel permission granted to user {user.id} on {locked_game.channel}"
                )

            # Send registration embed
            self.discord.send_game_embed(locked_game, embed_type="register", player=user.id)

            self._invalidate_dashboard_stats(user.id, locked_game.gm_id)
            return locked_game

        except (DuplicateRegistrationError, GameFullError, GameClosedError):
            db.session.rollback()
            raise
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception("Failed to register user due to DB error.")
            raise

    def unregister_player(self, slug: str, user_id: str) -> Game:
        """Unregister a player from a game.

        Args:
            slug: Game slug.
            user_id: User ID to unregister.

        Returns:
            Updated Game instance.

        Raises:
            NotFoundError: If game or user doesn't exist.
            ValidationError: If user is not registered.
        """
        game = self.get_by_slug(slug)
        user = self.user_service.get_by_id(user_id)

        if user not in game.players:
            raise ValidationError(
                "User is not registered for this game.",
                field="user_id",
            )

        game.players.remove(user)
        reopened = self._auto_reopen_if_space(game)

        db.session.commit()
        logger.info(f"User {user.id} removed from Game {game.id}")

        # Refresh the announcement embed so its title and register button reflect
        # the reopened status.
        if reopened and game.msg_id:
            try:
                self.discord.send_game_embed(game, embed_type="annonce")
            except DiscordAPIError as e:
                logger.warning(f"Failed to update embed on status change for game {game.id}: {e}")

        # Revoke channel access: dedicated role, or the per-member permission
        # overwrite when the game runs in direct-permission mode (no role).
        if game.role:
            self.discord.remove_role_from_user(user.id, game.role)
            logger.info(f"Role {game.role} removed from Player {user.id}")
        elif game.channel:
            self.discord.delete_channel_permission(game.channel, user.id)
            logger.info(f"Channel permission removed from user {user.id} on {game.channel}")

        log_game_event(
            "unregister",
            game.id,
            "Le·a joueur·euse a été désinscrit·e de l'annonce.",
            user_id=user.id,
        )

        self._invalidate_dashboard_stats(user.id, game.gm_id)
        return game

    def notify_players(self, slug: str, message: str, user_id: str | None = None) -> Game:
        """Notify a game's players by posting a message in its Discord channel.

        Replaces the GM's manual role mention: the message is posted in the game
        channel and pings the dedicated player role (role mode) or every registered
        player individually (direct-permission mode).

        Args:
            slug: Game slug.
            message: Free-text message written by the GM.
            user_id: ID of the user sending the notification.

        Returns:
            The Game instance.

        Raises:
            NotFoundError: If the game doesn't exist.
            ValidationError: If the message is empty or the game has no channel.
            DiscordAPIError: If the Discord request fails.
        """
        from website.utils.game_embeds import player_mentions

        game = self.get_by_slug(slug)

        cleaned = (message or "").strip()
        if not cleaned:
            raise ValidationError("Notification message is required.", field="message")
        if not game.channel:
            raise ValidationError("Game has no Discord channel.", field="channel")

        mentions = player_mentions(game)
        game_url = f"{SITE_BASE_URL}/annonces/{game.slug}/"
        content = (
            f"{mentions}\n"
            f"📣 **{game.name}** — un message de votre MJ :\n\n"
            f"{cleaned}\n\n"
            f"🔗 L'annonce sur QuestMaster : {game_url}"
        ).strip()

        self.discord.send_message(
            content,
            game.channel,
            allowed_mentions={"parse": ["users", "roles"]},
        )
        logger.info(f"Notification posted in channel {game.channel} for game {game.id}")
        log_game_event(
            "edit",
            game.id,
            "Le MJ a notifié les joueur·euses dans le salon.",
            user_id=user_id,
        )

        return game

    def clone(self, slug: str) -> dict:
        """Clone a game (return data dict for form prefill).

        Args:
            slug: Game slug to clone.

        Returns:
            Dict with game data for form.

        Raises:
            NotFoundError: If game doesn't exist.
        """
        game = self.get_by_slug(slug)
        return game.to_dict(include_relationships=False)

    def is_player(self, game: Game, user_id: str) -> bool:
        """Check if a user is registered as a player in a game.

        Args:
            game: Game instance.
            user_id: User ID to check.

        Returns:
            True if the user is a registered player.
        """
        return any(p.id == user_id for p in game.players)

    def search(
        self,
        filters: dict,
        page: int = 1,
        per_page: int = 20,
        user_payload: Optional[dict] = None,
    ) -> tuple[list[Game], int]:
        """Search games with filters.

        Args:
            filters: Search filters dict.
            page: Page number.
            per_page: Items per page.
            user_payload: User auth payload.

        Returns:
            Tuple of (games list, total count).
        """
        return self.repo.search(filters, page, per_page, user_payload)
