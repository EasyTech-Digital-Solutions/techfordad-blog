"""Things a visitor can click: FAQ, mobile menu, copy/share, and the print buttons (including the scroll-position fix)."""
import pytest

import pages as P

pytestmark = pytest.mark.slow

# Stand-in for the browser's print dialog: records what the page looked like at print time, then behaves like
# Chrome after a cancelled print (fires beforeprint, jumps to the top, fires afterprint).
PRINT_STUB = """
window.__prints = [];
window.print = () => {
  window.__prints.push({
    summary: document.body.classList.contains('print-summary'),
    keep: [...document.querySelectorAll('.print-keep')].map(e => e.id || e.tagName.toLowerCase()),
  });
  window.dispatchEvent(new Event('beforeprint'));
  window.scrollTo(0, 0);
  window.dispatchEvent(new Event('afterprint'));
};
"""
# Same, but stays in "printing" state so the test can inspect the print layout.
PRINT_HOLD = PRINT_STUB.replace("window.scrollTo(0, 0);\n  window.dispatchEvent(new Event('afterprint'));", "")


def _open(sessions, rel, viewport="desktop", init=None):
    pg, console, errors, failed = sessions(viewport).open(rel, init=init)
    return pg


def _scroll_to_middle(pg):
    y = pg.evaluate("Math.round((document.documentElement.scrollHeight - innerHeight) * 0.4)")
    pg.evaluate(f"scrollTo(0, {y})")
    pg.wait_for_timeout(80)
    return y


def _press(locator):
    """Click without scrolling first: Playwright's click() scrolls the element into view, which would hide scroll bugs."""
    locator.evaluate("e => e.click()")


def _button(pg, text):
    return pg.locator(".page-tools button, .page-tools a, .table-tools button").filter(has_text=text).first


# ------------------------------------------------------------------ FAQ and navigation

def test_faq_opens_and_closes(page, sessions):
    pg = _open(sessions, page)
    if not pg.locator(".faq-item .faq-q").count():
        pytest.skip("page has no click-to-open FAQ (some pages show every answer, which is fine)")
    item = pg.locator(".faq-item").first
    item.locator(".faq-q").click()
    assert "open" in item.get_attribute("class")
    assert item.locator(".faq-a").is_visible(), "answer should show after opening"
    item.locator(".faq-q").click()
    assert "open" not in item.get_attribute("class")
    assert not item.locator(".faq-a").is_visible(), "answer should hide after closing"
    pg.close()


def test_mobile_menu_opens_and_closes(sample_page, sessions):
    pg = _open(sessions, sample_page, "mobile")
    toggle = pg.locator(".nav-toggle")
    assert toggle.is_visible()
    before = pg.locator("#site-nav a").first.is_visible()
    toggle.click()
    pg.wait_for_timeout(150)
    assert pg.locator("#site-nav a").first.is_visible(), "menu links should show after tapping the menu button"
    toggle.click()
    pg.wait_for_timeout(150)
    assert pg.locator("#site-nav a").first.is_visible() == before, "menu should close again"
    pg.close()


def test_reviews_dropdown_opens_on_desktop(sample_page, sessions):
    pg = _open(sessions, sample_page)
    btn = pg.locator(".nav-dropdown-toggle").first
    if not btn.count():
        pytest.skip("no dropdown on this page")
    btn.click()
    assert btn.get_attribute("aria-expanded") == "true"
    assert pg.locator(".nav-dropdown-menu").first.is_visible()
    pg.keyboard.press("Escape")
    pg.close()


# ------------------------------------------------------------------ share and copy

def test_copy_link_copies_the_canonical_address(page, toolbar_page, sessions):
    sess = sessions("desktop")
    sess.ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=sess.base)
    pg = _open(sessions, page)
    canonical = pg.evaluate("document.querySelector('link[rel=canonical]').href")
    _button(pg, "Copy link").click()
    pg.wait_for_timeout(150)
    assert "Link copied" in pg.locator(".page-tools-status").inner_text()
    assert pg.evaluate("navigator.clipboard.readText()") == canonical, "must copy the clean page address, never an affiliate link"
    pg.close()


