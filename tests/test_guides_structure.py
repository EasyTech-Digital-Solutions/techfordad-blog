"""Guides and gift guides follow the same lean layout as the reviews (docs/page-structure.md)."""
import re

import pytest

import pages as P

GUIDES = sorted(p.relative_to(P.ROOT).as_posix() for p in (P.ROOT / "guides").glob("*.html")
                if p.name != "index.html" and 'http-equiv="refresh"' not in p.read_text(encoding="utf-8"))
GIFT_GUIDES = sorted(p.relative_to(P.ROOT).as_posix() for p in (P.ROOT / "gift-guides").glob("*.html"))


def _foot_in_order(t):
    marks = [m for m in ("class=\"newsletter\"", 'class="author-box', "</main>") if m in t]
    pos = [t.index(m) for m in marks]
    assert pos == sorted(pos), f"the foot of the page is out of order: {marks}"


@pytest.mark.parametrize("rel", GUIDES)
def test_guide_follows_the_layout(rel):
    t = P.read(rel)
    assert t.count('class="article-disclaimer"') == 1, "one disclosure strip under the hero"
    assert 'class="affiliate-box"' not in t and 'class="disclaimer"' not in t, "no second disclosure box"
    m = re.search(r'<!-- guide-toc -->.*?<p class="toc-title">Table of Contents</p>(.*?)<!-- /guide-toc -->', t, re.S)
    assert m, "the guide has no table of contents (scripts/build_guide_toc.py writes it)"
    ids = re.findall(r'href="#([^"]+)"', m.group(1))
    assert len(ids) >= 3 and all(f'id="{i}"' in t for i in ids), "every contents entry points at a section that exists"
    assert t.index("<!-- guide-toc -->") < t.index("<h2", t.index("<!-- /guide-toc -->")), "the contents list comes before the first section"
    assert 'class="author-box' in t and "affiliate-disclosure" not in t[t.index('class="author-box'):t.index('class="author-box') + 900], \
        "the author strip does not repeat the disclosure"
    _foot_in_order(t)


@pytest.mark.parametrize("rel", GIFT_GUIDES)
def test_gift_guide_follows_the_layout(rel):
    t = P.read(rel)
    assert t.count('class="article-disclaimer"') == 1, "one disclosure strip under the hero"
    assert "As an Amazon Associate I earn from qualifying purchases" in t[:t.index("</main>")] and 'class="affiliate-box"' not in t, \
        "the Amazon Associate statement lives in the strip, with no second box"
    if "toc-box" in t:
        assert "<strong>Table of Contents</strong>" in t, "the contents box is titled Table of Contents"
    assert 'class="newsletter"' in t and 'class="author-box' in t, "newsletter and author strip close the page"
    _foot_in_order(t)
    if "faq" in t and "related" in t:
        assert t.index('id="faq"') < t.index('id="related"'), "FAQ comes before the related reviews"
