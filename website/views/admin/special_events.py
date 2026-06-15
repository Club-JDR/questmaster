"""Admin routes for managing special (themed) events."""

# Third-party imports
from flask import flash, redirect, render_template, request, url_for

# Local imports
from website.exceptions import NotFoundError, ValidationError
from website.services.special_event import SpecialEventService
from website.views.admin import admin_bp

special_event_service = SpecialEventService()


def _parse_color(raw: str | None) -> int | None:
    """Parse a hex color string (e.g. '#ff6600') into an integer.

    Args:
        raw: Raw color value from the form, or None.

    Returns:
        Integer color value, or None if no color was provided.
    """
    if not raw:
        return None
    return int(raw.lstrip("#"), 16)


@admin_bp.route("/special-events/", methods=["GET"])
def list_special_events():
    """List all special events."""
    events = special_event_service.get_all()
    return render_template("admin/special_events/list.html", events=events)


@admin_bp.route("/special-events/new", methods=["GET", "POST"])
def create_special_event():
    """Create a new special event."""
    if request.method == "POST":
        try:
            special_event_service.create(
                name=request.form.get("name", "").strip(),
                emoji=request.form.get("emoji", "").strip() or None,
                color=_parse_color(request.form.get("color")),
                active="active" in request.form,
            )
            flash("Événement créé.", "success")
            return redirect(url_for("admin.list_special_events"))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template("admin/special_events/form.html", event=None)


@admin_bp.route("/special-events/<int:event_id>/edit", methods=["GET", "POST"])
def edit_special_event(event_id):
    """Edit an existing special event."""
    try:
        event = special_event_service.get_by_id(event_id)
    except NotFoundError:
        flash("Événement introuvable.", "danger")
        return redirect(url_for("admin.list_special_events"))

    if request.method == "POST":
        try:
            special_event_service.update(
                event_id,
                {
                    "name": request.form.get("name", "").strip(),
                    "emoji": request.form.get("emoji", "").strip() or None,
                    "color": _parse_color(request.form.get("color")),
                    "active": "active" in request.form,
                },
            )
            flash("Événement mis à jour.", "success")
            return redirect(url_for("admin.list_special_events"))
        except ValidationError as e:
            flash(str(e), "danger")

    return render_template("admin/special_events/form.html", event=event)


@admin_bp.route("/special-events/<int:event_id>/delete", methods=["POST"])
def delete_special_event(event_id):
    """Delete a special event."""
    special_event_service.delete(event_id)
    flash("Événement supprimé.", "success")
    return redirect(url_for("admin.list_special_events"))
