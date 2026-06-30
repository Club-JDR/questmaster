"""Unit tests for website.utils.discord_components (link-button helpers)."""

import pytest

from website.exceptions import ValidationError
from website.utils.discord_components import build_link_button_rows, clean_link_buttons


class TestCleanLinkButtons:
    def test_keeps_valid_buttons(self):
        buttons = clean_link_buttons([{"label": "Site", "url": "https://example.com"}])
        assert buttons == [{"label": "Site", "url": "https://example.com"}]

    def test_strips_whitespace(self):
        buttons = clean_link_buttons([{"label": "  Site  ", "url": " https://x.io "}])
        assert buttons == [{"label": "Site", "url": "https://x.io"}]

    def test_drops_fully_empty_rows(self):
        buttons = clean_link_buttons(
            [
                {"label": "", "url": ""},
                {"label": "Site", "url": "https://example.com"},
            ]
        )
        assert len(buttons) == 1

    def test_missing_url_raises(self):
        with pytest.raises(ValidationError):
            clean_link_buttons([{"label": "Site", "url": ""}])

    def test_missing_label_raises(self):
        with pytest.raises(ValidationError):
            clean_link_buttons([{"label": "", "url": "https://example.com"}])

    def test_non_http_url_raises(self):
        with pytest.raises(ValidationError):
            clean_link_buttons([{"label": "Bad", "url": "javascript:alert(1)"}])

    def test_too_long_label_raises(self):
        with pytest.raises(ValidationError):
            clean_link_buttons([{"label": "x" * 81, "url": "https://example.com"}])

    def test_too_many_buttons_raises(self):
        with pytest.raises(ValidationError):
            clean_link_buttons(
                [{"label": f"b{i}", "url": "https://example.com"} for i in range(6)]
            )


class TestBuildLinkButtonRows:
    def test_empty_returns_empty_list(self):
        assert build_link_button_rows([]) == []

    def test_builds_single_action_row(self):
        rows = build_link_button_rows(
            [
                {"label": "A", "url": "https://a.io"},
                {"label": "B", "url": "https://b.io"},
            ]
        )
        assert len(rows) == 1
        assert rows[0]["type"] == 1  # action row
        buttons = rows[0]["components"]
        assert [b["label"] for b in buttons] == ["A", "B"]
        assert all(b["type"] == 2 and b["style"] == 5 for b in buttons)
        assert buttons[0]["url"] == "https://a.io"
