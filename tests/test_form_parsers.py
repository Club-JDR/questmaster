"""Unit tests for website.utils.form_parsers module.

Tests the form-parsing utilities that extract structured data from Flask
request forms (classification, ambience, restriction tags).
"""

import pytest
from flask import Flask
from werkzeug.datastructures import MultiDict

from website.utils.form_parsers import (
    get_ambience,
    get_classification,
    parse_restriction_tags,
)


@pytest.fixture
def parser_app():
    """Minimal Flask app for request-context-dependent parsers."""
    return Flask(__name__)


# ---------------------------------------------------------------------------
# get_classification
# ---------------------------------------------------------------------------


class TestGetClassification:
    def test_extracts_class_prefixed_fields(self, parser_app):
        data = MultiDict({"class-action": "2", "class-horror": "1", "other-field": "x"})
        with parser_app.test_request_context("/", data=data, method="POST"):
            result = get_classification()
        assert result == {"action": 2, "horror": 1}

    def test_empty_form(self, parser_app):
        with parser_app.test_request_context("/", data={}, method="POST"):
            result = get_classification()
        assert result == {}

    def test_no_class_prefixed_fields(self, parser_app):
        data = MultiDict({"name": "test", "value": "42"})
        with parser_app.test_request_context("/", data=data, method="POST"):
            result = get_classification()
        assert result == {}

    def test_invalid_value_defaults_to_zero(self, parser_app):
        data = MultiDict({"class-action": "not_a_number", "class-horror": "2"})
        with parser_app.test_request_context("/", data=data, method="POST"):
            result = get_classification()
        assert result["action"] == 0
        assert result["horror"] == 2

    def test_all_classification_keys(self, parser_app):
        data = MultiDict(
            {
                "class-action": "1",
                "class-investigation": "2",
                "class-interaction": "0",
                "class-horror": "1",
            }
        )
        with parser_app.test_request_context("/", data=data, method="POST"):
            result = get_classification()
        assert result == {
            "action": 1,
            "investigation": 2,
            "interaction": 0,
            "horror": 1,
        }


# ---------------------------------------------------------------------------
# get_ambience
# ---------------------------------------------------------------------------


class TestGetAmbience:
    def test_all_selected(self):
        data = {"chill": "on", "serious": "on", "comic": "on", "epic": "on"}
        assert get_ambience(data) == ["chill", "serious", "comic", "epic"]

    def test_none_selected(self):
        assert get_ambience({}) == []

    def test_partial_selection(self):
        assert get_ambience({"chill": "on", "epic": "on"}) == ["chill", "epic"]

    def test_falsy_values_excluded(self):
        data = {"chill": "", "serious": None, "comic": "on", "epic": False}
        assert get_ambience(data) == ["comic"]

    def test_preserves_order(self):
        assert get_ambience({"epic": "on", "chill": "on"}) == ["chill", "epic"]

    def test_extra_keys_ignored(self):
        data = {"chill": "on", "unknown": "on", "serious": "on"}
        assert get_ambience(data) == ["chill", "serious"]


# ---------------------------------------------------------------------------
# parse_restriction_tags
# ---------------------------------------------------------------------------


class TestParseRestrictionTags:
    def test_valid_yaml_tags(self):
        raw = '[{"value": "violence"}, {"value": "horreur"}]'
        assert parse_restriction_tags({"restriction_tags": raw}) == "violence, horreur"

    def test_single_tag(self):
        raw = '[{"value": "gore"}]'
        assert parse_restriction_tags({"restriction_tags": raw}) == "gore"

    def test_empty_string(self):
        assert parse_restriction_tags({"restriction_tags": ""}) is None

    def test_missing_key(self):
        assert parse_restriction_tags({}) is None

    def test_malformed_yaml_returns_none(self, parser_app):
        with parser_app.test_request_context("/"):
            result = parse_restriction_tags({"restriction_tags": "[{invalid yaml"})
        assert result is None

    def test_invalid_structure_returns_none(self, parser_app):
        with parser_app.test_request_context("/"):
            result = parse_restriction_tags({"restriction_tags": "just a string"})
        assert result is None
