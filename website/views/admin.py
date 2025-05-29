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
    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class GameEventAdmin(ModelView):
    form_columns = ["game_id", "timestamp", "event_type", "description"]
    column_list = ["game_id", "timestamp", "event_type", "description"]
    can_create = False
    can_edit = False

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        abort(403)
