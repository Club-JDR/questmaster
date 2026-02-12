"""Global Discord bot instance management."""

_bot = None


def set_bot(bot_instance):
    """Set the global Discord bot instance.

    Args:
        bot_instance: Discord API client to store globally.
    """
    global _bot
    _bot = bot_instance


def get_bot():
    """Return the global Discord bot instance.

    Returns:
        The Discord API client, or None if not initialized.
    """
    return _bot
