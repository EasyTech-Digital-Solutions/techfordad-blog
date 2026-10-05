"""What comes out of the printer: chrome removed, content kept, page address and date added."""
import pytest

import pages as P

pytestmark = pytest.mark.slow

HIDDEN_ON_PAPER = [
    "header", "footer", ".gift-bar", "aside", ".page-tools", ".table-tools", ".btn-check-price", ".perk-note",
    ".perk-cta", ".perk-line", ".card-perk", ".perk-btn", ".toc-box", ".related-guides", ".author-box", ".newsletter",
    ".email-form", ".breadcrumb",
]


def test_print_layout_removes_page_chrome_and_keeps_content(page, sessions):
    pg, *_ = sessions("desktop").open(page)
    pg.emulate_media(media="print")
    still_visible = pg.evaluate("""(sels) => sels.flatMap(sel =>
        [...document.querySelectorAll(sel)].filter(e => getComputedStyle(e).display !== 'none').map(() => sel))""", HIDDEN_ON_PAPER)
    assert not still_visible, f"these still show when printed: {sorted(set(still_visible))}"
    info = pg.evaluate("""() => ({
        h1: !!document.querySelector('h1') && getComputedStyle(document.querySelector('h1')).display !== 'none',
        words: document.body.innerText.split(/\\s+/).length,
        closedAnswers: [...document.querySelectorAll('.faq-a')].filter(e => getComputedStyle(e).display === 'none').length,
        black: getComputedStyle(document.body).color,
    })""")
    assert info["h1"], "the page title must print"
    assert info["words"] > 80, "the printout is nearly empty"
    assert info["closedAnswers"] == 0, f"{info['closedAnswers']} FAQ answers would print closed (hidden)"
    pg.close()


def test_printout_names_the_page_and_the_date(page, toolbar_page, sessions):
    pg, *_ = sessions("desktop").open(page)
    canonical = pg.evaluate("document.querySelector('link[rel=canonical]').href")
    screen_hidden = pg.evaluate("[...document.querySelectorAll('.print-only')].every(e => getComputedStyle(e).display === 'none')")
    assert screen_hidden, "print-only text must not show on screen"
    pg.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    pg.emulate_media(media="print")
    head = pg.locator(".print-head").inner_text()
    foot = pg.locator(".print-foot").inner_text()
    assert head == f"TechForDad · {canonical}", head
    assert foot.startswith("Printed ") and "check the retailer" in foot, foot
    assert pg.locator(".print-head").is_visible() and pg.locator(".print-foot").is_visible()
    pg.close()


def test_country_badge_is_not_printed(sample_page, sessions):
    """A floating pill on a printed page would sit on top of the text."""
    if not P.has_toolbar(sample_page):
        pytest.skip("page has no country badge")
    pg, console, errors, failed = sessions("desktop").open(sample_page)
    pg.emulate_media(media="print")
    shown = pg.evaluate("(() => { const e = document.querySelector('.country-badge'); return !!e && getComputedStyle(e).display !== 'none'; })()")
    pg.close()
    assert not shown, "the country badge is visible when printing"
