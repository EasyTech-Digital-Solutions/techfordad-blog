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
# A how-to guide, not a product review: it has its own top-of-page notes instead of the review disclosure box.
NOT_A_REVIEW = {"blog/how-to-set-up-ipad-for-elderly-parent.html"}
# A head-to-head comparison: its cards are labelled J1, J2, i1 (one letter per product line), not ranked 1..N.
LABELLED_CARDS = {"blog/jitterbug-vs-iphone-for-seniors.html"}


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
    assert 'class="disclaimer"' not in aside, "the disclosure lives in the strip under the hero, not in the sidebar"


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


def test_table_of_contents_numbering_is_continuous(html_page):
    """Once the contents list starts numbering (1., 2., ...) it numbers every later entry, in order, to the end."""
    t = _article(html_page)
    m = re.search(r'<ol class="toc-plain">(.*?)</ol>', t, re.S)
    if not m:
        pytest.skip("page has no numbered-style contents list")
    texts = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)]
    numbers = [re.match(r"(\d+)\.\s", x) for x in texts]
    first = next((i for i, n in enumerate(numbers) if n), None)
    assert first is not None, "contents list has no numbered entries"
    tail = numbers[first:]
    assert all(tail), f"entries after the first numbered one are not numbered: {[texts[first + i] for i, n in enumerate(tail) if not n]}"
    assert [int(n.group(1)) for n in tail] == list(range(1, len(tail) + 1)), f"numbering is not 1..{len(tail)} in order: {[int(n.group(1)) for n in tail]}"


def test_summary_then_products_then_comparison_table(html_page):
    """Reading order is the same on every article: 'Which one should you buy?', the product reviews, then the comparison table."""
    t = _article(html_page)
    if 'id="comparison"' not in t or 'class="product-card' not in t:
        pytest.skip("page has no comparison table or no product cards")
    first, last = t.find('<div class="product-card'), t.rfind('<div class="product-card')
    comparison = t.find('<h2 id="comparison"')
    assert comparison > last, "the comparison table must come AFTER the last product review (it sits before them on this page)"
    summary = [i for i in (t.find('<h2 id="top-picks"'), t.find('<h2 id="which-one"')) if i != -1]
    if summary:
        assert min(summary) < first, "the 'Which One Should You Buy?' summary must come before the first product review"
    assert t.count('id="comparison"') == 1 and t.count('id="top-picks"') <= 1, "duplicate section ids"


# ---------------------------------------------------------------- component-level parity (inside the template)

def _cards(t):
    """Each product card as text, from its opening tag to the next section heading."""
    out = []
    for m in re.finditer(r'<div class="product-card[^"]*">', t):
        end = t.find("<h2", m.end())
        out.append(t[m.start():end if end != -1 else len(t)])
    return out


def test_product_cards_use_the_shared_structure(html_page):
    """Rank number, title and badge on top; price/specs, Pros and Cons headings, and the buy button inside the card."""
    t = _article(html_page)
    cards = _cards(t)
    if not cards:
        pytest.skip("page has no product cards")
    for legacy in ('class="product-price"', 'class="product-badge"', 'class="product-pros-cons"'):
        assert legacy not in t, f"old card markup ({legacy}); use the shared card structure"
    ranks = []
    for n, card in enumerate(cards, 1):
        for needle in ('class="product-header"', 'class="product-rank', 'class="product-title"', "<h3>", 'class="product-badge-small"',
                       'class="product-body"', 'class="product-specs"', 'class="pros-cons"', "<h4>Pros</h4>", "<h4>Cons</h4>"):
            assert needle in card, f"card {n} is missing {needle}"
        label = re.search(r'class="product-rank(?: gold)?">([^<]+)<', card).group(1)
        ranks.append(label if html_page in LABELLED_CARDS else int(label))
    if html_page not in LABELLED_CARDS:
        assert ranks == list(range(1, len(cards) + 1)), f"card numbers are not 1..{len(cards)} in order: {ranks}"
        assert cards[0].startswith('<div class="product-card top-pick">'), "the first card is the highlighted top pick"
        for n, card in enumerate(cards[1:], 2):
            assert "top-pick" not in card.split(">", 1)[0], f"only the first card is the top pick (card {n})"
    for n, card in enumerate(cards, 1):
        if 'class="btn-check-price"' in card:
            body = card[card.index('class="product-body"'):]
            assert body.index('class="btn-check-price"') > body.index('class="pros-cons"'), f"card {n}: the buy button belongs after the pros and cons, inside the card"


