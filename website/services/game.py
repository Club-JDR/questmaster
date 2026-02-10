"""Game service for business logic."""

from datetime import datetime, timedelta
from typing import Optional

from flask import current_app
from slugify import slugify
from sqlalchemy.exc import SQLAlchemyError

from config.constants import (
    BADGE_OS_ID,
    BADGE_OS_GM_ID,
    BADGE_CAMPAIGN_ID,
    BADGE_CAMPAIGN_GM_ID,
)
from website.exceptions import (
    ValidationError,
    NotFoundError,
    GameFullError,
    GameClosedError,
    DuplicateRegistrationError,
    DiscordAPIError,
)
from website.extensions import db
from website.models import Game, User
from website.repositories.game import GameRepository
from website.services.channel import ChannelService
from website.services.game_session import GameSessionService
from website.services.trophy import TrophyService
from website.services.user import UserService
from website.utils.discord import PLAYER_ROLE_PERMISSION
from website.utils.logger import logger, log_game_event


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
    ):
        self.repo = repository or GameRepository()
        self.user_service = user_service or UserService()
        self.channel_service = channel_service or ChannelService()
        self.session_service = session_service or GameSessionService()
        self.trophy_service = trophy_service or TrophyService()

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

    def generate_slug(self, name: str, gm_name: str) -> str:
        """Generate unique slug for a game.

        Args:
            name: Game name.
            gm_name: GM display name.

        Returns:
            Unique URL-safe slug.
        """
        existing_slugs = self.repo.get_all_slugs()
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
        bot=None,
        status: str = "draft",
        create_resources: bool = False,
    ) -> Game:
        """Create a new game.

        Args:
            data: Game data dictionary from form.
            gm_id: GM user ID.
            bot: Discord bot instance (optional, for resource creation).
            status: Initial status (draft, open, closed).
            create_resources: Whether to create Discord resources (role, channel).

        Returns:
            Created Game instance.

        Raises:
            ValidationError: If data is invalid.
            DiscordAPIError: If Discord resource creation fails.
        """
        from website.utils.form_parsers import get_classification, get_ambience, parse_restriction_tags
        from config.constants import DEFAULT_TIMEFORMAT

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
                date=datetime.strptime(data["date"], DEFAULT_TIMEFORMAT),
                session_length=data["session_length"],
                frequency=data.get("frequency") or None,
                characters=data["characters"],
                classification=get_classification(),
                ambience=get_ambience(data),
                complement=data.get("complement"),
                status=status,
                img=data.get("img"),
                party_selection="party_selection" in data,
                restriction_tags=parse_restriction_tags(data),
            )

            # Generate unique slug
            game.slug = self.generate_slug(data["name"], gm.name)

            # Add to session
            self.repo.add(game)
            db.session.flush()  # Ensure game.id is available

            logger.info(f"Game object created: {game.name} with slug {game.slug}")

            # Create Discord resources if requested
            if create_resources and bot:
                self._setup_game_resources(game, bot)
                logger.info("Game post-creation setup completed.")

            db.session.commit()
            log_game_event(
                "create",
                game.id,
                f"Annonce créée avec le statut {game.status}.",
            )
            logger.info(f"Game saved in DB with ID: {game.id}")

            return game

        except ValidationError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create game: {e}", exc_info=True)
            # Rollback Discord resources if they were created
            if create_resources and bot and hasattr(game, "role"):
                self._rollback_discord_resources(bot, game)
            raise

    def _setup_game_resources(self, game: Game, bot) -> None:
        """Set up Discord resources for a game (role, channel, session, channel message).

        Args:
            game: Game instance.
            bot: Discord bot instance.

        Raises:
            DiscordAPIError: If Discord operations fail.
        """
        from website.utils.game_embeds import send_discord_embed

        # Create initial game session
        self.session_service.create(
            game,
            game.date,
            game.date + timedelta(hours=float(game.session_length)),
        )
        logger.info("Initial game session created.")

        # Create Discord role
        game.role = bot.create_role(
            role_name="PJ_" + game.slug,
            permissions=PLAYER_ROLE_PERMISSION,
            color=Game.COLORS[game.type],
        )["id"]
        logger.info(f"Role created with ID: {game.role}")

        # Create Discord channel
        category = self.channel_service.get_category(game.type)
        game.channel = bot.create_channel(
            channel_name=game.slug.lower(),
            parent_id=category.id,
            role_id=game.role,
            gm_id=game.gm_id,
        )["id"]
        logger.info(f"Channel created with ID: {game.channel} under category: {category.id}")

        self.channel_service.increment_size(category)

        # Post initial message in the game channel
        send_discord_embed(game, type="annonce_details")
        logger.info("Initial channel message posted.")

    def _rollback_discord_resources(self, bot, game: Game) -> None:
        """Rollback Discord resources on error.

        Args:
            bot: Discord bot instance.
            game: Game instance with potentially created resources.
        """
        if game.channel:
            bot.delete_channel(game.channel)
            logger.info(f"Channel {game.channel} deleted")
        if game.role:
            bot.delete_role(game.role)
            logger.info(f"Role {game.role} deleted")

    def update(self, slug: str, data: dict, bot=None) -> Game:
        """Update an existing game.

        Args:
            slug: Game slug.
            data: Updated game data.
            bot: Discord bot instance (optional, for embed updates).

        Returns:
            Updated Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
            ValidationError: If data is invalid.
        """
        from website.utils.form_parsers import get_classification, get_ambience, parse_restriction_tags
        from config.constants import DEFAULT_TIMEFORMAT

        game = self.get_by_slug(slug)

        try:
            # Only allow type/name changes if game is draft
            if game.status == "draft":
                game_type, special_event_id = self.parse_game_type(data["type"])
                game.type = game_type
                game.special_event_id = special_event_id
                game.name = data["name"]

            # Update fields
            game.system_id = data["system"]
            game.vtt_id = data.get("vtt") or None
            game.description = data["description"]
            game.date = datetime.strptime(data["date"], DEFAULT_TIMEFORMAT)
            game.length = data["length"]
            game.party_size = data["party_size"]
            game.party_selection = "party_selection" in data
            game.xp = data["xp"]
            game.session_length = data["session_length"]
            game.frequency = data.get("frequency") or None
            game.characters = data["characters"]
            game.classification = get_classification()
            game.ambience = get_ambience(data)
            game.complement = data.get("complement")
            game.img = data.get("img")
            game.restriction = data["restriction"]
            game.restriction_tags = parse_restriction_tags(data)

            db.session.commit()
            log_game_event("edit", game.id, "Le contenu de l'annonce a été édité.")
            logger.info(f"Game {game.id} changes saved")

            # Update Discord embed if message exists
            if game.msg_id and bot:
                from website.utils.game_embeds import send_discord_embed

                try:
                    send_discord_embed(game, type="annonce")
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

    def publish(self, slug: str, bot, silent: bool = False) -> Game:
        """Publish a draft game to Discord.

        Args:
            slug: Game slug.
            bot: Discord bot instance.
            silent: If True, don't send announcement (set to closed instead of open).

        Returns:
            Published Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
            ValidationError: If game is already published or is full.
            DiscordAPIError: If Discord operations fail.
        """
        from website.utils.game_embeds import send_discord_embed

        game = self.get_by_slug(slug)

        if game.msg_id:
            raise ValidationError("Game is already published.", field="status")

        if len(game.players) >= game.party_size:
            raise ValidationError(
                "Cannot publish a full game.", field="party_size"
            )

        try:
            game.status = "closed" if silent else "open"

            # Set up resources if not already created
            if not game.role or not game.channel:
                self._setup_game_resources(game, bot)

            # Send Discord announcement if not silent
            if not silent:
                game.msg_id = send_discord_embed(game, type="annonce")
                logger.info(f"Discord embed sent with message ID: {game.msg_id}")

            db.session.commit()
            log_game_event(
                "edit",
                game.id,
                "L'annonce a été publiée et ouverte." if not silent else "L'annonce a été ouverte silencieusement.",
            )
            logger.info(f"Game {game.id} published and {'opened' if not silent else 'opened silently'}.")

            return game

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to publish game {game.id}: {e}", exc_info=True)
            # Rollback Discord resources if they were just created
            if not game.role or not game.channel:
                self._rollback_discord_resources(bot, game)
            raise

    def close(self, slug: str, bot=None) -> Game:
        """Close a game to new registrations.

        Args:
            slug: Game slug.
            bot: Discord bot instance (optional, for embed updates).

        Returns:
            Updated Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
        """
        game = self.get_by_slug(slug)
        game.status = "closed"

        db.session.commit()
        log_game_event("edit", game.id, "Le statut de l'annonce à changé en closed.")
        logger.info(f"Game status for {game.id} has been updated to closed")

        # Update Discord embed
        if game.msg_id and bot:
            from website.utils.game_embeds import send_discord_embed

            try:
                send_discord_embed(game, type="annonce")
                logger.info(f"Embed updated due to status change for game {game.id}")
            except DiscordAPIError as e:
                logger.warning(
                    f"Failed to update embed on status change for game {game.id}: {e}"
                )

        return game

    def reopen(self, slug: str, bot=None) -> Game:
        """Reopen a closed game.

        Args:
            slug: Game slug.
            bot: Discord bot instance (optional, for embed updates).

        Returns:
            Updated Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
        """
        game = self.get_by_slug(slug)
        game.status = "open"

        db.session.commit()
        log_game_event("edit", game.id, "Le statut de l'annonce à changé en open.")
        logger.info(f"Game status for {game.id} has been updated to open")

        # Update Discord embed
        if game.msg_id and bot:
            from website.utils.game_embeds import send_discord_embed

            try:
                send_discord_embed(game, type="annonce")
                logger.info(f"Embed updated due to status change for game {game.id}")
            except DiscordAPIError as e:
                logger.warning(
                    f"Failed to update embed on status change for game {game.id}: {e}"
                )

        return game

    def archive(self, slug: str, bot, award_trophies: bool = True) -> None:
        """Archive a game and clean up Discord resources.

        Args:
            slug: Game slug.
            bot: Discord bot instance.
            award_trophies: Whether to award trophies to participants.

        Raises:
            NotFoundError: If game doesn't exist.
        """
        game = self.get_by_slug(slug)
        game.status = "archived"

        db.session.commit()
        log_game_event("edit", game.id, "Le statut de l'annonce à changé en archived.")
        logger.info(f"Game status for {game.id} has been updated to archived")

        # Award trophies
        msg = "Annonce archivée."
        if award_trophies:
            self._award_game_trophies(game)
            msg += " Badges distribués."
        else:
            msg += " Badges non-distribués."

        # Clean up Discord resources
        self._cleanup_discord_resources(game, bot)
        self._delete_game_message(game, bot)

        log_game_event("delete", game.id, msg)

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

    def _cleanup_discord_resources(self, game: Game, bot) -> None:
        """Clean up Discord resources for a game.

        Args:
            game: Game instance.
            bot: Discord bot instance.
        """
        self.channel_service.adjust_category_size(bot, game)

        try:
            bot.delete_channel(game.channel)
            logger.info(f"Game {game.id} channel {game.channel} has been deleted")
        except DiscordAPIError as e:
            logger.warning(f"Failed to delete channel for game {game.id}: {e}")

        try:
            bot.delete_role(game.role)
            logger.info(f"Game {game.id} role {game.role} has been deleted")
        except DiscordAPIError as e:
            logger.warning(f"Failed to delete role for game {game.id}: {e}")

    def _delete_game_message(self, game: Game, bot) -> None:
        """Delete Discord announcement message.

        Args:
            game: Game instance.
            bot: Discord bot instance.
        """
        if not game.msg_id:
            return

        try:
            bot.delete_message(game.msg_id, current_app.config["POSTS_CHANNEL_ID"])
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
        self.repo.delete_by_id(game.id)
        db.session.commit()
        logger.info(f"Game {game.id} has been deleted.")

    def register_player(
        self, slug: str, user_id: str, bot, force: bool = False
    ) -> Game:
        """Register a player to a game (concurrent-safe).

        Args:
            slug: Game slug.
            user_id: User ID to register.
            bot: Discord bot instance.
            force: If True, bypass capacity and status checks.

        Returns:
            Updated Game instance.

        Raises:
            NotFoundError: If game doesn't exist.
            DuplicateRegistrationError: If user is already registered.
            GameFullError: If game is at capacity and force is False.
            GameClosedError: If game is closed and force is False.
        """
        from website.utils.game_embeds import send_discord_embed

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

            # Check if already registered
            if user in locked_game.players:
                raise DuplicateRegistrationError(
                    "User is already registered for this game.",
                    game_id=locked_game.id,
                    user_id=user.id,
                )

            # Check capacity
            if len(locked_game.players) >= locked_game.party_size and not force:
                raise GameFullError(
                    "Game is full.",
                    game_id=locked_game.id,
                    max_players=locked_game.party_size,
                )

            # Check status
            if locked_game.status == "closed" and not force:
                raise GameClosedError(
                    "Game is closed for registration.",
                    game_id=locked_game.id,
                )

            # Add player
            locked_game.players.append(user)

            # Auto-close if full
            if (
                len(locked_game.players) >= locked_game.party_size
                and not locked_game.party_selection
            ):
                locked_game.status = "closed"
                if locked_game.msg_id:
                    try:
                        send_discord_embed(locked_game, type="annonce")
                        logger.info(
                            f"Embed updated due to status change for game {locked_game.id}"
                        )
                    except DiscordAPIError as e:
                        logger.warning(
                            f"Failed to update embed on status change for game {locked_game.id}: {e}"
                        )
                log_game_event(
                    "edit",
                    locked_game.id,
                    f"Annonce fermée automatiquement après avoir atteint le nombre max de joueur·euses ({locked_game.party_size}).",
                )
                logger.info(
                    f"Game status for {locked_game.id} has been updated to closed"
                )

            db.session.commit()

            # Log event
            if force:
                log_game_event(
                    "register",
                    locked_game.id,
                    f"{user.display_name} a été inscrit à l'annonce par le MJ ou un admin.",
                )
            else:
                log_game_event(
                    "register",
                    locked_game.id,
                    f"{user.display_name} s'est inscrit sur l'annonce.",
                )

            logger.info(f"User {user.id} registered to Game {locked_game.id}")

            # Add Discord role
            bot.add_role_to_user(user.id, locked_game.role)
            logger.info(f"Role {locked_game.role} added to user {user.id}")

            # Send registration embed
            send_discord_embed(locked_game, type="register", player=user.id)

            return locked_game

        except (DuplicateRegistrationError, GameFullError, GameClosedError):
            db.session.rollback()
            raise
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception("Failed to register user due to DB error.")
            raise

    def unregister_player(self, slug: str, user_id: str, bot) -> Game:
        """Unregister a player from a game.

        Args:
            slug: Game slug.
            user_id: User ID to unregister.
            bot: Discord bot instance.

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

        # Reopen if it was full
        if (
            game.status == "closed"
            and len(game.players) < game.party_size
            and not game.party_selection
        ):
            game.status = "open"
            log_game_event(
                "edit",
                game.id,
                "Annonce rouverte automatiquement après désinscription.",
            )

        db.session.commit()
        logger.info(f"User {user.id} removed from Game {game.id}")

        # Remove Discord role
        bot.remove_role_from_user(user.id, game.role)
        logger.info(f"Role {game.role} removed from Player {user.id}")

        log_game_event(
            "unregister",
            game.id,
            f"{user.display_name} a été désinscrit de l'annonce.",
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
