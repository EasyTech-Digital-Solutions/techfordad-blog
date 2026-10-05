"""US and Canada twins share one structure, and every page type ends the same way (docs/page-structure.md)."""
import re

import pytest

import pages as P

PAIRS = sorted(
    (p.relative_to(P.ROOT).as_posix(), p.relative_to(P.ROOT).as_posix().replace(".html", "-canada.html"))
    for p in (P.ROOT / "blog").glob("best-*.html")
    if not p.name.endswith("-canada.html") and (P.ROOT / "blog" / p.name.replace(".html", "-canada.html")).exists()
)

MARKERS = [
    ("strip", 'class="article-disclaimer"'), ("toc", "Table of Contents"), ("which-one", "<!-- buy-summary -->"),
    ("compare", 'id="comparison"'), ("faq", 'id="faq"'), ("how-we-chose", "<!-- how-we-chose -->"),
    ("sources", "<!-- sources -->"), ("related", "<!-- related -->"), ("newsletter", 'class="newsletter"'), ("author", 'class="author-box'),
]


def _order(rel):
    t = P.read(rel)
    return [name for name, m in sorted(MARKERS, key=lambda x: t.find(x[1]) if x[1] in t else 10**9) if m in t]


@pytest.mark.parametrize("us,ca", PAIRS, ids=[u.split("/")[1] for u, _ in PAIRS])
def test_twins_have_the_same_sections_in_the_same_order(us, ca):
    if P.is_noindex(us) or P.is_noindex(ca):
        pytest.skip("parked (noindex) page: it is not rewritten to the layout until it is brought back")
    a, b = _order(us), _order(ca)
    # a twin may lack a section the other has for a content reason (no Canada Sources yet), but never reorder the shared ones
    shared = [x for x in a if x in b]
    assert shared == [x for x in b if x in a], f"{us} and {ca} order their sections differently:\n  {a}\n  {b}"
    for must in ("strip", "faq", "how-we-chose", "related", "newsletter", "author"):
        assert (must in a) == (must in b), f"only one of {us} / {ca} has the {must!r} section"


@pytest.mark.parametrize("us,ca", PAIRS, ids=[u.split("/")[1] for u, _ in PAIRS])
def test_twins_say_the_same_disclosure(us, ca):
    def strip(rel):
        m = re.search(r'<div class="article-disclaimer">\s*(.*?)(?:<br>|</div>)', P.read(rel), re.S)
        return re.sub(r"\s+", " ", m.group(1)).strip() if m else None
    assert strip(us) == strip(ca), "the disclosure strip differs between the USA and Canada page"


def test_every_content_page_ends_with_newsletter_then_author_strip_then_footer():
    problems = []
    for rel in P.all_html():
        t = P.read(rel)
        if "class=\"author-box" not in t or 'http-equiv="refresh"' in t:
            continue
        if "<footer" not in t:
            continue
        a = t.index('class="author-box')
        if 'class="newsletter"' in t and t.index('class="newsletter"') > a:
            problems.append(f"{rel}: newsletter comes after the author strip")
        if a > t.index("<footer"):
            problems.append(f"{rel}: author strip is after the footer")
    assert not problems, problems


def test_no_page_repeats_the_commission_sentence_in_a_second_box():
    """One disclosure per page: the strip. The old sidebar note, the amber box and the author-box line are gone."""
    bad = []
    for rel in P.all_html():
        t = P.read(rel)
        main = t[t.find("<main"):t.find("</main>")] if "<main" in t else ""
        if not main:
            continue
        if 'class="disclaimer"' in main or 'class="affiliate-box"' in main or main.count("<strong>Affiliate Disclosure:</strong>") > 1:
            bad.append(rel)
        if re.search(r'background:#fffbeb[^>]*>\s*<strong>Affiliate Disclosure', main):
            bad.append(rel + " (old amber box)")
        if "We may earn a commission from some links" in main:
            bad.append(rel + " (author box)")
    assert not bad, bad
