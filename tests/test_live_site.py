"""Checks against the PUBLISHED site (https://www.techfordad.com). Opt in with:  pytest --live

These catch what no repo test can: the site being down, an expired certificate, a security header dropped by
Cloudflare, an internal file accidentally published, or a deploy that never reached visitors.
Run them after merging to main (a feature branch is not published yet).
"""
import concurrent.futures
import re
import socket
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone

import pytest

import pages as P

pytestmark = pytest.mark.live
SITE = "https://www.techfordad.com"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def fetch(url: str, method: str = "GET"):
    """Return (status, headers dict lower-cased, body bytes). Does not follow redirects."""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "techfordad-test-suite"})
    try:
        with _opener.open(req, timeout=20) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read()


def sitemap_urls():
    xml = (P.ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)


def test_every_sitemap_url_is_up():
    urls = sitemap_urls()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda u: (u, fetch(u)[0]), urls))
    bad = [(u, s) for u, s in results if s != 200]
    assert not bad, f"pages that are not returning 200: {bad}"


@pytest.mark.parametrize("path", ["robots.txt", "sitemap.xml", "ads.txt", ".well-known/security.txt", "favicon.svg", "css/style.css", "js/main.js"])
def test_support_files_are_published(path):
    status, _, body = fetch(f"{SITE}/{path}")
    assert status == 200 and body, f"/{path} returned {status}"


def test_http_redirects_to_https():
    status, headers, _ = fetch("http://www.techfordad.com/")
    assert status in (301, 308) and headers.get("location", "").startswith("https://www.techfordad.com"), (status, headers.get("location"))


def test_bare_domain_redirects_to_www():
    status, headers, _ = fetch("https://techfordad.com/")
    assert status in (301, 308) and headers.get("location", "").startswith("https://www.techfordad.com"), (status, headers.get("location"))


def test_unknown_page_returns_a_real_404():
    status, _, body = fetch(f"{SITE}/this-page-does-not-exist-xyz")
    assert status == 404, f"unknown URLs must return 404 (got {status}); a 200 would create soft-404s in search"
    assert b"Page Not Found" in body, "the custom 404 page is not being served"


@pytest.mark.parametrize("path", ["admin/", "admin/index.html", "scripts/products.json", "scripts/amazon-registry.json", "docs/",
                                  "tests/", "tests/test_security.py", "CLAUDE.md", "README.md", "newsletter-log.json",
                                  "_config.yml", "Gemfile", ".git/config", ".env", ".github/workflows/live-site-check.yml"])
def test_internal_files_are_not_published(path):
    status, _, _ = fetch(f"{SITE}/{path}")
    assert status == 404, f"/{path} is publicly reachable (HTTP {status})"


REQUIRED_HEADERS = {
    "strict-transport-security": "HSTS: browsers refuse plain http on this site",
    "x-content-type-options": "nosniff: stops browsers guessing file types",
    "referrer-policy": "limits what other sites learn from a click",
}


@pytest.mark.parametrize("header", list(REQUIRED_HEADERS))
def test_required_security_headers(header):
    _, headers, _ = fetch(f"{SITE}/")
    assert header in headers, f"missing {header}: {REQUIRED_HEADERS[header]}"
    if header == "strict-transport-security":
        assert int(re.search(r"max-age=(\d+)", headers[header]).group(1)) >= 15552000, "HSTS max-age should be at least 6 months"


def test_clickjacking_protection():
    _, headers, _ = fetch(f"{SITE}/")
    csp = headers.get("content-security-policy", "")
    assert "x-frame-options" in headers or "frame-ancestors" in csp, "pages can be framed by other sites (clickjacking)"


@pytest.mark.xfail(reason="Not set yet. Add in Cloudflare (Rules > Transform Rules > Modify Response Header). The site uses inline scripts "
                          "and Google tag/AdSense, so start with Content-Security-Policy-Report-Only.", strict=False)
@pytest.mark.parametrize("header", ["content-security-policy", "permissions-policy"])
def test_recommended_security_headers(header):
    _, headers, _ = fetch(f"{SITE}/")
    assert header in headers, f"{header} is not set"


def test_certificate_is_not_about_to_expire():
    ctx = ssl.create_default_context()
    with socket.create_connection(("www.techfordad.com", 443), timeout=20) as sock:
        with ctx.wrap_socket(sock, server_hostname="www.techfordad.com") as tls:
            cert = tls.getpeercert()
    expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    days = (expires - datetime.now(timezone.utc)).days
    assert days >= 14, f"TLS certificate expires in {days} days ({expires:%Y-%m-%d}); renewal normally happens automatically, so check Cloudflare"


def _on_main_branch():
    import os
    import subprocess

    ref = os.environ.get("GITHUB_REF_NAME") or subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=P.ROOT, capture_output=True, text=True).stdout.strip()
    return ref == "main"


def test_published_site_matches_the_repo():
    """The live pages load the same stylesheet version as the repo (catches a stalled deploy). Only meaningful on main."""
    import re as _re

    if not _on_main_branch():
        pytest.skip("only meaningful on main: a feature branch has not been published yet")

    version = _re.search(r'ASSET_VERSION = "(\d+)"', P.read("scripts/build_nav.py")).group(1)
    _, _, body = fetch(f"{SITE}/blog/best-tablets-for-seniors.html")
    live = _re.search(rb"css/style\.css\?v=(\d+)", body).group(1).decode()
    assert live == version, f"live pages use style.css?v={live} but the repo says {version}: not deployed yet (GitHub Pages takes a few minutes) or Pages is failing"
