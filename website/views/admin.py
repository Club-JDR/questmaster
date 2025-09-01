from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, expose
from flask import (
    session,
    abort,
)
from wtforms.validators import NumberRange


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
    can_delete = True
    column_filters = ["id", "name", "gm_id", "type"]
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
