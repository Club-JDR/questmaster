"""Form-parsing utilities for extracting structured data from Flask request forms."""

from flask import request


def get_classification():
    """Parse classification fields from request.form.

    Returns:
        Dict mapping classification keys to integer scores.
        Keys come from form fields prefixed with 'class-'.
    """
    prefix = "class-"
    classification = {}
    for key in request.form:
        if key.startswith(prefix):
            clean_key = key[len(prefix) :]
            try:
                classification[clean_key] = int(request.form[key])
            except ValueError, TypeError:
                classification[clean_key] = 0
    return classification


def get_ambience(data):
    """Parse ambience checkboxes from form data dict.

    Args:
        data: Form data dict.

    Returns:
        List of selected ambience values.
    """
    return [a for a in ("chill", "serious", "comic", "epic") if data.get(a)]


def parse_restriction_tags(data):
    """Parse restriction tags from form data.

    Args:
        data: Form data dict containing optional 'restriction_tags' key.

    Returns:
        Stripped tag string, or None if absent.
    """
    raw = data.get("restriction_tags", "")
    return raw.strip() or None
