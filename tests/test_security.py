"""Security and privacy hygiene for a static site: what is published, what is loaded, and what must never be committed."""
import json
import re
import subprocess
from urllib.parse import urlparse

import pytest

import pages as P
import htmlutil as H

DATA = P.ROOT / "tests" / "data"
KNOWN = json.loads((DATA / "known_issues.json").read_text(encoding="utf-8"))
THIRD = json.loads((DATA / "third_party_hosts.json").read_text(encoding="utf-8"))


def _tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=P.ROOT, capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if (P.ROOT / f).is_file()]


# ------------------------------------------------------------------ what gets published

def _excluded_from_pages():
    text = (P.ROOT / "_config.yml").read_text(encoding="utf-8")
    block = re.search(r"^exclude:\s*\n((?:\s+-.*\n?)+)", text, re.M)
    return {re.sub(r"\s*#.*", "", line).strip().lstrip("- ").strip() for line in block.group(1).splitlines()} if block else set()


def test_internal_files_are_not_published():
    """GitHub Pages publishes everything not excluded in _config.yml. New top-level items must be a conscious choice."""
    public = set(json.loads((DATA / "public_top_level.json").read_text(encoding="utf-8"))["public"])
    excluded = _excluded_from_pages()
    top = {f.split("/")[0] for f in _tracked_files()}
    # Jekyll skips names starting with "_" or "." by itself (except .well-known, which is listed explicitly).
    candidates = {t for t in top if not t.startswith(("_", ".")) or t == ".well-known"}
    exposed = sorted(candidates - excluded - public)
    assert not exposed, (
        "These top-level files/folders would be PUBLISHED on techfordad.com but are not on the allowlist.\n"
        "If they are internal, add them to `exclude:` in _config.yml. If they are meant to be public, add them to tests/data/public_top_level.json.\n  "
        + "\n  ".join(exposed))


def test_public_allowlist_has_no_stale_entries():
    public = set(json.loads((DATA / "public_top_level.json").read_text(encoding="utf-8"))["public"])
    top = {f.split("/")[0] for f in _tracked_files()}
    assert not (public - top), f"allowlist names that no longer exist: {sorted(public - top)}"


@pytest.mark.parametrize("name", ["admin", "scripts", "docs", "tests", "CLAUDE.md", "newsletter-log.json"])
def test_internal_items_are_excluded_from_publishing(name):
    assert name in _excluded_from_pages(), f"{name} must stay in the `exclude:` list in _config.yml"


def test_admin_page_is_hidden_from_search_and_has_no_secrets():
    text = P.read("admin/index.html")
    assert re.search(r'name="robots"\s+content="[^"]*noindex[^"]*nofollow', text), "admin page must be noindex,nofollow"
    assert not re.search(r"github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{30,}|sk-ant-[A-Za-z0-9_-]{20,}", text), "admin page contains a token"


# ------------------------------------------------------------------ what the pages load

def test_no_insecure_http_resources(html_page):
    bad = [f"<{t} {a}={u}>" for t, a, u in H.parse(html_page).base_resources if u.startswith("http://")]
    assert not bad, f"insecure (http://) resources, blocked as mixed content on an https page: {bad}"


def test_third_party_scripts_are_allowlisted(html_page):
    if P.kind(html_page) == "admin":
        pytest.skip("local tool")
    doc = H.parse(html_page)
    problems = []
    for s in doc.scripts:
        src = s.get("src", "")
        host = urlparse(src).hostname if src.startswith(("http", "//")) else None
        if host and host not in THIRD["script"]:
            problems.append(f"script from {host} ({src[:70]})")
    for l in doc.links:
        href = l.get("href", "")
        host = urlparse(href).hostname if href.startswith(("http", "//")) else None
        if host and "stylesheet" in l.get("rel", "") and host not in THIRD["stylesheet"]:
            problems.append(f"stylesheet from {host}")
    for f in doc.iframes:
        problems.append(f"iframe {f.get('src', '')[:70]} (none are allowed today)")
    for f in doc.forms:
        host = urlparse(f.get("action", "")).hostname
        if host and host not in THIRD["form_action"]:
            problems.append(f"form posts to {host}")
        if f.get("action", "").startswith("http://"):
            problems.append("form posts over http://")
    assert not problems, "not on tests/data/third_party_hosts.json (decide deliberately, then add it):\n  " + "\n  ".join(problems)


def test_inline_event_handlers_only_where_known():
    """onclick= and friends block a strict Content-Security-Policy. The two known pages are tracked; new ones fail."""
    found = sorted(rel for rel in P.all_html() if P.kind(rel) != "admin" and H.parse(rel).elements_with_inline_handlers)
    known = sorted(KNOWN["inline_event_handlers"])
    new, fixed = sorted(set(found) - set(known)), sorted(set(known) - set(found))
    assert not new, f"new inline event handlers (use addEventListener in js/main.js): {new}"
    assert not fixed, f"fixed! delete these from tests/data/known_issues.json -> inline_event_handlers: {fixed}"


def test_no_javascript_urls(html_page):
    bad = [a["href"] for a in H.parse(html_page).anchors if a.get("href", "").strip().lower().startswith("javascript:")]
    assert not bad, f"javascript: links: {bad}"


# ------------------------------------------------------------------ our own JavaScript and CSS

JS_FILES = sorted(p.relative_to(P.ROOT).as_posix() for p in (P.ROOT / "js").glob("*.js"))


