"""Content rules that keep the site fair, transparent and source-based (added in the 2026-10-05 sweep).

The site says it does not test products and does not claim experience it does not have (About, How We Review). These tests
make that promise checkable: they fail on wording that claims experience, on superlatives no source supports, on a tax claim
the CRA contradicts, and on health pages that cite nothing. They read the visible text only (not scripts or JSON-LD).
"""
import html
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_health_note as H  # noqa: E402
import pages as P  # noqa: E402

CONTENT_KINDS = {"article-us", "article-ca", "guide", "gift-guide", "home", "hub", "info"}

# Wording that claims first-hand experience, testing or conversations the site does not have.
INVENTED_EXPERIENCE = [
    r"\bwe(?:'|’)ve (?:spoken|talked|heard|interviewed|visited|met|seen families)",
    r"\bwe have (?:spoken|talked|interviewed)",
    r"\b(?:caregivers|families|readers|seniors) we(?:'|’)ve\b",
    r"\btold us\b",
    r"\b(?:our readers|readers (?:say|report|told|wrote))\b",
    r"\bin our experience\b",
    r"\bfrom our experience\b",
    r"\bwe personally\b",
    r"\bour (?:testers|reviewers|lab|test lab)\b",
    r"\bin our (?:tests|testing|lab)\b",
    r"\bwe (?:tested|wore|used) (?:it|them|the|this|these)\b",
    r"\bhands-on (?:tested|testing)\b(?! (?:a|any|the)?)",
]
# Superlatives and medical claims no source on the site supports.
UNSUPPORTED = [
    r"\bindustry[- ]leading\b",
    r"\bbest[- ]in[- ]class\b",
    r"\bclinically proven\b",
    r"\bmedically proven\b",
    r"\bmiracle\b",
    r"\bno other tracker (?:on the market|available|comes close)\b",
    r"\bonly tracker we can recommend\b",
]

AUTHORITY_DOMAINS = (
    "cdc.gov", "fda.gov", "nih.gov", "medicare.gov", "irs.gov", "canada.ca", "statcan.gc.ca", "justice.gc.ca", "alz.org",
    "alzheimer.ca", "ncoa.org", "hypertension.ca", "ontario.ca", "alberta.ca", "gov.bc.ca", "gov.mb.ca", "myretireeplan.ca",
    "heart.org", "aarp.org", "iii.org", "ibc.ca", "telus.com", "rogers.com", "va.gov", "hearingtracker.com", "hearingreview.com",
    "laws-lois.justice.gc.ca", "carp.ca",
)


def _visible_text(rel):
    text = P.read(rel)
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", text, flags=re.S)
    m = re.search(r"<main\b.*?</main>", text, re.S)
    text = m.group(0) if m else text
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split())


def _content_page(rel):
    if P.kind(rel) not in CONTENT_KINDS or P.is_noindex(rel):
        pytest.skip("not an indexable content page")


def test_no_claims_of_experience_the_site_does_not_have(html_page):
    _content_page(html_page)
    if html_page == "how-we-review.html":
        pytest.skip("explains what we do not do")
    text = _visible_text(html_page)
    hits = [m.group(0) for pat in INVENTED_EXPERIENCE for m in [re.search(pat, text, re.I)] if m]
    assert not hits, f"wording claims experience or testing we do not have: {hits}. Say what the source says instead."


def test_no_unsupported_superlatives(html_page):
    _content_page(html_page)
    text = _visible_text(html_page)
    hits = [m.group(0) for pat in UNSUPPORTED for m in [re.search(pat, text, re.I)] if m]
    assert not hits, f"unsupported claim wording: {hits}. Attribute it to the maker or remove it."


def test_blood_pressure_monitors_are_not_called_tax_claimable(html_page):
    """The CRA guide lists blood pressure monitors under 'common medical expenses you cannot claim'."""
    _content_page(html_page)
    for para in re.findall(r"<(?:p|li|div)\b[^>]*>(.*?)</(?:p|li|div)>", P.read(html_page), re.S):
        plain = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", para)).split())
        if re.search(r"blood pressure monitor", plain, re.I) and re.search(r"medical expense tax credit|METC", plain, re.I):
            assert re.search(r"cannot claim|can't claim|not eligible|do not count", plain, re.I), f"tax claim about blood pressure monitors: {plain[:160]}"


