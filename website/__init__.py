import os, uuid
from flask import Flask, g
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from website.utils.discord import Discord
from website.utils.logger import RequestLoggerAdapter, configure_logging
from website.models import Channel, Game, GameSession, System, Vtt, User, GameEvent
from website.bot import set_bot
from website.views import admin as admin_view
from website.extensions import db, migrate, csrf, cache, discord
from website.views import register_blueprints, register_filters


def create_app():
    app = Flask(__name__)

    # Config
    app.secret_key = os.environ.get("FLASK_AUTH_SECRET")
    app.config.from_object("config.Config")

    # Logging
    configure_logging()

    @app.before_request
    def assign_trace_id():
        g.trace_id = str(uuid.uuid4())

    @app.after_request
    def add_trace_id_to_response(response):
        response.headers["X-Trace-ID"] = g.trace_id
        return response

    @app.context_processor
    def inject_payload():
        from flask import session

        # Build your payload however you normally do
        payload = {
            "username": session.get("username"),
            "avatar": session.get("avatar"),
            "is_gm": session.get("is_gm"),
            "is_admin": session.get("is_admin"),
            # Add more as needed
        }
        return dict(payload=payload)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)
    discord.init_app(app)

    # Create bot instance and store it
    bot_instance = Discord(
        app.config["DISCORD_GUILD_ID"], app.config["DISCORD_BOT_TOKEN"]
    )
    set_bot(bot_instance)

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"  # Dev only

    # Admin
    app.config["FLASK_ADMIN_SWATCH"] = "cosmo"
    admin = Admin(
        app,
        name="QuestMaster Admin",
        template_mode="bootstrap4",
        index_view=admin_view.SecureAdminIndexView(),
    )
    admin.add_view(admin_view.GameAdmin(Game, db.session))
    admin.add_view(admin_view.GameEventAdmin(GameEvent, db.session))
    admin.add_view(admin_view.GameSessionAdmin(GameSession, db.session))
    admin.add_view(admin_view.ChannelAdmin(Channel, db.session))
    admin.add_view(admin_view.UserAdmin(User, db.session))
    admin.add_view(admin_view.VttAdmin(Vtt, db.session))
    admin.add_view(admin_view.SystemAdmin(System, db.session))

    register_blueprints(app)
    register_filters(app)
    return app
