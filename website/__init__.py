import os, uuid
from flask import Flask, g
from flask_admin import Admin
from website.utils.discord import Discord
from website.utils.logger import configure_logging
from website import models
from website.bot import set_bot
from website.views import admin as admin_view
from website.extensions import db, migrate, csrf, cache, discord, seed_trophies
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
        base_template="admin.j2",
        index_view=admin_view.SecureAdminIndexView(),
    )
    admin.add_view(admin_view.GameAdmin(models.Game, db.session))
    admin.add_view(admin_view.GameSessionAdmin(models.GameSession, db.session))
    admin.add_view(admin_view.ChannelAdmin(models.Channel, db.session))
    admin.add_view(admin_view.UserAdmin(models.User, db.session))
    admin.add_view(admin_view.AdminView(models.Trophy, db.session))
    admin.add_view(admin_view.UserTrophyAdmin(models.UserTrophy, db.session))
    admin.add_view(admin_view.AdminView(models.Vtt, db.session))
    admin.add_view(admin_view.AdminView(models.System, db.session))

    register_blueprints(app)
    register_filters(app)

    with app.app_context():
        db.create_all()
        seed_trophies()

    return app
