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
from werkzeug.middleware.proxy_fix import ProxyFix


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

        payload = {
            "username": session.get("username"),
            "avatar": session.get("avatar"),
            "is_gm": session.get("is_gm"),
            "is_admin": session.get("is_admin"),
        }
        return {"payload": payload}

    @app.context_processor
    def inject_guild_id():
        return {"DISCORD_GUILD_ID": app.config["DISCORD_GUILD_ID"]}

    def get_app_version():
        version = os.environ.get("TAG")
        if not version:
            version = "dev"
        return version

    @app.context_processor
    def inject_version():
        return {"app_version": get_app_version()}

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)
    discord.init_app(app)
    app.cli.add_command(seed_trophies)

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
    admin.add_view(
        admin_view.ChannelAdmin(models.Channel, db.session, name="Catégories (salons)")
    )
    admin.add_view(
        admin_view.GameEventAdmin(models.GameEvent, db.session, name="Journaux")
    )

    register_blueprints(app)
    register_filters(app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    return app
