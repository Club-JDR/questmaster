from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, expose
from flask import (
    session,
    abort,
    request,
    Blueprint,
    render_template,
    request,
    url_for,
    redirect,
    flash,
)
from wtforms.validators import NumberRange
from website.extensions import db
from website.utils.logger import logger
from website.views.auth import who, login_required
from website.views.games import SEARCH_GAMES_ROUTE

# from website.models import EventLog, User
# from website.models.game_event import EVENT_ACTIONS, EVENT_TARGET_TYPE

# admin_bp = Blueprint("admin_misc", __name__)


# @admin_bp.route("/admin/events")
# @login_required
# def admin_events():
#     payload = who()
#     if not payload["is_admin"]:
#         logger.warning(
#             f"Unauthorized access to events page by user: {payload.get('user_id', 'Unknown')}"
#         )
#         flash("Vous devez être Admin pour accéder à cette page.", "danger")
#         return redirect(url_for(SEARCH_GAMES_ROUTE))
#     page = request.args.get("page", 1, type=int)
#     per_page = 200

#     query = EventLog.query

#     user_id = request.args.get("user_id")
#     target_type = request.args.get("target_type")
#     target_id = request.args.get("target_id", type=int)
#     action = request.args.get("action")

#     if user_id:
#         query = query.filter_by(user_id=user_id)
#     if target_type:
#         query = query.filter_by(target_type=target_type)
#     if target_id:
#         query = query.filter_by(target_id=target_id)
#     if action:
#         query = query.filter_by(action=action)

#     query = query.order_by(EventLog.timestamp.desc())
#     pagination = query.paginate(page=page, per_page=per_page, error_out=False)

#     events = pagination.items
#     users = User.query.all()  # For dropdown filter
#     return render_template(
#         "event_log.j2",
#         events=events,
#         pagination=pagination,
#         users=users,
#         filters={
#             "user_id": user_id,
#             "target_type": target_type,
#             "target_id": target_id,
#             "action": action
#         },
#         event_actions=EVENT_ACTIONS,
#         target_types=EVENT_TARGET_TYPE,
#     )


def is_admin_authenticated():
    return "user_id" in session and session.get("is_admin", False)


class SecureAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not is_admin_authenticated():
            abort(403)
        return super().index()


class AdminView(ModelView):
    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class UserAdmin(AdminView):
    form_columns = ["id"]
    column_list = ["id", "name", "avatar"]
    column_editable_list = ["id"]
    can_create = True
    can_edit = False
    page_size = 50


class ChannelAdmin(AdminView):
    form_columns = ["id", "type", "size"]
    column_list = ["id", "type", "size"]
    column_editable_list = ["id", "type", "size"]
    can_create = True
    can_edit = True

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class VttAdmin(AdminView):
    form_columns = ["name", "icon"]
    column_list = ["id", "name", "icon"]
    column_editable_list = ["name", "icon"]
    column_searchable_list = [
        "id",
        "name",
    ]
    can_create = True
    can_edit = True

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class GameEventAdmin(AdminView):
    column_list = ["timestamp", "action", "game.slug", "description"]
    column_searchable_list = ["action", "game.slug", "description"]
    column_filters = ["action", "game.slug", "description"]
    column_labels = {
        "timestamp": "Timestamp (UTC)",
        "action": "Action",
        "game.slug": "Annonce",
        "description": "Détails",
    }
    page_size = 50
    can_create = False
    can_edit = False
    can_delete = False

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class SystemAdmin(AdminView):
    form_columns = ["name", "icon"]
    column_list = ["id", "name", "icon"]
    column_editable_list = ["name", "icon"]
    column_searchable_list = [
        "id",
        "name",
    ]
    can_create = True
    can_edit = True

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class GameSessionAdmin(AdminView):
    form_columns = ["game_id", "start", "end"]
    column_list = ["game_id", "start", "end"]
    column_editable_list = ["start", "end"]

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class GameAdmin(AdminView):
    column_list = [
        "id",
        "name",
        "slug",
        "type",
        "gm",
        "party_size",
        "party_selection",
        "date",
        "img",
        "channel",
        "role",
        "status",
    ]
    form_columns = [
        "id",
        "name",
        "slug",
        "type",
        "length",
        "gm",
        "system_id",
        "vtt_id",
        "restriction",
        "restriction_tags",
        "party_size",
        "party_selection",
        "xp",
        "date",
        "session_length",
        "frequency",
        "characters",
        "classification",
        "ambience",
        "complement",
        "img",
        "channel",
        "msg_id",
        "role",
        "status",
        "players",
    ]
    column_editable_list = [
        "name",
        "slug",
        "type",
        "gm",
        "party_size",
        "party_selection",
        "date",
        "status",
        "channel",
        "role",
        "img",
    ]

    can_create = False
    can_edit = True
    can_delete = False
    column_searchable_list = ["id", "gm_id", "type", "name"]
    column_filters = ["id", "gm_id", "type"]
    page_size = 10


class UserTrophyAdmin(AdminView):
    form_columns = ("user", "trophy", "quantity")

    column_list = ("user", "trophy", "quantity")
    column_searchable_list = ("user.id", "trophy.name")
    column_filters = ("user.id", "trophy.name")

    form_args = {
        "quantity": {
            "default": 1,
            "validators": [NumberRange(min=1)],
        }
    }

    def on_model_change(self, form, model, is_created):
        """
        Enforce trophy uniqueness if it's a unique trophy.
        """
        trophy = model.trophy
        if trophy.unique:
            existing = (
                self.session.query(self.model)
                .filter_by(user_id=model.user_id, trophy_id=model.trophy_id)
                .first()
            )

            if existing and (is_created or model != existing):
                raise form.ValidationError(
                    f"L'utilisateur possède déjà le trophée unique '{trophy.name}'."
                )

        if trophy.unique:
            model.quantity = 1
