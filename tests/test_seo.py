"""Per-page basics a search engine and a screen reader both rely on (no browser needed)."""
import pytest

import pages as P
import htmlutil as H

NOT_CONTENT = {"stub", "admin"}


def _skip_if_not_content(rel):
    if P.kind(rel) in NOT_CONTENT:
        pytest.skip(f"{P.kind(rel)} page")


def test_page_is_well_formed(html_page):
    """No unclosed or stray tags (these are the mistakes hand-edited HTML collects)."""
    doc = H.parse(html_page)
    assert not doc.errors, "\n".join(doc.errors[:8])


def test_no_duplicate_ids(html_page):
    ids = H.parse(html_page).ids
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate id values (anchors and scripts will pick the wrong element): {dupes}"


def test_title_and_description(html_page):
    _skip_if_not_content(html_page)
    doc = H.parse(html_page)
    title = doc.title.strip()
    assert title, "missing <title>"
    desc = doc.meta("description", "content")
    if P.kind(html_page) != "error":
        assert desc and desc.strip(), "missing meta description"
        assert len(desc) <= 160, f"meta description is {len(desc)} chars (limit 160)"
    assert len(title) <= 60, f"title is {len(title)} chars (limit 60): {title!r}"


def test_exactly_one_h1(html_page):
    _skip_if_not_content(html_page)
    assert H.parse(html_page).h1 == 1, f"expected one <h1>, found {H.parse(html_page).h1}"


def test_language_matches_market(html_page):
    _skip_if_not_content(html_page)
    lang = H.parse(html_page).lang
    if P.kind(html_page) == "article-ca":
        assert lang == "en-CA", f'Canada pages must use lang="en-CA", found {lang!r}'
    else:
        assert lang in ("en", "en-US"), f'expected lang="en", found {lang!r}'


def test_viewport_meta(html_page):
    if P.kind(html_page) == "stub":
        pytest.skip("redirect stub")
    assert H.parse(html_page).meta("viewport", "content"), 'missing <meta name="viewport"> (page would not scale on phones)'


def test_canonical_url(html_page):
    _skip_if_not_content(html_page)
    doc = H.parse(html_page)
    canon = doc.canonical()
    assert canon, "missing canonical link"
    if not P.is_noindex(html_page) and P.kind(html_page) != "error":
        assert canon == P.public_url(html_page), f"canonical {canon} should be {P.public_url(html_page)}"


def test_social_tags(html_page):
    if P.kind(html_page) not in {"home", "hub", "article-us", "article-ca", "gift-guide", "guide", "info"}:
        pytest.skip("page type has no social card")
    doc = H.parse(html_page)
    for prop in ("og:title", "og:description", "og:image", "og:url"):
        assert doc.meta(prop, "content", attr="property"), f"missing {prop}"
    image = doc.meta("og:image", "content", attr="property")
    local = image.removeprefix("https://www.techfordad.com/")
    assert (P.ROOT / local).is_file(), f"og:image points at a file that does not exist: {image}"


def test_images_have_alt_text(html_page):
    _skip_if_not_content(html_page)
    missing = [i.get("src") for i in H.parse(html_page).images if "alt" not in i]
    assert not missing, f"images without an alt attribute (use alt=\"\" for decorative ones): {missing[:5]}"


def test_local_assets_exist(html_page):
    """Every local image, stylesheet, script and icon the page asks for is in the repo."""
    if P.kind(html_page) == "admin":
        pytest.skip("local tool")
    doc = H.parse(html_page)
    base = (P.ROOT / html_page).parent
    missing = []
    for tag, attr, url in doc.base_resources:
        if not url or url.startswith(("http:", "https:", "//", "data:", "#", "mailto:", "tel:")):
            continue
        clean = url.split("?")[0].split("#")[0]
        target = (P.ROOT / clean.lstrip("/")) if clean.startswith("/") else (base / clean)
        if clean and not target.resolve().exists():
            missing.append(f"<{tag} {attr}={url}>")
    assert not missing, "references to files that do not exist:\n  " + "\n  ".join(missing)