@pytest.mark.parametrize("path", JS_FILES, ids=JS_FILES)
def test_js_avoids_dangerous_apis(path):
    text = P.read(path)
    code = re.sub(r"/\*.*?\*/", "", text, flags=re.S)       # block comments
    code = re.sub(r"(?m)(^|\s)//.*$", "", code)               # line comments (needs a space before //, so https:// is safe)
    bad = [p for p in (r"\beval\s*\(", r"new\s+Function\s*\(", r"document\.write\s*\(", r"\.innerHTML\s*=", r"\.outerHTML\s*=", r"insertAdjacentHTML") if re.search(p, code)]
    assert not bad, f"{path} uses {bad}: build DOM nodes with textContent/createElement instead"


def test_published_inline_scripts_avoid_dangerous_apis(html_page):
    if P.kind(html_page) == "admin":
        pytest.skip("local tool")
    bad = sorted({p for s in H.parse(html_page).inline_scripts for p in ("eval(", "new Function", "document.write(", ".innerHTML") if p in s})
    assert not bad, f"inline script uses {bad}"


def test_no_insecure_urls_in_css_or_js():
    bad = []
    for path in [*JS_FILES, "css/style.css"]:
        for m in re.finditer(r"http://[^\s\"')]+", P.read(path)):
            if "www.w3.org" in m.group(0):  # SVG namespace, not a request
                continue
            bad.append(f"{path}: {m.group(0)[:60]}")
    assert not bad, "\n".join(bad)


# ------------------------------------------------------------------ secrets and repo settings

SECRET_PATTERNS = {
    "GitHub token": r"\bgh[pousr]_[A-Za-z0-9]{30,}\b|github_pat_[A-Za-z0-9_]{30,}",
    "Anthropic API key": r"sk-ant-[A-Za-z0-9_-]{30,}",
    "AWS access key": r"\bAKIA[0-9A-Z]{16}\b",
    "private key": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "Slack token": r"\bxox[baprs]-[A-Za-z0-9-]{20,}",
    "Mailchimp API key": r"\b[0-9a-f]{32}-us\d{1,2}\b",
    "Google API key": r"\bAIza[0-9A-Za-z_-]{35}\b",
}
TEXT_SUFFIXES = {".html", ".js", ".json", ".css", ".md", ".py", ".yml", ".yaml", ".txt", ".xml", ".ini", ".cfg", ".toml", ".sh"}


def test_no_secrets_committed():
    hits = []
    for rel in _tracked_files():
        if not any(rel.endswith(s) for s in TEXT_SUFFIXES):
            continue
        text = (P.ROOT / rel).read_text(encoding="utf-8", errors="replace")
        for name, pat in SECRET_PATTERNS.items():
            if re.search(pat, text):
                hits.append(f"{rel}: looks like a {name}")
    assert not hits, "possible secrets in the repo (rotate them, then remove):\n  " + "\n  ".join(hits)


def test_cname_and_robots():
    assert P.read("CNAME").strip() == "www.techfordad.com"
    robots = P.read("robots.txt")
    assert "Sitemap: https://www.techfordad.com/sitemap.xml" in robots


def test_robots_does_not_block_noindex_stubs():
    """A page blocked in robots.txt cannot be crawled, so Google never sees its noindex tag and may keep the URL indexed.
    Every old stub (meta refresh + noindex) must stay crawlable."""
    disallowed = [line.split(":", 1)[1].strip() for line in P.read("robots.txt").splitlines() if line.lower().startswith("disallow:")]
    stubs = [rel for rel, kind in P.inventory().items() if kind == "stub"]
    blocked = [rel for rel in stubs for d in disallowed if d and ("/" + rel).startswith(d)]
    assert not blocked, f"robots.txt blocks pages that rely on a noindex tag: {blocked[:5]}"


WORKFLOWS = sorted((P.ROOT / ".github" / "workflows").glob("*.yml"))


@pytest.mark.parametrize("wf", WORKFLOWS, ids=[w.name for w in WORKFLOWS])
def test_workflow_hardening(wf):
    text = wf.read_text(encoding="utf-8")
    assert "pull_request_target" not in text, "pull_request_target runs untrusted code with secrets; avoid it"
    assert re.search(r"^\s*permissions:", text, re.M), "declare minimal `permissions:` (default token rights are broad)"
    for line in text.splitlines():
        m = re.match(r"\s*-?\s*uses:\s*([^\s@]+)@(\S+)", line)
        if m and not m.group(1).startswith("./"):
            assert re.fullmatch(r"[0-9a-f]{40}", m.group(2)), f"action {m.group(1)} is not pinned to a commit SHA: @{m.group(2)}"


def test_security_txt_has_not_expired():
    """/.well-known/security.txt says when to stop trusting it. Renew it before the date, or researchers see a dead contact."""
    from datetime import datetime, timedelta, timezone

    text = (P.ROOT / ".well-known" / "security.txt").read_text(encoding="utf-8")
    m = re.search(r"^Expires:\s*(\S+)", text, re.M)
    assert m, "security.txt has no Expires: line (the standard requires one)"
    expires = datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
    assert expires > datetime.now(timezone.utc) + timedelta(days=30), (
        f"security.txt expires {expires:%Y-%m-%d}: renew the Expires: line now (the test fails 30 days ahead)")
    assert "Contact:" in text


def test_well_known_folder_is_opted_in_to_publishing():
    """Jekyll skips dot-folders by default, so /.well-known/security.txt is only served if _config.yml `include:`s it."""
    config = (P.ROOT / "_config.yml").read_text(encoding="utf-8")
    assert re.search(r"^include:\s*\n(?:\s+-.*\n)*?\s+-\s*\.well-known\b", config, re.M), (
        "_config.yml must have `include:` with `- .well-known`, otherwise security.txt returns 404 on the live site")
