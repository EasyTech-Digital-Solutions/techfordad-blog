"""Manual AdSense slots (scripts/build_ads.py): off until an id is set, then only in reader-safe places, idempotent, one client id."""
import json
import re
import sys

import pytest

import pages as P

sys.path.insert(0, str(P.ROOT / "scripts"))
import build_ads as A  # noqa: E402
import build_buying_summary as B  # noqa: E402

DUMMY = {"client": "ca-pub-6309879983967574", "slots": {"in_article": "1111111111", "after_table": "2222222222", "sidebar": "3333333333"}}
REVIEWS = sorted(B.PAGES)


@pytest.fixture
def with_ids(monkeypatch):
    monkeypatch.setattr(A, "config", lambda: DUMMY)


def _inside_forbidden(text, pos):
    """True if `pos` is inside a list, table, product card, contents box, FAQ item or the offers box."""
    before = text[:pos]
    for tag, close in (("<ul", "</ul>"), ("<ol", "</ol>"), ("<table", "</table>")):
        if before.rfind(tag) > before.rfind(close):
            return tag
    for cls in ('class="product-card', 'class="toc"', 'class="faq-item"', 'class="perk-offers"'):
        i = before.rfind(cls)
        if i != -1:
            depth_open = before[i:].count("<div") - before[i:].count("</div>")
            if depth_open > 0:
                return cls
    return None


def test_ads_are_off_while_no_slot_id_is_set():
    cfg = json.loads((P.ROOT / "scripts/ads.json").read_text(encoding="utf-8"))
    assert cfg["client"] == "ca-pub-6309879983967574", "the AdSense publisher id changed"
    if any(cfg["slots"].values()):
        pytest.skip("slots are configured: the other tests cover them")
    assert not [r for r in P.all_html() if "ad-slot" in P.read(r) or 'class="adsbygoogle"' in P.read(r)]


@pytest.mark.parametrize("rel", REVIEWS)
def test_slots_land_only_in_reader_safe_places(rel, with_ids):
    text = P.read(rel)
    if not A.is_indexable_review(text):
        pytest.skip("not an indexable review (no ads on noindex or sidebar-less pages)")
    new = A.place(text, B.PAGES[rel][1][0])
    assert new.count('class="ad-slot ad-slot-sidebar"') == 1
    assert 1 <= new.count('class="ad-slot ad-slot-article"') <= 3
    hero_end = new.index('class="article-hero"')
    for m in re.finditer(r'<!-- ad:(\w+) -->', new):
        pos = m.start()
        assert pos > hero_end, "an ad sits above the hero"
        if "ad-slot-sidebar" in new[pos:pos + 200]:
            continue
        assert not _inside_forbidden(new, pos), f"{rel}: ad inside {_inside_forbidden(new, pos)}"
        art_start = new.index('<article class="article-body"')
        assert pos > art_start and pos < new.index("</article>")
    assert 'data-ad-client="ca-pub-6309879983967574"' in new and new.count(".push({})") == new.count("<ins class=\"adsbygoogle\"")


@pytest.mark.parametrize("rel", REVIEWS[:6])
def test_placing_twice_changes_nothing_and_removing_restores_the_page(rel, with_ids, monkeypatch):
    text = A.BLOCK_RE.sub("", P.read(rel))  # the page without any ad blocks, whatever is configured for real
    once = A.place(text, B.PAGES[rel][1][0])
    assert A.place(once, B.PAGES[rel][1][0]) == once, "placement is not idempotent"
    monkeypatch.setattr(A, "config", lambda: {"client": DUMMY["client"], "slots": {"in_article": "", "after_table": "", "sidebar": ""}})
    assert A.place(once, B.PAGES[rel][1][0]) == text, "turning the slots off does not restore the original page"


def test_a_slot_needs_its_own_id(monkeypatch):
    text = P.read("blog/best-tablets-for-seniors.html")
    monkeypatch.setattr(A, "config", lambda: {"client": DUMMY["client"], "slots": {"in_article": "", "after_table": "2222222222", "sidebar": ""}})
    new = A.place(text, "ipad")
    assert new.count("ad-slot-table") == 1 and "ad-slot-article" not in new and "ad-slot-sidebar" not in new