def test_share_falls_back_to_text_and_email(sample_page, sessions):
    """Desktop browsers without a share sheet get 'Text it' and 'Email it' links carrying the page address."""
    if not P.has_toolbar(sample_page):
        pytest.skip("page has no toolbar")
    pg = _open(sessions, sample_page, init="Object.defineProperty(navigator, 'share', {value: undefined, configurable: true});")
    canonical = pg.evaluate("document.querySelector('link[rel=canonical]').href")
    text_href = _button(pg, "Text it").get_attribute("href")
    mail_href = _button(pg, "Email it").get_attribute("href")
    from urllib.parse import quote
    assert text_href.startswith("sms:?&body=") and quote(canonical, safe="") in text_href
    assert mail_href.startswith("mailto:?subject=") and quote(canonical, safe="") in mail_href
    assert pg.locator(".page-tools button", has_text="Share").count() == 0
    pg.close()


def test_native_share_sheet_gets_title_and_canonical_url(sample_page, sessions):
    if not P.has_toolbar(sample_page):
        pytest.skip("page has no toolbar")
    pg = _open(sessions, sample_page, init="navigator.share = async (d) => { window.__shared = d; };")
    canonical = pg.evaluate("document.querySelector('link[rel=canonical]').href")
    h1 = pg.evaluate("document.querySelector('h1').textContent.trim()")
    _button(pg, "Share").click()
    pg.wait_for_timeout(100)
    shared = pg.evaluate("window.__shared")
    assert shared == {"title": h1, "url": canonical}
    assert pg.locator(".page-tools a", has_text="Text it").count() == 0
    pg.close()


# ------------------------------------------------------------------ print buttons

def test_print_page_restores_scroll_position(page, toolbar_page, sessions):
    """Regression test: cancelling the print dialog used to send the reader back to the top of the page."""
    pg = _open(sessions, page, init=PRINT_STUB)
    y = _scroll_to_middle(pg)
    _press(_button(pg, "Print this page"))
    pg.wait_for_timeout(200)
    after = pg.evaluate("scrollY")
    assert abs(after - y) <= 5, f"page jumped from {y}px to {after}px after printing"
    state = pg.evaluate("({prints: window.__prints.length, flag: document.body.classList.contains('print-summary'), keep: document.querySelectorAll('.print-keep').length})")
    assert state == {"prints": 1, "flag": False, "keep": 0}
    pg.close()


def test_ctrl_p_restores_scroll_position(sample_page, sessions):
    if not P.has_toolbar(sample_page):
        pytest.skip("page has no toolbar")
    pg = _open(sessions, sample_page)
    y = _scroll_to_middle(pg)
    pg.evaluate("window.dispatchEvent(new Event('beforeprint')); window.scrollTo(0, 0); window.dispatchEvent(new Event('afterprint'));")
    pg.wait_for_timeout(200)
    assert abs(pg.evaluate("scrollY") - y) <= 5
    pg.close()


def test_quick_comparison_prints_only_the_picks_and_table(page, toolbar_page, sessions):
    pg = _open(sessions, page, init=PRINT_STUB)
    btn = _button(pg, "Print quick comparison")
    if not btn.count():
        pytest.skip("page has no picks summary or comparison table")
    y = _scroll_to_middle(pg)
    _press(btn)
    pg.wait_for_timeout(200)
    printed = pg.evaluate("window.__prints[0]")
    assert printed["summary"] is True
    assert printed["keep"], "nothing was marked for printing"
    assert ("comparison" in printed["keep"]) or ("top-picks" in printed["keep"]) or ("which-one" in printed["keep"])
    assert abs(pg.evaluate("scrollY") - y) <= 5
    assert pg.evaluate("document.querySelectorAll('.print-keep').length") == 0, "page should be restored afterwards"
    pg.close()


