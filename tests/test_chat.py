"""The "Ask TechForDad" chat: the floating button, the panel, answers with links to our articles, the search fallback
when the AI is unavailable, and that Google Analytics never receives the question text. The Worker itself is tested
with Node (worker/test/index.test.mjs); /api/chat is faked here, since it only exists on Cloudflare."""
import json
import re
import shutil
import subprocess
import sys

import pytest

import pages as P

ARTICLE = "blog/best-tablets-for-seniors.html"
CANADA = "blog/best-tablets-for-seniors-canada.html"
CHAT_ON = "try { localStorage.setItem('tfd-chat', 'on'); } catch (e) {}"  # same as conftest.py
GTAG_SPY = "window.__ga = []; window.gtag = function () { window.__ga.push(JSON.stringify([].slice.call(arguments))); };"


def test_worker_unit_tests():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed")
    run = subprocess.run([node, "--test", "worker/test/index.test.mjs"], cwd=P.ROOT, capture_output=True, text=True)
    assert run.returncode == 0, (run.stdout + run.stderr)[-2500:]


def test_chat_index_is_current():
    run = subprocess.run([sys.executable, "scripts/build_chat_index.py", "--check"],
                         cwd=P.ROOT, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr


def _chunks():
    sys.path.insert(0, str(P.ROOT / "scripts"))
    import build_chat_index
    return build_chat_index.build()


def test_chat_index_covers_every_live_article_and_nothing_else():
    index = json.loads(_chunks()[0])
    indexed = {p["u"].lstrip("/") for p in index["pages"]}
    expected = {rel for rel, kind in P.inventory().items()
                if kind in {"article-us", "article-ca", "gift-guide", "guide"} and not P.is_noindex(rel)}
    assert indexed == expected, f"missing: {sorted(expected - indexed)[:5]}, extra: {sorted(indexed - expected)[:5]}"
    for p in index["pages"]:
        assert p["c"] == ("CA" if P.kind(p["u"].lstrip("/")) == "article-ca" else p["c"]), p["u"]


def test_chunk_buttons_come_untagged_from_the_right_store():
    """Products in the chat index are the sections' own Check Price buttons, stored WITHOUT a tag (the Worker adds the
    tag for the page the chat is open on), from amazon.ca on Canada pages and amazon.com everywhere else."""
    _, chunks = _chunks()
    bad = []
    for c in chunks:
        for p in json.loads(c["products"]):
            store = "www.amazon.ca" if c["country"] == "CA" else "www.amazon.com"
            if "tag=" in p["url"] or not p["url"].startswith(f"https://{store}/") or not p["name"]:
                bad.append((c["id"], p))
    assert not bad, bad[:5]
    assert sum(c["products"] != "[]" for c in chunks) > 100, "product buttons are no longer picked up from the pages"


def test_chunks_are_clean_and_fit_vectorize():
    _, chunks = _chunks()
    assert len({c["id"] for c in chunks}) == len(chunks), "chunk ids must be unique"
    too_long = [c["id"] for c in chunks if len(c["id"].encode("utf-8")) > 64]
    assert not too_long, f"Vectorize ids are at most 64 bytes: {too_long[:3]}"
    for c in chunks:
        assert "Check Price on Amazon" not in c["text"], f"{c['id']}: button text leaked into the chunk"
        assert "As an Amazon Associate" not in c["text"], f"{c['id']}: footer text leaked into the chunk"
        assert len(json.dumps(c).encode("utf-8")) < 10_000, f"{c['id']}: over Vectorize's 10 KiB metadata limit"
        assert c["url"].startswith("/") and c["text"].strip(), c["id"]


def test_chat_uses_only_the_registered_affiliate_tags():
    """The Worker, the widget and the local preview may only use the three registered Associates tags (CLAUDE.md)."""
    worker = (P.ROOT / "worker/src/index.js").read_text(encoding="utf-8")
    widget = (P.ROOT / "js/chat.js").read_text(encoding="utf-8")
    preview = (P.ROOT / "scripts/chat_preview.py").read_text(encoding="utf-8")
    for name, text in (("worker/src/index.js", worker), ("js/chat.js", widget), ("scripts/chat_preview.py", preview)):
        tags = set(re.findall(r"['\"]([a-z0-9-]+-2\d)['\"]", text))
        assert tags == P.ALL_TAGS, f"{name} uses tags {sorted(tags)}; registered: {sorted(P.ALL_TAGS)}"


def test_worker_source_is_not_published():
    config = (P.ROOT / "_config.yml").read_text(encoding="utf-8")
    assert "  - worker" in config, "worker/ must be in _config.yml exclude:"


# ------------------------------------------------------------------ browser


def _open_chat(sessions, rel, viewport="desktop", api=None):
    pg, console, errors, failed = sessions(viewport).open(rel)
    pg.evaluate(GTAG_SPY)  # after load: the page's own Google tag snippet defines gtag
    sent = []

    def handle(route):
        body = json.loads(route.request.post_data or "{}")
        sent.append(body)
        if api is None:
            return route.fulfill(status=503, content_type="text/plain", body="")
        status, payload = api(body)
        route.fulfill(status=status, content_type="application/json", body=json.dumps(payload))

    pg.route("**/api/chat", handle)
    pg.route("**/api/chat/feedback", lambda r: r.fulfill(status=200, content_type="application/json", body='{"ok":true}'))
    pg.locator("#chat-launcher").click()
    pg.locator("#chat-panel").wait_for(state="visible")
    return pg, sent, errors


def _ask(pg, question):
    pg.locator("#chat-input").fill(question)
    pg.locator(".chat-send").click()
    pg.locator(".chat-msg-bot:not([aria-busy])").last.wait_for()


@pytest.mark.slow
def test_launcher_is_on_every_kind_of_page(sample_page, sessions):
    pg, *_ = sessions("mobile").open(sample_page)
    btn = pg.locator("#chat-launcher")
    assert btn.count() == 1 and btn.is_visible(), "the Ask TechForDad button is missing"
    box = btn.bounding_box()
    vw, vh = pg.evaluate("[innerWidth, innerHeight]")
    assert box["height"] >= 44, "button is too small to tap"
    assert box["x"] >= 0 and box["x"] + box["width"] <= vw and box["y"] + box["height"] <= vh, "button is off screen"
    badge = pg.locator(".country-badge-pill")
    if badge.count():
        b = badge.bounding_box()
        assert b["x"] + b["width"] <= box["x"], "the chat button overlaps the country badge"
    pg.close()


@pytest.mark.slow
def test_chat_answers_from_the_worker_with_site_links(sessions):
    def api(body):
        return 200, {"id": "t1", "mode": "ai", "answer": "TechForDad recommends the iPad.\n- Big screen\n- Simple to use",
                     "sources": [{"title": "Best Tablets for Seniors", "url": "/blog/best-tablets-for-seniors.html#ipad"},
                                 {"title": "Bad", "url": "https://evil.example/"}],
                     "products": [{"name": "Apple iPad (11th Generation)", "url": "https://www.amazon.com/dp/B0IPAD?tag=techfordad0b-20"},
                                  {"name": "Made-up tag", "url": "https://www.amazon.com/dp/B0X?tag=techfordad-ca-20"},
                                  {"name": "Other store", "url": "https://evil.example/dp/B0X?tag=techfordad0b-20"}]}

    pg, sent, errors = _open_chat(sessions, ARTICLE, api=api)
    _ask(pg, "Which tablet is easiest for my mom?")
    bot = pg.locator(".chat-msg-bot").last
    assert "recommends the iPad" in bot.inner_text()
    assert bot.locator(".chat-list li").count() == 2, "dash lines should become a list"
    links = bot.locator(".chat-sources a")
    assert links.count() == 1, "only links to our own pages are shown"
    assert links.first.get_attribute("href") == "/blog/best-tablets-for-seniors.html", "articles open at the top, not mid-page"
    assert sent[0]["country"] == "US" and sent[0]["page"] == "/" + ARTICLE and sent[0]["history"] == []

    buy = bot.locator("a.chat-buy")
    assert buy.count() == 1, "only registered tags on amazon.com/.ca become buttons"
    assert buy.get_attribute("href") == "https://www.amazon.com/dp/B0IPAD?tag=techfordad0b-20"
    assert buy.get_attribute("rel") == "sponsored noopener" and buy.get_attribute("target") == "_blank"
    assert "Check Price on Amazon" in buy.inner_text() and buy.bounding_box()["height"] >= 44
    assert "As an Amazon Associate I earn from qualifying purchases." in bot.inner_text()
    pg.evaluate("addEventListener('click', e => { if (e.target.closest('a.chat-buy')) e.preventDefault(); }, true)")
    buy.click()
    clicks = [c for c in pg.evaluate("window.__ga") if "amazon_affiliate_click" in c]
    assert clicks and '"cta_location":"chat"' in clicks[0] and "Apple iPad" in clicks[0], clicks

    bot.locator(".chat-fb").first.click()
    assert "Thanks" in bot.locator(".chat-feedback").inner_text()

    _ask(pg, "And the cheaper one?")
    assert [t["role"] for t in sent[1]["history"]] == ["user", "assistant"], "follow-ups carry the conversation"
    ga = " ".join(pg.evaluate("window.__ga"))
    assert "chat_question" in ga and "chat_answer" in ga and "chat_feedback" in ga
    assert "easiest for my mom" not in ga and "cheaper one" not in ga, "question text must never go to Google Analytics"
    assert not errors
    pg.close()


@pytest.mark.slow
def test_chat_falls_back_to_article_search_when_the_ai_is_unavailable(sessions):
    pg, sent, errors = _open_chat(sessions, CANADA)  # /api/chat answers 503
    _ask(pg, "hearing aids")
    bot = pg.locator(".chat-msg-bot").last
    assert "resting" in bot.inner_text()
    hrefs = [a.get_attribute("href") for a in bot.locator(".chat-sources a").all()]
    assert hrefs and all(h.startswith("/") for h in hrefs), hrefs
    assert "hearing-aids-canada" in hrefs[0], f"a Canada page should prefer the Canada article: {hrefs}"
    assert sent[0]["country"] == "CA"
    assert not errors
    pg.close()


@pytest.mark.slow
def test_conversation_follows_the_reader_to_the_next_page(browser, site_url):
    """Kept in sessionStorage: same tab keeps it across pages (same session id, follow-ups still work); a new tab starts fresh."""
    answer = {"id": "t1", "mode": "ai", "answer": "TechForDad recommends the iPad.",
              "sources": [{"title": "Best Tablets", "url": "/blog/best-tablets-for-seniors.html"}],
              "products": [{"name": "Apple iPad (11th Generation)", "url": "https://www.amazon.com/dp/B0IPAD?tag=techfordad0b-20"}]}
    sent = []

    def handle(route):
        sent.append(json.loads(route.request.post_data))
        route.fulfill(status=200, content_type="application/json", body=json.dumps(answer))

    ctx = browser.new_context()
    ctx.add_init_script(CHAT_ON)
    ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(site_url) else r.fulfill(status=200, body=""))
    ctx.route("**/api/chat", handle)
    pg = ctx.new_page()
    pg.goto(f"{site_url}/{ARTICLE}")
    pg.locator("#chat-launcher").click()
    _ask(pg, "Which tablet is easiest?")
    pg.goto(f"{site_url}/index.html")
    assert pg.locator("#chat-panel").count() == 0, "the panel should not pop open on the next page"
    pg.locator("#chat-launcher").click()
    pg.locator("#chat-panel").wait_for(state="visible")
    assert pg.locator(".chat-msg-user").all_inner_texts() == ["Which tablet is easiest?"]
    assert pg.locator("a.chat-buy").count() == 1, "the Check Price button comes back too"
    assert pg.locator(".chat-starters").is_hidden()
    _ask(pg, "And the cheaper one?")
    assert sent[1]["session"] == sent[0]["session"], "one session id across pages"
    assert [t["role"] for t in sent[1]["history"]] == ["user", "assistant"]

    other = ctx.new_page()  # a new tab has its own sessionStorage
    other.goto(f"{site_url}/index.html")
    other.locator("#chat-launcher").click()
    other.locator("#chat-panel").wait_for(state="visible")
    assert other.locator(".chat-msg").count() == 0
    ctx.close()


