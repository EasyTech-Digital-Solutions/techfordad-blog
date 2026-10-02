"""Page inventory: every HTML file in the repo, and what kind of page it is.

The tests are driven from this list, so a new kind of page has to be added here on purpose
(test_inventory.py fails on any page that matches no rule). That is the point: when you add a page
type, you also decide which checks apply to it.

Kinds
    home         index.html
    hub          blog/index.html, gift-guides/index.html, guides/index.html
    article-us   blog/*.html (USD, amazon.com)
    article-ca   blog/*-canada.html (CAD, amazon.ca, lang="en-CA")
    gift-guide   gift-guides/*.html
    guide        guides/*.html
    info         about, contact, privacy, affiliate disclosure, our story, how we review
    error        404.html
    stub         a "page moved" redirect (meta refresh); old WordPress-era URLs and renamed pages
    admin        admin/index.html (a local tool, never published; see admin/README.md)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Folders that hold no website pages (tools, docs, tests, dependencies).
SKIP_DIRS = {".git", ".venv", "node_modules", "tests", "docs", "scripts", "__pycache__", ".github", ".pytest_cache"}

INFO_PAGES = {
    "about.html", "contact.html", "privacy-policy.html", "affiliate-disclosure.html",
    "our-story.html", "how-we-review.html",
}
HUB_PAGES = {"blog/index.html", "gift-guides/index.html", "guides/index.html"}

# Affiliate tracking IDs by page type. A page may only use the ID for its own kind.
AMAZON_TAGS = {
    "article-us": {"techfordad0b-20"},
    "gift-guide": {"techfordad-gifts-20"},
    "article-ca": {"abhikar91-20"},
}
ALL_TAGS = set().union(*AMAZON_TAGS.values())

# Kinds that are real, rendered content pages (everything the browser tests visit).
CONTENT_KINDS = {"home", "hub", "article-us", "article-ca", "gift-guide", "guide", "info", "error"}
# Kinds that carry the print/share toolbar (see js/main.js: /blog|gift-guides|guides/*.html, not index).
TOOLBAR_KINDS = {"article-us", "article-ca", "gift-guide", "guide"}


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def all_html() -> list[str]:
    out = []
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS:
            continue
        out.append(rel.as_posix())
    return out


def kind(rel: str) -> str | None:
    """Return the page's kind, or None if no rule matches (the inventory test then fails)."""
    if rel == "admin/index.html":
        return "admin"
    if 'http-equiv="refresh"' in read(rel):
        return "stub"
    if rel == "404.html":
        return "error"
    if rel == "index.html":
        return "home"
    if rel in INFO_PAGES:
        return "info"
    if rel in HUB_PAGES:
        return "hub"
    if rel.startswith("blog/"):
        return "article-ca" if rel.endswith("-canada.html") else "article-us"
    if rel.startswith("gift-guides/"):
        return "gift-guide"
    if rel.startswith("guides/"):
        return "guide"
    return None


def inventory() -> dict[str, str | None]:
    return {rel: kind(rel) for rel in all_html()}


def has_toolbar(rel: str) -> bool:
    return kind(rel) in TOOLBAR_KINDS


def is_noindex(rel: str) -> bool:
    text = read(rel).lower()
    return 'name="robots"' in text and "noindex" in text.split('name="robots"', 1)[1][:80]


def public_url(rel: str) -> str:
    return "https://www.techfordad.com/" + ("" if rel == "index.html" else rel)
