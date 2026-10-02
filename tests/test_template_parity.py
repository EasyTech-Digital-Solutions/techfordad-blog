"""USA and Canada articles share ONE template: two columns, the same sidebar boxes, author box, newsletter and FAQ.

Canada pages used to be a different, simpler template (no sidebar, four different FAQ styles). These tests keep every
article on the same one, so a visitor on techfordad.com sees the same site whichever country they are reading.
"""
import re

import pytest

import pages as P

ARTICLE_KINDS = {"article-us", "article-ca"}
# USA pages whose sidebar is deliberately different (a "Quick Guide" box instead of "Our Top Picks"). Canada has none.
SIDEBAR_EXCEPTIONS = {"blog/medical-alert-no-monthly-fee.html"}


def _article(html_page):
    if P.kind(html_page) not in ARTICLE_KINDS:
        pytest.skip("not a USA/Canada article")
    return P.read(html_page)


def test_article_has_the_full_template(html_page):
    t = _article(html_page)
    for needle, what in [('<div class="article-layout">', "two-column layout"), ('<article class="article-body">', "article column"),
                         ('<aside class="article-sidebar">', "right-hand sidebar"), ('class="toc"', "table of contents"),
                         ('class="author-box"', "author box"), ('class="newsletter"', "free-checklist signup")]:
        assert needle in t, f"missing the {what} ({needle})"
    assert t.index("</article>") < t.index('<aside class="article-sidebar">') < t.index('class="author-box"') < t.index('class="newsletter"') < t.index("</main>")


def test_sidebar_has_the_standard_boxes(html_page):
    t = _article(html_page)
    aside = t[t.index('<aside class="article-sidebar">'):t.index("</aside>", t.index('<aside class="article-sidebar">'))]
    boxes = re.findall(r'<div class="sidebar-box">\s*<h3>(.*?)</h3>', aside, re.S)
    assert "Related Guides" in boxes, f"sidebar has no 'Related Guides' box (boxes: {boxes})"
    if 'class="buy-decision"' in t and html_page not in SIDEBAR_EXCEPTIONS:
        assert "Our Top Picks" in boxes, "the page has a ranked pick list but the sidebar has no 'Our Top Picks' box"
    assert 'class="disclaimer"' in aside and "Affiliate Disclosure" in aside, "sidebar is missing the affiliate note"


def test_top_picks_sidebar_matches_the_pick_list(html_page):
    """'Our Top Picks' lists the same products, in the same order, linking to the same sections as 'Which one should you buy?'."""
    t = _article(html_page)
    lst = re.search(r'<ul class="buy-decision">(.*?)</ul>', t, re.S)
    aside = t[t.index('<aside class="article-sidebar">'):t.index("</aside>", t.index('<aside class="article-sidebar">'))]
    box = re.search(r'<h3>Our Top Picks</h3>(.*?)(?=<div class="sidebar-box">|<p class="disclaimer"|$)', aside, re.S)
    if not (lst and box):
        pytest.skip("no pick list or no Top Picks box")
    wanted = re.findall(r'<li>(.*?)</li>', lst.group(1), re.S)
    entries = box.group(1).count('class="quick-pick"')
    assert 1 <= entries <= len(wanted), f"sidebar lists {entries} picks but the pick list has {len(wanted)}"
    if P.kind(html_page) == "article-ca":  # generated: all picks, links must match exactly (USA pages may show only their top few, or link straight to Amazon, on purpose)
        assert entries == len(wanted), f"sidebar lists {entries} picks but the pick list has {len(wanted)}"
        anchors = re.findall(r'<a href="#([^"]+)">', lst.group(1))
        assert re.findall(r'<a href="#([^"]+)"', box.group(1)) == anchors, "sidebar picks link to different sections than the pick list"


def test_faq_uses_the_click_to_open_markup(html_page):
    t = _article(html_page)
    if 'id="faq"' not in t:
        pytest.skip("no FAQ section on this page")
    items = re.findall(r'<div class="faq-item">(.*?)</div>\s*(?=<div class="faq-item">|\n\s*<(?:aside|!--|section|h2|/article))', t, re.S)
    assert t.count('class="faq-item"') >= 3, "FAQ section should have at least 3 questions"
    assert t.count('class="faq-q"') == t.count('class="faq-item"') == t.count('class="faq-a"'), "every FAQ item needs a .faq-q and a .faq-a"
    assert "<details" not in t, "FAQs use the shared click-to-open markup (div.faq-q), not <details>"
    faq_part = t[t.index('id="faq"'):]
    faq_part = faq_part[:faq_part.index("</article>")]
    assert not re.search(r"<h3>", faq_part.split('class="faq-item"')[0].split("</h2>", 1)[1]), "bare <h3> questions sit above the FAQ items"