@pytest.mark.slow
def test_soft_launch_shows_the_button_only_after_chat_on(browser, site_url):
    """Until CHAT_FOR_EVERYONE is true in js/main.js, visitors see no button; ?chat=on turns it on for that browser
    (kept across pages and visits) and ?chat=off turns it off again."""
    if re.search(r"const CHAT_FOR_EVERYONE = true", (P.ROOT / "js/main.js").read_text(encoding="utf-8")):
        pytest.skip("the chat is launched for everyone")
    ctx = browser.new_context()  # no CHAT_ON: a normal visitor
    ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(site_url) else r.fulfill(status=200, body=""))
    pg = ctx.new_page()
    pg.goto(f"{site_url}/{ARTICLE}")
    assert pg.locator("#chat-launcher").count() == 0, "visitors must not see the chat during the soft launch"
    pg.goto(f"{site_url}/{ARTICLE}?chat=on")
    assert pg.locator("#chat-launcher").is_visible()
    pg.goto(f"{site_url}/index.html")
    assert pg.locator("#chat-launcher").is_visible(), "?chat=on should be remembered on the next page"
    pg.goto(f"{site_url}/index.html?chat=off")
    assert pg.locator("#chat-launcher").count() == 0
    pg.goto(f"{site_url}/{ARTICLE}")
    assert pg.locator("#chat-launcher").count() == 0, "?chat=off should be remembered too"
    ctx.close()


