"""Shared test setup: a local web server for the site, a real browser, and cached per-page reports.

How the browser tests work
    * The repo folder is served on a random local port, exactly as GitHub Pages would serve it.
    * Requests to other websites (Google Tag Manager, Amazon, ...) are answered with empty files, so
      the tests run offline and never send fake analytics hits. The hosts that were requested are
      recorded and checked against an allowlist in test_security.py.
    * Each page is loaded once per viewport (desktop and phone) and measured; the individual tests
      then read that report. This keeps a full run to a couple of minutes.

Options
    --quick   one page of each kind instead of every page (a fast check while you work)
    --live    also run tests/test_live_site.py against https://www.techfordad.com
"""
from __future__ import annotations

import functools
import http.server
import socketserver
import threading
from pathlib import Path

import pytest

import pages as P

ROOT = P.ROOT

VIEWPORTS = {
    "desktop": dict(viewport={"width": 1280, "height": 900}),
    "mobile": dict(
        viewport={"width": 390, "height": 844},
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True,
        user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
                    "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"),
    ),
}
GIF = bytes.fromhex("47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b")


def pytest_addoption(parser):
    parser.addoption("--quick", action="store_true", help="test one page of each kind only")
    parser.addoption("--live", action="store_true", help="also run the live-site checks (needs network)")
    parser.addoption("--update-baseline", action="store_true",
                     help="rewrite tests/data/a11y_known_issues.json from what axe finds now (review the diff before committing!)")


def pytest_configure(config):
    config.addinivalue_line("markers", "live: needs network")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--live"):
        return
    skip = pytest.mark.skip(reason="live-site checks are opt-in: pass --live")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)


def _ui_pages(config) -> list[str]:
    inv = P.inventory()
    pages = [rel for rel, k in inv.items() if k in P.CONTENT_KINDS]
    if config.getoption("--quick"):
        seen, picked = set(), []
        for rel in pages:
            if inv[rel] not in seen:
                seen.add(inv[rel])
                picked.append(rel)
        return picked
    return pages


def pytest_generate_tests(metafunc):
    """Tests that take `page` run for every content page; `html_page` for every HTML file; `viewport` for both sizes."""
    if "page" in metafunc.fixturenames:
        pages = _ui_pages(metafunc.config)
        if "toolbar_page" in metafunc.fixturenames:
            pages = [p for p in pages if P.has_toolbar(p)]
        metafunc.parametrize("page", pages, ids=pages)
    if "sample_page" in metafunc.fixturenames:  # one page of each kind, for checks that do not vary by page
        inv = P.inventory()
        seen, sample = set(), []
        for rel, k in inv.items():
            if k in P.CONTENT_KINDS and k not in seen:
                seen.add(k)
                sample.append(rel)
        metafunc.parametrize("sample_page", sample, ids=sample)
    if "html_page" in metafunc.fixturenames:
        pages = P.all_html()
        metafunc.parametrize("html_page", pages, ids=pages)
    if "viewport" in metafunc.fixturenames:
        metafunc.parametrize("viewport", list(VIEWPORTS), ids=list(VIEWPORTS))


@pytest.fixture
def toolbar_page():  # marker fixture: restricts `page` to pages that carry the print/share toolbar
    return True


# ---------------------------------------------------------------- local server

class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep test output readable
        pass


@pytest.fixture(scope="session")
def site_url():
    handler = functools.partial(_Quiet, directory=str(ROOT))
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    # The default backlog is 5 pending connections; a page with dozens of images (the blog index) can overrun it, and a
    # dropped connection looks like a broken image. 128 is plenty and removes that flake.
    socketserver.ThreadingTCPServer.request_queue_size = 128
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


# ---------------------------------------------------------------- browser

@pytest.fixture(scope="session")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch(channel="chrome")  # the Chrome already installed on a laptop
        except Exception:
            b = pw.chromium.launch()  # CI: the browser installed by `playwright install chromium`
        yield b
        b.close()


class Session:
    """One browser context (desktop or phone) with external requests stubbed out."""

    def __init__(self, browser, base: str, viewport: str):
        self.base = base
        self.external: list[str] = []
        self.ctx = browser.new_context(**VIEWPORTS[viewport])
        self.ctx.route("**/*", self._route)

    def _route(self, route):
        url = route.request.url
        if url.startswith(self.base) or url.startswith(("data:", "blob:", "about:")):
            return route.continue_()
        self.external.append(url)
        kind = route.request.resource_type
        if kind == "script":
            return route.fulfill(status=200, content_type="text/javascript", body="")
        if kind == "image":
            return route.fulfill(status=200, content_type="image/gif", body=GIF)
        if kind == "stylesheet":
            return route.fulfill(status=200, content_type="text/css", body="")
        return route.fulfill(status=200, body="")

    def open(self, rel: str, init: str | None = None):
        """Open a page and return (page, console_messages, page_errors, failed_local_responses).

        `init` is JavaScript that runs before the page's own scripts (used to stub navigator.share or window.print).
        """
        pg = self.ctx.new_page()
        if init:
            pg.add_init_script(init)
        console, errors, failed = [], [], []
        pg.on("console", lambda m: console.append((m.type, m.text)))
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("response", lambda r: failed.append((r.status, r.url)) if r.url.startswith(self.base) and r.status >= 400 else None)
        pg.on("requestfailed", lambda r: failed.append((0, r.url)) if r.url.startswith(self.base) else None)
        pg.goto(f"{self.base}/{rel}", wait_until="load")
        # scroll through the page so lazy-loaded images actually load
        pg.evaluate("""async () => {
            const step = Math.max(400, innerHeight * 0.8);
            for (let y = 0; y < document.documentElement.scrollHeight; y += step) { scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); }
            scrollTo(0, 0);
        }""")
        try:  # let the images that scrolling just triggered finish loading before anything is measured
            pg.wait_for_load_state("networkidle", timeout=4000)
        except Exception:
            pass
        pg.wait_for_timeout(150)
        return pg, console, errors, failed


@pytest.fixture(scope="session")
def sessions(browser, site_url):
    made: dict[str, Session] = {}

    def get(viewport: str) -> Session:
        if viewport not in made:
            made[viewport] = Session(browser, site_url, viewport)
        return made[viewport]

    yield get
    for s in made.values():
        s.ctx.close()


# ---------------------------------------------------------------- per-page report (measured once)

MEASURE_JS = (Path(__file__).parent / "measure.js").read_text(encoding="utf-8")
_reports: dict[tuple[str, str], dict] = {}


@pytest.fixture
def report(page, viewport, sessions):
    """Everything measured on one page at one viewport. Computed once, shared by every test that asks."""
    key = (page, viewport)
    if key not in _reports:
        sess = sessions(viewport)
        pg, console, errors, failed = sess.open(page)
        data = pg.evaluate(MEASURE_JS)
        data.update(console=console, pageErrors=errors, failedLocal=failed, external=list(sess.external))
        pg.close()
        _reports[key] = data
    return _reports[key]
