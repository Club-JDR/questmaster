from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, expose
from flask import session
from wtforms.validators import NumberRange
from markupsafe import Markup
from wtforms import fields
from wtforms.widgets import html_params
from website.models import SpecialEvent
from website.extensions import db
from website.exceptions import UnauthorizedError


def is_admin_authenticated():
    return "user_id" in session and session.get("is_admin", False)


class SecureAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not is_admin_authenticated():
            raise UnauthorizedError(
                "Admin access required.", action="admin"
            )
        return super().index()


class AdminView(ModelView):
    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        raise UnauthorizedError("Admin access required.", action="admin")


class ChannelAdmin(AdminView):
    form_columns = ["id", "type", "size"]
    column_list = ["id", "type", "size"]
    column_editable_list = ["id", "type", "size"]
    can_create = True
    can_edit = True

    def is_accessible(self):
        return is_admin_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        raise UnauthorizedError("Admin access required.", action="admin")


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
        raise UnauthorizedError("Admin access required.", action="admin")


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
        raise UnauthorizedError("Admin access required.", action="admin")


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
        raise UnauthorizedError("Admin access required.", action="admin")


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
        "special_event",
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
        "special_event",
    ]

    can_create = False
    can_edit = True
    can_delete = True
    column_filters = ["id", "name", "gm_id", "type"]
    page_size = 10

    form_args = {
        "special_event": {
            "query_factory": lambda: db.session.query(SpecialEvent).order_by(
                SpecialEvent.name
            ),
            "label": "Special Event",
        }
    }


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


class ColorInputWidget:
    """Render a <input type='color'> element."""

    def __call__(self, field, **kwargs):
        kwargs.setdefault("type", "color")

        # Normalize DB value (int or string) into valid CSS hex (#RRGGBB)
        value = field.data
        if isinstance(value, int):
            value = f"#{value:06x}"
        elif isinstance(value, str):
            if not value.startswith("#"):
                # handle strings like 'FF6600' or '0xFF6600'
                value = value.replace("0x", "").replace("0X", "")
                value = f"#{value.zfill(6)}"
        else:
            value = "#000000"

        kwargs.setdefault("value", value)
        return Markup(f"<input {html_params(name=field.name, **kwargs)}>")


class ColorField(fields.StringField):
    widget = ColorInputWidget()


class SpecialEventAdmin(AdminView):
    can_view_details = True
    column_list = ["name", "color_preview", "emoji", "active"]

    form_overrides = {"color": ColorField}

    form_widget_args = {
        "color": {
            "style": "width: 80px; height: 40px; padding: 0; border: none; cursor: pointer;"
        }
    }

    def _color_preview(view, context, model, name):
        color_value = model.color

        if isinstance(color_value, int):
            color_hex = f"#{color_value:06x}"
        elif isinstance(color_value, str):
            color_value = color_value.strip()
            if color_value.startswith("#"):
                color_hex = color_value
            elif color_value.startswith("0x") or color_value.startswith("0X"):
                color_hex = f"#{int(color_value, 16):06x}"
            else:
                color_hex = f"#{color_value.zfill(6)}"
        else:
            color_hex = "#000000"

        return Markup(
            f'<div style="background-color: {color_hex}; '
            'width: 40px; height: 20px; border-radius: 4px; border: 1px solid #ccc;"></div>'
        )

    column_formatters = {
        "color_preview": _color_preview,
    }

    column_labels = {"color_preview": "Color"}

    def scaffold_list_columns(self):
        columns = super().scaffold_list_columns()
        if "color_preview" not in columns:
            columns.append("color_preview")
        return columns

    def on_model_change(self, form, model, is_created):
        color_str = form.color.data
        if isinstance(color_str, str) and color_str.startswith("#"):
            model.color = int(color_str.lstrip("#"), 16)
        elif isinstance(color_str, str) and (
            color_str.startswith("0x") or color_str.startswith("0X")
        ):
            model.color = int(color_str, 16)
        elif color_str is None or color_str == "":
            model.color = None
        else:
            model.color = int(color_str)
