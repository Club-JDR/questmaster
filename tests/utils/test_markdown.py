"""Unit tests for website.utils.markdown module."""

from markupsafe import Markup

from website.utils.markdown import render_markdown


class TestRenderMarkdownFormatting:
    def test_empty_and_none_render_to_empty_markup(self):
        assert render_markdown(None) == ""
        assert render_markdown("") == ""
        assert isinstance(render_markdown(None), Markup)

    def test_bold_and_italic(self):
        html = render_markdown("**bold** and *italic*")
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_single_newline_becomes_br(self):
        html = render_markdown("Line one\nLine two")
        assert "<br" in html
        assert "<p>Line one<br" in html

    def test_paragraph_break_on_blank_line(self):
        html = render_markdown("Para one\n\nPara two")
        assert html.count("<p>") == 2

    def test_list_rendering(self):
        html = render_markdown("- item1\n- item2")
        assert "<ul>" in html
        assert html.count("<li>") == 2

    def test_heading_rendering(self):
        html = render_markdown("# Title")
        assert "<h1>Title</h1>" in html

    def test_blockquote_rendering(self):
        html = render_markdown("> a quote")
        assert "<blockquote>" in html

    def test_link_rendering_with_safe_rel(self):
        html = render_markdown("[club](https://example.com)")
        assert 'href="https://example.com"' in html
        assert "noopener" in html
        assert "noreferrer" in html

    def test_autolink_bare_url(self):
        html = render_markdown("Check https://example.com out")
        assert '<a href="https://example.com"' in html

    def test_result_is_markup_safe_for_jinja(self):
        html = render_markdown("<not-escaped-twice>")
        # Markup instances are not re-escaped by Jinja's |safe/autoescape.
        assert isinstance(html, Markup)


class TestRenderMarkdownXSS:
    def test_script_tag_is_neutralized(self):
        html = render_markdown("<script>alert(1)</script>")
        assert "<script" not in html
        assert "alert(1)" not in html or "&lt;script&gt;" in html

    def test_img_onerror_is_stripped(self):
        # Raw HTML is disabled at the markdown-it level, so the whole tag is
        # rendered as inert escaped text (`&lt;img ...&gt;`), not a live tag.
        html = render_markdown('<img src=x onerror="alert(1)">')
        assert "<img" not in html
        assert "&lt;img" in html

    def test_javascript_scheme_link_is_neutralized(self):
        html = render_markdown("[click me](javascript:alert(1))")
        assert 'href="javascript' not in html

    def test_data_scheme_link_is_neutralized(self):
        html = render_markdown("[click me](data:text/html,<script>alert(1)</script>)")
        assert 'href="data' not in html

    def test_inline_html_event_handler_is_escaped(self):
        html = render_markdown('<div onclick="alert(1)">hi</div>')
        assert "<div" not in html
        assert "&lt;div" in html

    def test_raw_iframe_is_stripped(self):
        html = render_markdown('<iframe src="https://evil.example"></iframe>')
        assert "<iframe" not in html

    def test_markdown_image_syntax_is_stripped(self):
        # Images are intentionally not part of the allowed tag set: games
        # already have a dedicated `img` field for their cover image.
        html = render_markdown("![alt](https://evil.example/x.png)")
        assert "<img" not in html

    def test_style_attribute_is_stripped_from_links(self):
        html = render_markdown('[link](https://example.com "title")')
        assert "style=" not in html