@pytest.mark.parametrize("rel", H.MEDICAL_PAGES)
def test_health_pages_link_to_their_sources(rel):
    """A medical page with no source links at all is not source-based. (One link is the floor; most pages have several.)"""
    body = re.search(r"<(?:article|main)\b.*?</(?:article|main)>", P.read(rel), re.S).group(0)
    hrefs = re.findall(r'href="(https?://[^"]+)"', body)
    sources = [h for h in hrefs if any(d in h.split("/")[2] for d in AUTHORITY_DOMAINS)]
    assert sources, f"{rel}: no links to health, government or independent sources in the body"


def test_gift_guides_keep_their_membership_links():
    """build_gift_guides.py does not know about the Prime/Audible/Music bounty links; regenerating deletes them (it did once)."""
    page = P.read("gift-guides/tech-gifts-for-elderly-parents.html")
    assert "amazon.com/amazonprime?tag=techfordad-gifts-20" in page, "the Prime membership link is gone from the gift guide"
    assert 'class="perk-' in page, "the membership offer blocks are gone from the gift guide"


def test_no_numeric_scores(html_page):
    """How We Review says "We do not use a numeric score". Invented X/10 or X/5 scores implied testing the site does not do
    (removed 2026-10-05). A third party's published score may stay when it is attributed (the HearAdvisor lab grade)."""
    _content_page(html_page)
    text = _visible_text(html_page)
    text = re.sub(r"HearAdvisor lab test:.*?\)", "", text)  # attributed, independent lab figure
    hits = re.findall(r"\b(?:our score|our rating)\b|\b\d(?:\.\d)?\s?/\s?(?:10|5)\b|\b\d(?:\.\d)?\s+out of\s+(?:10|5)\b", text, re.I)
    assert not hits, f"numeric score on the page: {hits[:3]}"


AMAZON_REVIEW_CLAIMS = re.compile(
    r"verified (?:customer|user|buyer|amazon)s?(?: \w+)? reviews|"
    r"\b(?:customers|reviewers|users|owners|buyers)\s+(?:consistently|frequently|often|generally)\b|"
    r"\bconsistently (?:rated|praised|reported)\b|\bhigh marks\b|\bstrong marks\b|"
    r"\b\d[\d,]*\+?\s(?:customer |amazon |verified )*(?:ratings|reviews)\b|\b\d\.\d[- ]stars?\b|\b\d-star (?:rating|average)\b|"
    r"\bamazon (?:rating|reviews)\b", re.I)


def test_no_amazon_ratings_or_invented_review_claims(html_page):
    """Amazon's Associates rules allow star ratings and review counts only when they come from its API, and the site says it does not
    test products: so no review counts, star averages or "customers consistently report" claims (removed 2026-10-05)."""
    _content_page(html_page)
    if html_page in ("about.html", "how-we-review.html", "our-story.html"):
        pytest.skip("these pages describe how we work (we read published and buyer reviews); they make no claim about a product")
    text = _visible_text(html_page)
    hits = [m.group(0) for m in AMAZON_REVIEW_CLAIMS.finditer(text)]
    assert not hits, f"claims about customer reviews or Amazon ratings: {hits[:3]}"


NUMBER_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12}


def test_researched_counts_match_the_products_shown(html_page):
    """A review must not claim a bigger research set than it shows ("8 devices researched" above five product cards, or "We researched 12
    systems" with five listed): every "N compared/researched" figure equals the number of product cards (fixed 2026-10-05)."""
    _content_page(html_page)
    raw = P.read(html_page)
    cards = len(re.findall(r'class="product-card', raw))
    if cards < 2:
        pytest.skip("no product cards")
    text = _visible_text(html_page)
    claims = []
    for m in re.finditer(r"<span>(\d{1,2})\s+[A-Za-z&\- ]+?\s+(?:researched|compared)</span>", raw):  # the hero line: "5 monitors compared"
        claims.append((int(m.group(1)), m.group(0)))
    for m in re.finditer(r"\bWe (?:researched|compared) (?:the )?(\d{1,2}|" + "|".join(NUMBER_WORDS) + r")\b", text, re.I):
        n = m.group(1).lower()
        claims.append((int(n) if n.isdigit() else NUMBER_WORDS[n], m.group(0)))
    bad = [c for n, c in claims if n != cards]
    assert not bad, f"{html_page}: shows {cards} products but says: {bad[:3]}"
