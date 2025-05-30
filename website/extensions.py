from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from flask_discord import DiscordOAuth2Session


db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
csrf = CSRFProtect()
discord = DiscordOAuth2Session()
