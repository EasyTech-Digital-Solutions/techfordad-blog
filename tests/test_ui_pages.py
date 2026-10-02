"""Every content page, in a real browser, at desktop and phone size: it loads cleanly and nothing is broken or cut off."""
import json

import pytest

import pages as P

pytestmark = pytest.mark.slow
THIRD = json.loads((P.ROOT / "tests/data/third_party_hosts.json").read_text(encoding="utf-8"))


def test_loads_without_errors(page, viewport, report):
    """No JavaScript errors, no console errors, no local file that fails to load (404, 500, blocked)."""
    errors = [m for t, m in report["console"] if t == "error"]
    assert not report["pageErrors"], f"JavaScript errors: {report['pageErrors'][:3]}"
    assert not errors, f"console errors: {errors[:3]}"
    expected_404 = P.kind(page) == "error"  # the 404 page is served by a server that returns 404 for it
    failed = [f for f in report["failedLocal"] if not (expected_404 and f[1].endswith("/404.html"))]
    assert not failed, f"files that failed to load: {failed[:5]}"


def test_no_console_warnings(page, viewport, report):
    warnings = [m for t, m in report["console"] if t == "warning"]
    assert not warnings, f"browser warnings (deprecations, mixed content, CSP): {warnings[:3]}"


def test_no_sideways_scrolling(page, viewport, report):
    assert report["docWidth"] <= report["vw"] + 1, (
        f"page is {report['docWidth']}px wide in a {report['vw']}px window; sticking out: {report['wide']}")
    assert not report["wide"], f"elements run past the right edge: {report['wide']}"


def test_no_broken_images(page, viewport, report):
    assert not report["brokenImages"], f"images that failed to render: {report['brokenImages'][:5]}"


def test_page_chrome_present(page, viewport, report):
    assert report["hasHeader"], "header is missing or hidden"
    assert report["hasFooter"], "footer is missing"
    assert report["h1Count"] == 1 and report["h1Text"], "the page needs exactly one non-empty h1"


def test_mobile_menu_button(page, viewport, report):
    """The hamburger button must exist on phones and not appear on desktop."""
    assert report["navToggleVisible"] == (viewport == "mobile")


def test_touch_targets_on_phones(page, viewport, report):
    """Buttons and tappable controls we own are at least 44px tall on a phone (older fingers, bigger targets)."""
    if viewport != "mobile":
        pytest.skip("phone-only check")
    assert not report["smallTargets"], f"controls under 44px tall: {report['smallTargets'][:5]}"


def test_list_text_is_readable_on_phones(page, viewport, report):
    if viewport != "mobile":
        pytest.skip("phone-only check")
    assert report["smallProsCons"] == 0, f"{report['smallProsCons']} pros/cons items are under 14px on a phone"


def test_only_allowlisted_third_parties_are_contacted(page, viewport, report):
    from urllib.parse import urlparse

    hosts = {urlparse(u).hostname for u in report["external"]}
    extra = sorted(hosts - set(THIRD["script"]))
    assert not extra, f"the page contacts websites that are not on tests/data/third_party_hosts.json: {extra}"


# ------------------------------------------------------------- print & share toolbar and table button (layout)

def test_toolbar_present_only_where_intended(page, viewport, report):
    expected = 1 if P.has_toolbar(page) else 0
    assert report["toolbar"]["count"] == expected, (
        f"expected {expected} print/share toolbar on a {P.kind(page)} page, found {report['toolbar']['count']}")


def test_toolbar_lines_up_with_the_article(page, viewport, report):
    if not P.has_toolbar(page):
        pytest.skip("page has no toolbar")
    tb = report["toolbar"]
    assert tb["leftDelta"] is not None and abs(tb["leftDelta"]) <= 2, (
        f"toolbar is {tb['leftDelta']}px off the article's left edge (it should line up with the content column)")
    assert tb["rightOverflow"] <= 1, "toolbar runs past the right edge"
    assert tb["labels"][0] == "Print this page" and "Copy link" in tb["labels"], f"unexpected buttons: {tb['labels']}"
    if viewport == "mobile":
        assert tb["rows"] <= 2, f"toolbar wraps onto {tb['rows']} rows on a phone (it should be a tidy 2-row grid)"


def test_table_print_button_only_on_pages_with_a_comparison_table(page, viewport, report):
    assert report["tableToolsCount"] == (1 if report["hasCompareTable"] else 0), (
        f"comparison table: {report['hasCompareTable']}, table print bars: {report['tableToolsCount']}")


def test_swipe_hint_shows_only_when_the_table_scrolls(page, viewport, report):
    if not report["hasCompareTable"]:
        pytest.skip("no comparison table")
    assert report["hintVisible"] == bool(report["tableScrolls"]), (
        f"hint visible={report['hintVisible']} but table scrolls={report['tableScrolls']}")


def test_membership_offers_are_complete(page, viewport, report):
    """If a page shows an offer card, it has real buttons; and the buttons are easy to tap on a phone."""
    perk = report["perk"]
    if perk["notes"]:
        assert perk["buttons"], "offer card without any button"
    if viewport == "mobile":
        small = [b for b in perk["buttons"] if b["h"] and b["h"] < 43.5]
        assert not small, f"offer buttons under 44px: {small}"


def test_articles_are_two_columns_on_desktop_and_stacked_on_phones(page, viewport, report):
    """The sidebar sits beside the article on desktop and drops below it on a phone."""
    if P.kind(page) not in {"article-us", "article-ca"}:
        pytest.skip("not a USA/Canada article")
    lay = report["layout"]
    assert lay["article"] and lay["sidebar"], f"missing article column or sidebar: {lay}"
    if viewport == "desktop":
        assert lay["sideRight"], "sidebar should be to the right of the article on a desktop screen"
    else:
        assert lay["sideBelow"], "sidebar should sit below the article on a phone"
    assert "Related Guides" in lay["boxes"]
