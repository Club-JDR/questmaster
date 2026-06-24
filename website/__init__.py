"""QuestMaster application factory and configuration."""

import os
import uuid

from flask import Flask, g
from werkzeug.middleware.proxy_fix import ProxyFix

from website.bot import set_bot
from website.client.discord import Discord
from website.extensions import cache, csrf, db, migrate, oauth, seed_trophies, setup_test_db
from website.scheduler import start_scheduler
from website.utils import get_app_version
from website.utils.logger import configure_logging
from website.views import register_blueprints, register_filters


def create_app():
    """Create and configure the Flask application.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)
    app.url_map.strict_slashes = False

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
            "permissions": session.get("permissions", []),
            "active_events": active_events,
        }
        return {"payload": payload}

    @app.context_processor
    def inject_guild_id():
        """Inject Discord guild ID into template context (DB override aware)."""
        from website.services import SettingsService

        return {"DISCORD_GUILD_ID": SettingsService().get("DISCORD_GUILD_ID")}

    @app.context_processor
    def inject_version():
        """Inject application version into template context."""
        return {"app_version": get_app_version()}

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)
    oauth.init_app(app)
    oauth.register(
        name="discord",
        authorize_url="https://discord.com/api/oauth2/authorize",
        access_token_url="https://discord.com/api/oauth2/token",
        api_base_url="https://discord.com/api/",
        client_kwargs={"scope": "identify"},
    )
    app.cli.add_command(seed_trophies)
    app.cli.add_command(setup_test_db)

    # Create bot instance and store it
    bot_instance = Discord(app.config["DISCORD_GUILD_ID"], app.config["DISCORD_BOT_TOKEN"])
    set_bot(bot_instance)

    register_blueprints(app)
    register_filters(app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Scheduled jobs
    with app.app_context():
        start_scheduler(app)

    return app
