"""Links: affiliate rules (the part that gets you paid), and links that point inside the site."""
import json
import re
from urllib.parse import parse_qsl, urlparse

import pytest

import pages as P
import htmlutil as H

APPROVED = json.loads((P.ROOT / "tests/data/approved_amazon_links.json").read_text(encoding="utf-8"))


def _amazon_anchors(rel):
    return [a for a in H.parse(rel).anchors if re.search(r"(^|\.)amazon\.(com|ca)$", urlparse(a.get("href", "")).hostname or "")]


def _expected_tags(kind):
    return P.AMAZON_TAGS.get(kind, P.ALL_TAGS)


def test_amazon_links_use_the_right_tracking_id(html_page):
    """US articles, gift guides and Canada articles each have their own tracking ID. A wrong one means lost commission."""
    kind = P.kind(html_page)
    problems = []
    for a in _amazon_anchors(html_page):
        url = urlparse(a["href"])
        tag = dict(parse_qsl(url.query)).get("tag")
        if tag is None:
            problems.append(f"line {a['_line']}: no tag= on {a['href'][:80]}")
        elif tag not in _expected_tags(kind):
            problems.append(f"line {a['_line']}: tag {tag!r} not allowed on a {kind} page (allowed: {sorted(_expected_tags(kind))})")
    assert not problems, "\n".join(problems)


def test_amazon_domain_matches_the_market(html_page):
    kind = P.kind(html_page)
    problems = []
    for a in _amazon_anchors(html_page):
        host = urlparse(a["href"]).hostname
        if kind == "article-ca" and host.endswith(".com"):
            problems.append(f"line {a['_line']}: Canada page links to {host}")
        if kind in ("article-us", "gift-guide") and host.endswith(".ca"):
            problems.append(f"line {a['_line']}: US page links to {host}")
    assert not problems, "\n".join(problems)


def test_amazon_links_are_marked_sponsored_and_safe(html_page):
    problems = []
    for a in _amazon_anchors(html_page):
        rel = a.get("rel", "").split()
        if "sponsored" not in rel:
            problems.append(f"line {a['_line']}: missing rel=\"sponsored\"")
        if a.get("target") == "_blank" and "noopener" not in rel:
            problems.append(f"line {a['_line']}: target=_blank without noopener")
    assert not problems, "\n".join(problems)


def test_no_shortened_or_foreign_affiliate_links(html_page):
    bad = [a["href"] for a in H.parse(html_page).anchors
           if re.search(r"(^|//)(amzn\.to|a\.co|amzn\.com|geni\.us|bit\.ly)\b", a.get("href", ""))]
    assert not bad, f"shortened/redirect links hide the destination and can't be audited: {bad}"


def test_pages_with_affiliate_links_carry_the_disclosure(html_page):
    if not _amazon_anchors(html_page):
        pytest.skip("no Amazon links")
    text = P.read(html_page).lower()
    assert "amazon associate" in text or "participant in the amazon services llc associates program" in text, (
        "page has affiliate links but no 'Amazon Associate' disclosure text")
    assert "affiliate-disclosure.html" in text, "page has affiliate links but does not link to the affiliate disclosure page"


def _match_membership(href, market):
    url = urlparse(href)
    query = dict(parse_qsl(url.query))
    tag = query.pop("tag", None)
    for entry in APPROVED[market]:
        if url.hostname == entry["host"] and url.path == entry["path"] and query == entry["params"]:
            return entry["name"], tag
    return None, tag


def test_membership_links_are_the_verified_ones(html_page):
    """Prime / Audible / Music / Kindle Unlimited bounty links must match tests/data/approved_amazon_links.json exactly."""
    kind = P.kind(html_page)
    market = "ca" if kind == "article-ca" else "us"
    problems = []
    for a in H.parse(html_page).anchors:
        cta = a.get("data-cta", "")
        if not cta.startswith("membership_"):
            continue
        name, tag = _match_membership(a["href"], market)
        if name is None:
            problems.append(f"line {a['_line']}: not an approved {market.upper()} membership link: {a['href']}")
        elif tag not in _expected_tags(kind):
            problems.append(f"line {a['_line']}: {name} link has tag {tag!r}")
    assert not problems, "\n".join(problems)


def test_discontinued_offers_are_gone(html_page):
    gone = [d["path"] for d in APPROVED["discontinued"]]
    text = P.read(html_page)
    found = [p for p in gone if p in text]
    assert not found, f"links to offers Amazon has ended: {found}"


def test_other_external_links_are_https_and_safe(html_page):
    problems = []
    for a in H.parse(html_page).anchors:
        href = a.get("href", "")
        host = urlparse(href).hostname
        if not host or re.search(r"(^|\.)amazon\.(com|ca)$", host) or host.endswith("techfordad.com"):
            continue
        if href.startswith("http://"):
            problems.append(f"line {a['_line']}: insecure link {href}")
        if a.get("target") == "_blank" and "noopener" not in a.get("rel", "").split():
            problems.append(f"line {a['_line']}: target=_blank without noopener on {href[:70]}")
    assert not problems, "\n".join(problems)


def test_in_page_anchors_point_at_real_ids(html_page):
    doc = H.parse(html_page)
    ids = set(doc.ids)
    missing = [a["href"] for a in doc.anchors if a.get("href", "").startswith("#") and len(a["href"]) > 1 and a["href"][1:] not in ids]
    assert not missing, f"links to #anchors that do not exist on this page: {sorted(set(missing))[:8]}"
