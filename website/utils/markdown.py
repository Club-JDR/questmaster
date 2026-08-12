"""Markdown rendering for user-authored game text (description, complement).

Markdown source is the only thing ever persisted; rendering to sanitized HTML
happens on read, here.
"""

import nh3
from markdown_it import MarkdownIt
from markupsafe import Markup

# Raw HTML is disabled (any literal HTML in the source is escaped by
# markdown-it, not passed through); linkify turns bare URLs into links;
# breaks turns a single newline into <br>, matching the previous
# `whitespace-pre-line` + `urlize` line-break behaviour.
_md = MarkdownIt("commonmark", {"html": False, "linkify": True, "breaks": True}).enable("linkify")

# Kept deliberately small: enough for prose formatting, no images (games
# already have a dedicated `img` field) and no raw HTML passthrough.
_ALLOWED_TAGS = {
    "p",
    "br",
    "strong",
    "em",
    "a",
    "ul",
    "ol",
    "li",
    "blockquote",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "del",
}
_ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}
_ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}
_LINK_REL = "noopener noreferrer nofollow ugc"


def render_markdown(text: str | None) -> Markup:
    """Render Markdown source to sanitized, safe-to-embed HTML.

    Args:
        text: Markdown source text, or None/empty.

    Returns:
        A ``Markup`` instance wrapping HTML that has been through
        markdown-it-py (raw HTML disabled) and then nh3 (tags/attributes/URL
        schemes allowlisted), safe to render unescaped in Jinja.
    """
    if not text:
        return Markup("")

    html = _md.render(text)
    clean = nh3.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes=_ALLOWED_URL_SCHEMES,
        link_rel=_LINK_REL,
    )
    return Markup(clean)
