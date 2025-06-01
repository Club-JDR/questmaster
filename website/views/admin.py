from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, expose
from flask_admin import helpers as admin_helpers
from flask import session, abort


def is_admin_authenticated():
    return "user_id" in session and session.get("is_admin", False)


class SecureAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not is_admin_authenticated():
            abort(403)
        return super().index()


class UserAdmin(ModelView):
    form_columns = ["id"]
    column_list = ["id"]
    column_editable_list = ["id"]
    can_create = True
    can_edit = False

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class ChannelAdmin(ModelView):
    form_columns = ["id", "type", "size"]
    column_list = ["id", "type", "size"]
    column_editable_list = ["id", "type", "size"]
    can_create = True
    can_edit = True

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class SystemAdmin(ModelView):
    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class GameSessionAdmin(ModelView):
    form_columns = ["game_id", "start", "end"]
    column_list = ["game_id", "start", "end"]
    column_editable_list = ["start", "end"]

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class VttAdmin(ModelView):
    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class GameAdmin(ModelView):
    column_list = [
        "name",
        "type",
        "length",
        "gm_id",
        "system_id",
        "vtt_id",
        "description",
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
    ]
    form_columns = column_list + ["players"]
    column_editable_list = [
        "name",
        "type",
        "length",
        "restriction",
        "party_size",
        "status",
    ]

    can_create = False
    can_edit = True
    can_delete = False
    column_searchable_list = ["gm_id", "type", "name"]
    column_filters = ["gm_id", "type"]
    page_size = 20

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class GameEventAdmin(ModelView):
    form_columns = ["game_id", "timestamp", "event_type", "description"]
    column_list = ["game_id", "timestamp", "event_type", "description"]
    column_searchable_list = ["game_id", "event_type"]
    column_filters = ["game_id", "event_type"]
    page_size = 20
    can_create = False
    can_edit = False

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)
