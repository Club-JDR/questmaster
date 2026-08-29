"""Pagination helpers for the QuestMaster API."""

import math

from flask import jsonify, request

from config.constants import API_DEFAULT_PAGE, API_DEFAULT_PER_PAGE, API_MAX_PER_PAGE


def parse_pagination_args() -> tuple[int, int]:
    """Parse page and per_page from query string parameters.

    Returns:
        Tuple of (page, per_page) with validated, bounded values.
    """
    try:
        page = int(request.args.get("page", API_DEFAULT_PAGE))
    except TypeError, ValueError:
        page = API_DEFAULT_PAGE

    try:
        per_page = int(request.args.get("per_page", API_DEFAULT_PER_PAGE))
    except TypeError, ValueError:
        per_page = API_DEFAULT_PER_PAGE

    page = max(1, page)
    per_page = max(1, min(per_page, API_MAX_PER_PAGE))
    return page, per_page


def paginated_response(items: list, total: int, page: int, per_page: int):
    """Build a standard paginated JSON response.

    Args:
        items: Serialised items for the current page.
        total: Total number of items across all pages.
        page: Current page number (1-based).
        per_page: Number of items per page.

    Returns:
        Flask JSON response with pagination envelope.
    """
    pages = math.ceil(total / per_page) if per_page else 0
    return jsonify(
        {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }
    )
