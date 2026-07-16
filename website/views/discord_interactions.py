"""Discord HTTP-interactions endpoint (slash-command webhook receiver).

Discord signs each interaction with the application's Ed25519 key and POSTs
it here. The signature is the authentication: no OAuth, JWT, or session is
involved. Read-only commands answer inline; mutating commands return a
deferred ack and follow up from a background thread.
"""

from flask import Blueprint, current_app, jsonify, request

from website.extensions import csrf
from website.services.discord_command import DiscordCommandService

discord_bp = Blueprint("discord_interactions", __name__)

# Discord interaction request/response type enums
PING = 1
APPLICATION_COMMAND = 2
PONG = 1
CHANNEL_MESSAGE = 4
DEFERRED_CHANNEL_MESSAGE = 5
EPHEMERAL = 64

command_service = DiscordCommandService()


def _verify_signature() -> bool:
    """Verify the Ed25519 signature of the raw request body.

    Verification runs on ``request.data`` (the exact raw bytes) before any
    JSON parsing — re-serializing the parsed body would break it.

    Returns:
        True if the signature matches the configured DISCORD_PUBLIC_KEY.
    """
    from nacl.exceptions import BadSignatureError
    from nacl.signing import VerifyKey

    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")
    public_key = current_app.config.get("DISCORD_PUBLIC_KEY")
    if not (signature and timestamp and public_key):
        return False
    try:
        VerifyKey(bytes.fromhex(public_key)).verify(
            timestamp.encode() + request.data, bytes.fromhex(signature)
        )
        return True
    except (BadSignatureError, ValueError):
        return False


@discord_bp.route("/discord/interactions", methods=["POST"])
@csrf.exempt
def interactions():
    """Receive and dispatch a Discord interaction.

    Returns:
        JSON interaction response: PONG for the handshake, an inline message
        for read-only commands, or a deferred ephemeral ack for mutating ones.
    """
    if not _verify_signature():
        return "invalid request signature", 401

    payload = request.get_json(silent=True) or {}
    interaction_type = payload.get("type")

    if interaction_type == PING:
        return jsonify({"type": PONG})

    if interaction_type == APPLICATION_COMMAND:
        if command_service.is_inline(payload):
            content = command_service.handle_inline(payload)
            return jsonify(
                {"type": CHANNEL_MESSAGE, "data": {"content": content, "flags": EPHEMERAL}}
            )
        command_service.dispatch_async(current_app._get_current_object(), payload)
        return jsonify({"type": DEFERRED_CHANNEL_MESSAGE, "data": {"flags": EPHEMERAL}})

    return jsonify({"type": PONG})
