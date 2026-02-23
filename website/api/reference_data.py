"""Read-only endpoints for reference data (systems, VTTs, special events)."""

from flask import Blueprint, jsonify, request

from website.api.auth import api_login_required
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
