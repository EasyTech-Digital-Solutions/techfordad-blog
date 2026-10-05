"""Every page is accounted for: it has a kind, and sitemap.xml agrees with what is indexable."""
import re

import pages as P
import htmlutil as H


def test_every_html_file_has_a_kind():
    """A new type of page must be added to tests/pages.py, so the right checks are chosen for it on purpose."""
    unknown = [rel for rel, k in P.inventory().items() if k is None]
    assert not unknown, (
        "These pages match no rule in tests/pages.py. Add a rule (and think about which checks apply):\n  "
        + "\n  ".join(unknown))


def _sitemap_paths():
    xml = (P.ROOT / "sitemap.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
    return urls


def test_sitemap_urls_all_exist():
    missing = []
    for url in _sitemap_paths():
        assert url.startswith("https://www.techfordad.com/"), f"sitemap URL not on the canonical host: {url}"
        rel = url.removeprefix("https://www.techfordad.com/") or "index.html"
        if not (P.ROOT / rel).is_file():
            missing.append(url)
    assert not missing, "sitemap.xml lists pages that do not exist:\n  " + "\n  ".join(missing)


def test_sitemap_has_no_duplicates():
    urls = _sitemap_paths()
    dupes = sorted({u for u in urls if urls.count(u) > 1})
    assert not dupes, f"duplicate sitemap entries: {dupes}"


def test_indexable_pages_are_in_the_sitemap():
    listed = {u.removeprefix("https://www.techfordad.com/") or "index.html" for u in _sitemap_paths()}
    inv = P.inventory()
    missing = [rel for rel, k in inv.items()
               if k in {"home", "hub", "article-us", "article-ca", "gift-guide", "guide", "info"}
               and not P.is_noindex(rel) and rel not in listed]
    assert not missing, "indexable pages missing from sitemap.xml (add them, or mark them noindex):\n  " + "\n  ".join(missing)


def test_noindex_pages_are_not_in_the_sitemap():
    listed = {u.removeprefix("https://www.techfordad.com/") or "index.html" for u in _sitemap_paths()}
    wrong = [rel for rel in P.all_html() if rel in listed and (P.is_noindex(rel) or P.kind(rel) in {"stub", "admin", "error"})]
    assert not wrong, "noindex/redirect pages must not be in sitemap.xml:\n  " + "\n  ".join(wrong)


def test_redirect_stubs_are_well_formed():
    """Old URLs: noindex, a canonical pointing at the target, a working target, and a JS fallback."""
    problems = []
    for rel, k in P.inventory().items():
        if k != "stub":
            continue
        text = P.read(rel)
        m = re.search(r'http-equiv="refresh"\s+content="\d+;\s*url=([^"]+)"', text)
        if not m:
            problems.append(f"{rel}: refresh meta has no url")
            continue
        target = m.group(1).removeprefix("https://www.techfordad.com").lstrip("/") or "index.html"
        if not (P.ROOT / target).is_file():
            problems.append(f"{rel}: redirects to missing page {target}")
        if not P.is_noindex(rel):
            problems.append(f"{rel}: stub is not noindex")
        doc = H.parse(rel)
        if doc.canonical() != P.public_url(target):
            problems.append(f"{rel}: canonical ({doc.canonical()}) should be the redirect target {P.public_url(target)}")
    assert not problems, "\n".join(problems)
