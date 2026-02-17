"""QuestMaster application factory and configuration."""

import os
import uuid

from flask import Flask, g
from flask_admin import Admin
from werkzeug.middleware.proxy_fix import ProxyFix

from website import models
from website.bot import set_bot
from website.client.discord import Discord
from website.extensions import cache, csrf, db, discord, migrate, seed_trophies, setup_test_db
from website.scheduler import start_scheduler
from website.utils import get_app_version
from website.utils.logger import configure_logging
from website.views import admin as admin_view
from website.views import register_blueprints, register_filters


def create_app():
    """Create and configure the Flask application.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Config
    app.secret_key = os.environ.get("FLASK_AUTH_SECRET")
    app.config.from_object("config.settings.Settings")

    # Logging
    configure_logging()

    @app.before_request
    def assign_trace_id():
        """Assign a unique trace ID to each request."""
        g.trace_id = str(uuid.uuid4())

    @app.after_request
    def add_trace_id_to_response(response):
        """Add the trace ID to the response headers."""
        response.headers["X-Trace-ID"] = g.trace_id
        return response

    @app.context_processor
    def inject_payload():
        """Inject user session payload into template context."""
        from flask import session

        from website.services import SpecialEventService

        special_event_service = SpecialEventService()
        active_events = special_event_service.get_active()
        payload = {
            "user_id": session.get("user_id"),
            "username": session.get("username"),
            "avatar": session.get("avatar"),
            "is_gm": session.get("is_gm"),
            "is_admin": session.get("is_admin"),
            "is_player": session.get("is_player"),
            "active_events": active_events,
        }
        return {"payload": payload}

    @app.context_processor
    def inject_guild_id():
        """Inject Discord guild ID into template context."""
        return {"DISCORD_GUILD_ID": app.config["DISCORD_GUILD_ID"]}

    @app.context_processor
    def inject_version():
        """Inject application version into template context."""
        return {"app_version": get_app_version()}

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)
    discord.init_app(app)
    app.cli.add_command(seed_trophies)
    app.cli.add_command(setup_test_db)

    # Create bot instance and store it
    bot_instance = Discord(app.config["DISCORD_GUILD_ID"], app.config["DISCORD_BOT_TOKEN"])
    set_bot(bot_instance)

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"  # Dev only

    # Admin
    app.config["FLASK_ADMIN_SWATCH"] = "cosmo"
    admin = Admin(
        app,
        name="QuestMaster Admin",
        index_view=admin_view.SecureAdminIndexView(),
    )
    admin.add_view(admin_view.UserAdmin(models.User, db.session, name="Utilisateurs"))
    admin.add_view(admin_view.GameAdmin(models.Game, db.session, name="Annonces"))
    admin.add_view(
        admin_view.SpecialEventAdmin(models.SpecialEvent, db.session, name="Événements")
    )
    admin.add_view(
        admin_view.UserTrophyAdmin(
            models.UserTrophy, db.session, name="Association Utilisateurs/Badges"
        )
    )
    admin.add_view(admin_view.AdminView(models.Trophy, db.session, name="Badges"))
    admin.add_view(admin_view.VttAdmin(models.Vtt, db.session, name="VTTs"))
    admin.add_view(admin_view.SystemAdmin(models.System, db.session, name="Systèmes"))
    admin.add_view(admin_view.ChannelAdmin(models.Channel, db.session, name="Catégories (salons)"))
    admin.add_view(admin_view.GameEventAdmin(models.GameEvent, db.session, name="Journaux"))

    register_blueprints(app)
    register_filters(app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Scheduled jobs
    with app.app_context():
        start_scheduler(app)

    return app
