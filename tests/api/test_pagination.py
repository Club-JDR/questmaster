"""Tests for pagination utilities."""

import pytest

from config.constants import API_DEFAULT_PAGE, API_DEFAULT_PER_PAGE, API_MAX_PER_PAGE
from website.api.pagination import paginated_response, parse_pagination_args


class TestParsePaginationArgs:
    """Tests for parse_pagination_args."""

    def test_defaults(self, test_app):
        """Uses default values when no query params provided."""
        with test_app.test_request_context("/api/v1/games"):
            page, per_page = parse_pagination_args()
            assert page == API_DEFAULT_PAGE
            assert per_page == API_DEFAULT_PER_PAGE

    def test_custom_values(self, test_app):
        """Parses custom page and per_page from query string."""
        with test_app.test_request_context("/api/v1/games?page=3&per_page=50"):
            page, per_page = parse_pagination_args()
            assert page == 3
            assert per_page == 50

    def test_page_minimum_is_one(self, test_app):
        """Page is clamped to a minimum of 1."""
        with test_app.test_request_context("/api/v1/games?page=0"):
            page, _ = parse_pagination_args()
            assert page == 1

    def test_negative_page(self, test_app):
        """Negative page is clamped to 1."""
        with test_app.test_request_context("/api/v1/games?page=-5"):
            page, _ = parse_pagination_args()
            assert page == 1

    def test_per_page_capped_at_max(self, test_app):
        """per_page is capped at API_MAX_PER_PAGE."""
        with test_app.test_request_context("/api/v1/games?per_page=999"):
            _, per_page = parse_pagination_args()
            assert per_page == API_MAX_PER_PAGE

    def test_per_page_minimum_is_one(self, test_app):
        """per_page is clamped to a minimum of 1."""
        with test_app.test_request_context("/api/v1/games?per_page=0"):
            _, per_page = parse_pagination_args()
            assert per_page == 1

    def test_invalid_page_falls_back_to_default(self, test_app):
        """Non-integer page falls back to default."""
        with test_app.test_request_context("/api/v1/games?page=abc"):
            page, _ = parse_pagination_args()
            assert page == API_DEFAULT_PAGE

    def test_invalid_per_page_falls_back_to_default(self, test_app):
        """Non-integer per_page falls back to default."""
        with test_app.test_request_context("/api/v1/games?per_page=xyz"):
            _, per_page = parse_pagination_args()
            assert per_page == API_DEFAULT_PER_PAGE


class TestPaginatedResponse:
    """Tests for paginated_response."""

    def test_envelope_structure(self, test_app):
        """Response contains all pagination envelope fields."""
        with test_app.test_request_context():
            resp = paginated_response(items=["a", "b"], total=10, page=1, per_page=2)
            data = resp.get_json()
            assert data["items"] == ["a", "b"]
            assert data["total"] == 10
            assert data["page"] == 1
            assert data["per_page"] == 2
            assert data["pages"] == 5

    def test_pages_calculation(self, test_app):
        """Pages is ceil(total / per_page)."""
        with test_app.test_request_context():
            resp = paginated_response(items=[], total=11, page=1, per_page=5)
            data = resp.get_json()
            assert data["pages"] == 3

    def test_empty_result(self, test_app):
        """Empty items with total 0 returns 0 pages."""
        with test_app.test_request_context():
            resp = paginated_response(items=[], total=0, page=1, per_page=20)
            data = resp.get_json()
            assert data["items"] == []
            assert data["total"] == 0
            assert data["pages"] == 0