def test_table_button_prints_only_the_table(page, toolbar_page, sessions):
    pg = _open(sessions, page, init=PRINT_STUB)
    btn = pg.locator(".table-tools button", has_text="Print this table")
    if not btn.count():
        pytest.skip("page has no comparison table")
    btn.scroll_into_view_if_needed()
    y = pg.evaluate("scrollY")
    btn.click()
    pg.wait_for_timeout(200)
    printed = pg.evaluate("window.__prints[0]")
    assert printed["summary"] is True and printed["keep"][0] == "comparison", printed
    assert "top-picks" not in printed["keep"] and "which-one" not in printed["keep"], "table-only print must not include the picks list"
    assert abs(pg.evaluate("scrollY") - y) <= 5, "page jumped after the table print"
    pg.close()


def test_table_more_options_link_scrolls_to_the_toolbar(page, toolbar_page, sessions):
    pg = _open(sessions, page)
    link = pg.locator(".table-tools a")
    if not link.count():
        pytest.skip("page has no comparison table")
    link.scroll_into_view_if_needed()
    link.click()
    pg.wait_for_function("(() => { const r = document.querySelector('#page-tools').getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; })()", timeout=5000)
    try:  # focus moves a moment after the scroll starts
        pg.wait_for_function("document.activeElement && document.activeElement.closest('.page-tools') !== null", timeout=3000)
    except Exception:
        raise AssertionError("keyboard focus should land in the toolbar")
    pg.close()


def test_quick_print_layout_hides_everything_else(page, toolbar_page, sessions):
    """In print mode with the quick-comparison button pressed, only the marked sections are left in the article."""
    pg = _open(sessions, page, init=PRINT_HOLD)
    btn = _button(pg, "Print quick comparison")
    if not btn.count():
        pytest.skip("no quick print on this page")
    btn.click()
    pg.emulate_media(media="print")
    visible = pg.evaluate("""() => {
        const host = document.querySelector('.print-host');
        return [...host.children].filter(c => getComputedStyle(c).display !== 'none' && !c.classList.contains('print-only'))
                                 .map(c => c.classList.contains('print-keep'));
    }""")
    assert visible and all(visible), "an unmarked section is still visible in the quick print"
    pg.close()


def test_skip_link_works_with_keyboard(sample_page, sessions):
    """First Tab reveals 'Skip to main content'; Enter jumps to the page content."""
    pg = _open(sessions, sample_page)
    link = pg.locator(".skip-link")
    assert link.bounding_box()["y"] < 0, "skip link should be hidden until it has keyboard focus"
    pg.keyboard.press("Tab")
    assert pg.evaluate("document.activeElement.className") == "skip-link", "the skip link must be the first thing Tab reaches"
    assert link.bounding_box()["y"] >= 0, "skip link must be visible while focused"
    pg.keyboard.press("Enter")
    assert pg.evaluate("document.activeElement.id") == "main", "after Enter, keyboard focus must be on the page content, not still on the link"
    pg.close()


def test_faq_works_from_the_keyboard(page, sessions):
    """Questions are reachable with Tab and open with Enter or Space (they used to respond to the mouse only)."""
    pg = _open(sessions, page)
    q = pg.locator(".faq-item .faq-q")
    if not q.count():
        pytest.skip("page has no click-to-open FAQ")
    first = q.first
    assert first.get_attribute("role") == "button" and first.get_attribute("tabindex") == "0"
    assert first.get_attribute("aria-expanded") == "false"
    first.focus()
    pg.keyboard.press("Enter")
    assert first.get_attribute("aria-expanded") == "true" and "open" in first.locator("xpath=..").get_attribute("class")
    pg.keyboard.press("Space")
    assert first.get_attribute("aria-expanded") == "false"
    pg.close()
