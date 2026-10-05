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


def test_has_main_landmark_and_skip_link(html_page):
    """Screen-reader and keyboard users jump straight to <main>; every page needs one landmark and a working skip link."""
    _skip_if_not_content(html_page)
    text = P.read(html_page)
    assert len(__import__("re").findall(r"<main\b", text)) == 1, "page needs exactly one <main> landmark"
    assert '<main id="main"' in text, '<main> needs id="main" (the skip link points at it)'
    skip = text.find('class="skip-link" href="#main"')
    assert 0 < skip < text.find("<header"), "the 'Skip to main content' link must be the first thing in <body>, before the header"
    assert text.find("<main") < text.find("<footer") and text.find("</main>") < text.find("<footer"), "<main> must end before the footer"


# ---------------------------------------------------------------- social cards and structured data (added in the 2026-10-05 sweep)

CARD_KINDS = {"home", "hub", "article-us", "article-ca", "gift-guide", "guide", "info"}
ARTICLE_KINDS = {"article-us", "article-ca", "gift-guide", "guide"}


def _indexable(rel, kinds):
    if P.kind(rel) not in kinds or P.is_noindex(rel):
        pytest.skip("page type or noindex page: no social card or article schema")


def test_social_card_is_complete(html_page):
    """Facebook, LinkedIn, X and messaging apps ignore SVG share images and need the twitter tags to show a large card."""
    _indexable(html_page, CARD_KINDS)
    doc = H.parse(html_page)
    image = doc.meta("og:image", "content", attr="property")
    assert not image.lower().endswith(".svg"), f"og:image is an SVG ({image}); use a JPG or PNG"
    assert doc.meta("twitter:card", "content") == "summary_large_image", "twitter:card should be summary_large_image"
    for name in ("twitter:title", "twitter:description", "twitter:image"):
        assert doc.meta(name, "content"), f"missing {name}"
    assert doc.meta("twitter:image", "content") == image, "twitter:image should match og:image"


def test_article_schema_is_complete(html_page):
    """Google reads the Article block for the image, dates and who publishes the page."""
    _indexable(html_page, ARTICLE_KINDS)
    articles = [b for b in H.jsonld(html_page) if b.get("@type") == "Article"]
    assert len(articles) == 1, f"expected exactly one Article block, found {len(articles)}"
    art = articles[0]
    assert len(art["headline"]) <= 110, "Article headline over 110 characters"
    image = art.get("image", "")
    assert image and not image.lower().endswith(".svg"), "Article needs a JPG or PNG image"
    local = image.removeprefix("https://www.techfordad.com/")
    assert (P.ROOT / local).is_file(), f"Article image file does not exist: {image}"
    assert art["datePublished"] <= art["dateModified"], "datePublished is after dateModified"
    parent = art["publisher"].get("parentOrganization", {})
    assert parent.get("name") == "EasyTech Vancouver" and parent.get("sameAs"), "publisher should name EasyTech Vancouver with its profile links"


def test_product_list_is_not_merchant_markup(html_page):
    """TechForDad does not sell the products it reviews, so its structured data must not look like a merchant listing.
    Product / Offer markup (price, availability, shipping, returns, GTIN, product image) made Search Console report merchant-listing
    errors on a review site. The product list is a plain ItemList of names; see scripts/build_product_schema.py."""
    for block in H.jsonld(html_page):
        if block.get("@type") != "ItemList":
            continue
        for element in block["itemListElement"]:
            assert element.get("@type") == "ListItem" and element.get("name"), "product list items need a name"
            assert "item" not in element and "offers" not in element, f"{element.get('name')}: Product/Offer markup is not allowed (we are not the merchant)"
    text = P.read(html_page)
    assert '"@type": "Offer"' not in text and '"@type": "Product"' not in text, "Offer/Product structured data found on the page"
    assert "schema.org/InStock" not in text, "availability markup claims stock we cannot verify"


def test_faq_schema_matches_the_visible_faq(html_page):
    """FAQ structured data must match what a visitor can open (the generator writes it, but a hand edit can break it)."""
    import html as htmllib
    import re

    if P.kind(html_page) not in ARTICLE_KINDS | {"hub"}:
        pytest.skip("page type has no FAQ")
    blocks = [b for b in H.jsonld(html_page) if b.get("@type") == "FAQPage"]
    text = P.read(html_page)
    visible = re.findall(r'<div class="faq-q"[^>]*>(.*?)</div>', text, re.S)
    if not visible and '<h2 id="faq">' in text:  # gift guides list each question as an <h3> under the FAQ heading
        section = text.split('<h2 id="faq">', 1)[1].split("<h2", 1)[0]
        visible = re.findall(r"<h3[^>]*>(.*?)</h3>", section, re.S)
    if not blocks:
        pytest.skip("no FAQ schema")

    def plain(s):
        return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", "", s))).strip()

    schema_questions = [e["name"] for e in blocks[0]["mainEntity"]]
    assert schema_questions == [plain(q) for q in visible], "FAQ schema questions differ from the visible FAQ (run scripts/build_nav.py)"