@pytest.mark.slow
def test_chat_closes_with_escape_and_returns_focus(sessions):
    pg, *_ = _open_chat(sessions, "index.html")
    assert pg.evaluate("document.activeElement.id") == "chat-input", "typing box should get focus on open"
    assert not pg.locator("#chat-launcher").is_visible(), "button hides while the panel is open"
    pg.keyboard.press("Escape")
    assert pg.locator("#chat-panel").is_hidden()
    assert pg.evaluate("document.activeElement.id") == "chat-launcher"
    pg.close()


@pytest.mark.slow
@pytest.mark.parametrize("size", ["desktop", "mobile"])
def test_chat_panel_fits_the_screen(sessions, size):
    pg, *_ = _open_chat(sessions, ARTICLE, size)
    r = pg.evaluate("""() => { const b = document.getElementById('chat-panel').getBoundingClientRect();
        return {l: b.left, r: b.right, t: b.top, b: b.bottom, vw: innerWidth, vh: innerHeight,
                doc: document.documentElement.scrollWidth}; }""")
    assert r["l"] >= 0 and r["r"] <= r["vw"] + 0.5 and r["t"] >= 0 and r["b"] <= r["vh"] + 0.5, r
    assert r["doc"] <= r["vw"] + 1, "the panel makes the page scroll sideways"
    small = pg.evaluate("""() => [...document.querySelectorAll('#chat-panel button, #chat-input')]
        .filter(e => e.offsetParent && e.getBoundingClientRect().height < 44).map(e => e.className)""")
    assert not small, f"controls under 44px tall: {small}"
    pg.close()
