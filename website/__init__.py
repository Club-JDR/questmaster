"""QuestMaster application factory and configuration."""

import os
import sys
import uuid

from flask import Flask, g
from werkzeug.middleware.proxy_fix import ProxyFix

from config.settings import check_required_env_vars
from website.bot import set_bot
from website.cli import clear_cache, sync_discord_commands
from website.client.discord import Discord
from website.extensions import cache, csrf, db, migrate, oauth, seed_trophies, setup_test_db
from website.logging_config import configure_logging
from website.scheduler import start_scheduler
from website.utils import get_app_version
from website.views import register_blueprints, register_filters


def _is_one_off_cli_command() -> bool:
    """Whether this process is running a one-off ``flask`` CLI command.

    True for maintenance commands like ``flask db upgrade`` or
    ``flask seed-trophies`` (run once per deploy from ``entrypoint.sh``), so
    they never start a background scheduler of their own even if
    ``QM_RUN_SCHEDULER`` leaks into their environment. False for the
    long-running ``flask run`` dev server, so local development keeps working
    as before.

    Returns:
        True if the app was loaded for a one-off `flask` CLI command.
    """
    return os.environ.get("FLASK_RUN_FROM_CLI") == "true" and "run" not in sys.argv[1:]


def create_app():
    """Create and configure the Flask application.

    Returns:
        Configured Flask application instance.
    """
    # Fail fast on missing config instead of a confusing failure deep inside
    # Flask/SQLAlchemy later.
    check_required_env_vars()

    app = Flask(__name__)
    app.url_map.strict_slashes = False

    # Flask only autoescapes .html/.xml/.svg by default, never our .j2
    # templates. Must be set before the Jinja env is built.
    app.jinja_options = {"autoescape": True}

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
    app.cli.add_command(sync_discord_commands)
    app.cli.add_command(clear_cache)

    # Create bot instance and store it
    bot_instance = Discord(app.config["DISCORD_GUILD_ID"], app.config["DISCORD_BOT_TOKEN"])
    set_bot(bot_instance)

    register_blueprints(app)
    register_filters(app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Scheduled jobs — only the dedicated `scheduler` service (QM_RUN_SCHEDULER=1)
    # runs background jobs; the web workers never do, and one-off `flask` CLI
    # invocations (migrations, seeding) are skipped even if the flag leaks into
    # their environment.
    if app.config["RUN_SCHEDULER"] and not _is_one_off_cli_command():
        with app.app_context():
            start_scheduler(app)

    return app