def test_buy_button_is_inside_its_card(html_page):
    """A product's buy button sits in its card; none is left floating between a card and the next section."""
    t = _article(html_page)
    for n, m in enumerate(re.finditer(r'<div class="product-card[^"]*">', t), 1):
        end = t.find("<h2", m.end())
        seg = t[m.start():end if end != -1 else len(t)]
        card_close = seg.find('class="product-body"')
        if card_close == -1:
            continue
        after_card = seg[seg.rfind("</div>\n    </div>") + 6:] if "</div>\n    </div>" in seg else ""
        assert 'class="btn-check-price"' not in after_card, f"card {n}: buy button sits outside the card"


def test_comparison_table_uses_the_shared_markup(html_page):
    t = _article(html_page)
    if 'id="comparison"' not in t:
        pytest.skip("no comparison table")
    seg = t[t.index('id="comparison"'):]
    seg = seg[:seg.index("<h2", 20)] if "<h2" in seg[20:] else seg
    assert 'class="compare-table"' in seg and 'class="comparison-table' not in seg, "use <table class=\"compare-table\"> in a scrolling wrapper"
    assert '<div style="overflow-x:auto;">' in seg, "the table sits in the standard scrolling wrapper"


def test_disclosure_is_one_slim_strip_under_the_hero(html_page):
    t = _article(html_page)
    if html_page in NOT_A_REVIEW:
        pytest.skip("how-to guide, not a review")
    strip = re.search(r'<div class="article-disclaimer">\s*<strong>Affiliate Disclosure:</strong>(.*?)</div>', t, re.S)
    assert strip, "the affiliate disclosure strip under the hero is missing or uses non-standard markup"
    assert t.index("article-disclaimer") < t.index('<div class="article-layout">'), "the strip belongs between the hero and the two-column layout"
    text = strip.group(1)
    assert "may earn a commission" in text and "never influenced by compensation" in text and "approximate" in text
    assert t.count("<strong>Affiliate Disclosure:</strong>") == 1, "one disclosure strip; no second box in the article or sidebar"
    assert 'background:#fffbeb' not in t and 'class="affiliate-box"' not in t, "the old amber disclosure box is gone"


def test_hero_line_and_breadcrumb(html_page):
    t = _article(html_page)
    meta = re.search(r'<div class="article-meta">(.*?)</div>', t.replace("\n", " "), re.S)
    assert meta, "hero has no meta line"
    spans = re.findall(r"<span>(.*?)</span>", meta.group(1))
    assert spans[0] == "By TechForDad" and spans[1].startswith("Updated "), spans
    assert any(re.fullmatch(r"\d+ min read", s) for s in spans), f"hero line has no reading time: {spans}"
    crumb = re.search(r'<div class="breadcrumb-inner">(.*?)</div>', t, re.S).group(1)
    levels = crumb.count("<span>›</span>")
    assert levels in (1, 2), f"unexpected breadcrumb depth: {crumb}"
    if P.kind(html_page) == "article-ca":
        assert levels == 1, "Canada pages use the same 'Home › Page' trail as the USA pages"


def test_quick_tip_sits_before_the_summary(html_page):
    t = _article(html_page)
    if 'class="perk-line"' not in t:
        pytest.skip("no quick tip")
    marker = "<!-- buy-summary -->" if "<!-- buy-summary -->" in t else '<h2 id="top-picks"'
    assert t.index('class="perk-line"') < t.index(marker), "the quick tip comes before 'Which One Should You Buy?', as on the USA pages"


def test_contents_list_follows_page_order(html_page):
    """Entries in the table of contents appear in the same order as their sections on the page."""
    t = _article(html_page)
    m = re.search(r'<ol class="toc-plain">(.*?)</ol>', t, re.S)
    if not m:
        pytest.skip("page has no contents list of this style")
    ids = re.findall(r'<li><a href="#([^"]+)">', m.group(1))
    positions = [t.find(f'id="{i}"') for i in ids]
    assert all(p >= 0 for p in positions), "a contents entry points at a section that does not exist"
    assert positions == sorted(positions), f"contents list is out of page order: {[i for i, p in zip(ids, positions) if p != sorted(positions)[positions.index(p)]][:4]}"
