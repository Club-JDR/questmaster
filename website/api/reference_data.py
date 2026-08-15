"""Read-only endpoints for reference data (systems, VTTs, special events).

Systems also expose a small write surface — declaring/withdrawing interest
in playing or running a system — reusing the same ``SystemService`` the
server-rendered system page calls.
"""

from flask import Blueprint, g, jsonify, request

from website.api.auth import api_login_required
from website.exceptions import UnauthorizedError
from website.services.special_event import SpecialEventService
from website.services.system import SystemService
from website.services.vtt import VttService

reference_data_bp = Blueprint("api_reference_data", __name__)

# Service instances
system_service = SystemService()
vtt_service = VttService()
special_event_service = SpecialEventService()


# ---------------------------------------------------------------------------
# Systems
# ---------------------------------------------------------------------------


@reference_data_bp.route("/systems/", methods=["GET"])
@api_login_required
def list_systems():
    """List all game systems.

    Returns:
        JSON array of system objects.
    """
    systems = system_service.get_all()
    return jsonify([s.to_dict() for s in systems])


@reference_data_bp.route("/systems/<int:id>/", methods=["GET"])
@api_login_required
def get_system(id):
    """Get a game system by ID.

    Args:
        id: System ID.

    Returns:
        JSON system object.

    Raises:
        NotFoundError: If system does not exist.
    """
    system = system_service.get_by_id(id)
    return jsonify(system.to_dict())


@reference_data_bp.route("/systems/<int:id>/run-history/", methods=["GET"])
@api_login_required
def get_system_run_history(id):
    """List GMs who have actually run this system, from game history.

    Args:
        id: System ID.

    Returns:
        JSON array of user objects.

    Raises:
        NotFoundError: If system does not exist.
    """
    users = system_service.get_run_history(id)
    return jsonify([u.to_dict() for u in users])


@reference_data_bp.route("/systems/<int:id>/interests/", methods=["GET"])
@api_login_required
def list_system_interests(id):
    """List users who declared interest in a system for a given role.

    Query parameters:
        role: "player" or "gm" (required).

    Returns:
        JSON array of user objects.

    Raises:
        NotFoundError: If system does not exist.
        ValidationError: If role is missing or unrecognized.
    """
    role = request.args.get("role", "")
    interests = system_service.get_interested(id, role)
    return jsonify([i.user.to_dict() for i in interests])


@reference_data_bp.route("/systems/<int:id>/interests/", methods=["POST"])
@api_login_required
def toggle_system_interest(id):
    """Add or remove the current user's declared interest in a system.

    Declaring GM interest requires the caller to be GM-flagged, mirroring
    the session-based gate used by the server-rendered system page.

    Request body:
        role: "player" or "gm" (required).
        note: Optional free text, used only when adding a new interest.

    Returns:
        JSON ``{"added": bool}``.

    Raises:
        NotFoundError: If system does not exist.
        ValidationError: If role is missing or unrecognized.
        UnauthorizedError: If declaring GM interest without GM access.
    """
    payload = request.get_json(silent=True) or {}
    role = payload.get("role", "")
    if role == "gm" and not g.current_user.get("is_gm", False):
        raise UnauthorizedError("GM access required.", action="gm")

    added = system_service.toggle_interest(
        id, g.current_user["sub"], role, note=payload.get("note") or None
    )
    return jsonify({"added": added})


# ---------------------------------------------------------------------------
# VTTs
# ---------------------------------------------------------------------------


@reference_data_bp.route("/vtts/", methods=["GET"])
@api_login_required
def list_vtts():
    """List all virtual tabletops.

    Returns:
        JSON array of VTT objects.
    """
    vtts = vtt_service.get_all()
    return jsonify([v.to_dict() for v in vtts])


@reference_data_bp.route("/vtts/<int:id>/", methods=["GET"])
@api_login_required
def get_vtt(id):
    """Get a VTT by ID.

    Args:
        id: VTT ID.

    Returns:
        JSON VTT object.

    Raises:
        NotFoundError: If VTT does not exist.
    """
    vtt = vtt_service.get_by_id(id)
    return jsonify(vtt.to_dict())


# ---------------------------------------------------------------------------
# Special Events
# ---------------------------------------------------------------------------


@reference_data_bp.route("/special-events/", methods=["GET"])
@api_login_required
def list_special_events():
    """List special events, optionally filtered by active status.

    Query parameters:
        active: If ``true``, only return active events.

    Returns:
        JSON array of special event objects.
    """
    active_only = request.args.get("active", "").lower() == "true"
    events = special_event_service.get_all(active_only=active_only)
    return jsonify([e.to_dict() for e in events])


@reference_data_bp.route("/special-events/<int:id>/", methods=["GET"])
@api_login_required
def get_special_event(id):
    """Get a special event by ID.

    Args:
        id: Special event ID.

    Returns:
        JSON special event object.

    Raises:
        NotFoundError: If special event does not exist.
    """
    event = special_event_service.get_by_id(id)
    return jsonify(event.to_dict())
