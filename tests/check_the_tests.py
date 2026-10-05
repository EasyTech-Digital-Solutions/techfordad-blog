#!/usr/bin/env python3
"""Does the suite actually catch problems? Breaks a COPY of the site in specific ways and checks the right test fails.

    ./.venv/bin/python tests/check_the_tests.py            # all mutations (about 4 minutes)
    ./.venv/bin/python tests/check_the_tests.py affiliate  # only mutations whose name contains "affiliate"

Run it after you change the tests (or add a new kind of check). A mutation that is NOT caught means the suite has a
blind spot: fix the test, not the mutation. The real site is never touched (everything happens in a temp folder).
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = "blog/best-alexa-devices-for-seniors.html"  # the first US article, so `--quick` always includes it


def sub(path, old, new, count=1):
    def run(root):
        p = root / path
        text = p.read_text(encoding="utf-8")
        assert old in text if not old.startswith("re:") else re.search(old[3:], text), f"mutation target not found in {path}: {old[:50]}"
        text = re.sub(old[3:], new, text, count=count) if old.startswith("re:") else text.replace(old, new, count)
        p.write_text(text, encoding="utf-8")
    return run


def add_file(path, content):
    def run(root):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(content, encoding="utf-8")
    return run


def append(path, content):
    def run(root):
        p = root / path
        p.write_text(p.read_text(encoding="utf-8") + content, encoding="utf-8")
    return run


# (name, mutation, pytest selector, extra args)
MUTATIONS = [
    ("affiliate: wrong tracking ID", sub(PAGE, r're:(<a [^>]*href="https://www\.amazon\.com/[^"]*tag=)techfordad0b-20', r"\1wrongtag-20"), "tests/test_links.py::test_amazon_links_use_the_right_tracking_id", []),
    ("affiliate: missing rel=sponsored", sub(PAGE, 'rel="sponsored noopener noreferrer"', 'rel="noopener"'), "tests/test_links.py::test_amazon_links_are_marked_sponsored_and_safe", []),
    ("affiliate: bounty link changed", sub(PAGE, "amazon.com/amazonprime?tag=", "amazon.com/prime?tag="), "tests/test_links.py::test_membership_links_are_the_verified_ones", []),
    ("affiliate: shortened amzn.to link", sub(PAGE, "</article>", '<a href="https://amzn.to/abc123">x</a></article>'), "tests/test_links.py::test_no_shortened_or_foreign_affiliate_links", []),
    ("seo: title too long", sub(PAGE, "re:<title>[^<]*</title>", "<title>" + "Very long title " * 6 + "</title>"), "tests/test_seo.py::test_title_and_description", []),
    ("seo: missing canonical", sub(PAGE, "re:<link rel=\"canonical\"[^>]*>", ""), "tests/test_seo.py::test_canonical_url", []),
    ("html: duplicate id", sub(PAGE, "</article>", '<p id="faq">x</p><p id="faq">y</p></article>'), "tests/test_seo.py::test_no_duplicate_ids", []),
    ("html: unclosed tag", sub(PAGE, "</article>", "<div></article>"), "tests/test_seo.py::test_page_is_well_formed", []),
    ("html: image without alt", sub(PAGE, "</article>", '<img src="../images/og-default.svg"></article>'), "tests/test_seo.py::test_images_have_alt_text", []),
    ("html: broken local image", sub(PAGE, "</article>", '<img src="../images/nope.jpg" alt="x"></article>'), "tests/test_seo.py::test_local_assets_exist", []),
    ("security: http:// resource", sub(PAGE, "</article>", '<img src="http://example.com/a.png" alt="x"></article>'), "tests/test_security.py::test_no_insecure_http_resources", []),
    ("security: unknown third-party script", sub(PAGE, "</article>", '<script src="https://evil.example/x.js"></script></article>'), "tests/test_security.py::test_third_party_scripts_are_allowlisted", []),
    ("security: eval in main.js", append("js/main.js", "\neval('1+1');\n"), "tests/test_security.py::test_js_avoids_dangerous_apis", []),
    ("security: secret committed", add_file("docs/oops.md", "token = ghp_" + "a" * 36 + "\n"), "tests/test_security.py::test_no_secrets_committed", []),
    ("security: internal folder published", sub("_config.yml", "  - scripts\n", ""), "tests/test_security.py::test_internal_items_are_excluded_from_publishing", []),
    ("security: new inline onclick", sub(PAGE, "</article>", '<button onclick="x()">x</button></article>'), "tests/test_security.py::test_inline_event_handlers_only_where_known", []),
    ("inventory: unclassified new page", add_file("brand-new-section/page.html", "<!DOCTYPE html><html lang='en'><head><title>x</title></head><body></body></html>"), "tests/test_inventory.py::test_every_html_file_has_a_kind", []),
    ("inventory: page missing from sitemap", sub("sitemap.xml", r"re:(?s)<url>(?:(?!</url>).)*?blog/best-alexa-devices-for-seniors\.html(?:(?!</url>).)*?</url>\s*", ""), "tests/test_inventory.py::test_indexable_pages_are_in_the_sitemap", []),
    ("registry: new CSS section without tests", append("css/style.css", "\n/* ===== SHINY NEW WIDGET ===== */\n.shiny { color: red; }\n"), "tests/test_ui_registry.py::test_every_css_section_is_registered", []),
    ("a11y: a page loses its <main> landmark", lambda root: (sub(PAGE, '<main id="main">', '<div id="main">')(root), sub(PAGE, "</main>", "</div>")(root)), "tests/test_seo.py::test_has_main_landmark_and_skip_link", []),
    ("a11y: skip link is always on screen", append("css/style.css", "\n.skip-link { top: 0 !important; }\n"), "tests/test_ui_interactions.py::test_skip_link_works_with_keyboard", ["--quick"]),
    ("a11y: low-contrast green comes back", sub("css/style.css", "--green:   #15803D;", "--green:   #16A34A;"), "tests/test_ui_a11y.py::test_accessibility", ["--quick"]),
    ("a11y: links in sentences lose their underline", append("css/style.css", "\n.article-body p a, .gift-more p a { text-decoration: none !important; }\n"), "tests/test_ui_a11y.py::test_links_in_sentences_are_not_colour_only", ["--quick"]),
    ("template: a Canada article loses its sidebar", sub("blog/best-tablets-for-seniors-canada.html", '<aside class="article-sidebar">', '<div class="article-sidebar">'), "tests/test_template_parity.py::test_article_has_the_full_template", []),
    ("template: Top Picks sidebar drifts from the pick list", sub("blog/best-tablets-for-seniors-canada.html", 'class="quick-pick">\n        <div class="quick-num gold">1</div>\n        <div class="quick-info">\n          <a href="#ipad"', 'class="quick-pick">\n        <div class="quick-num gold">1</div>\n        <div class="quick-info">\n          <a href="#nope"'), "tests/test_template_parity.py::test_top_picks_sidebar_matches_the_pick_list", []),
    ("template: the comparison table drifts above the products", sub("blog/best-tablets-for-seniors-canada.html", "</article>", '<div class="product-card"></div></article>'), "tests/test_template_parity.py::test_summary_then_products_then_comparison_table", []),
    ("template: a Canada card goes back to the flat layout", sub("blog/best-tablets-for-seniors-canada.html", "<h4>Pros</h4>", "<strong>Pros</strong>"), "tests/test_template_parity.py::test_product_cards_use_the_shared_structure", []),
    ("template: a buy button floats outside its card", sub("blog/best-tablets-for-seniors-canada.html", '<h2 id="comparison">', '<a class="btn-check-price" href="#">x</a><h2 id="comparison">'), "tests/test_template_parity.py::test_buy_button_is_inside_its_card", []),
    ("template: Canada table goes back to its own style", sub("blog/best-tablets-for-seniors-canada.html", '<table class="compare-table">', '<table class="comparison-table">'), "tests/test_template_parity.py::test_comparison_table_uses_the_shared_markup", []),
    ("template: Canada breadcrumb gets an extra level", sub("blog/best-tablets-for-seniors-canada.html", '<a href="../index.html">Home</a> <span>›</span>', '<a href="../index.html">Home</a> <span>›</span> <a href="index.html">Reviews</a> <span>›</span>'), "tests/test_template_parity.py::test_hero_line_and_breadcrumb", []),
    ("template: a second amber disclosure box returns to a review", sub("blog/best-tablets-for-seniors-canada.html", '<div class="article-layout">', '<div class="toc" style="background:#fffbeb; border-color:#f59e0b; font-size:0.9rem;"><strong>Affiliate Disclosure:</strong> x</div><div class="article-layout">'), "tests/test_template_parity.py::test_disclosure_is_one_slim_strip_under_the_hero", []),
    ("template: a page goes back to details-style FAQ", sub("blog/best-tablets-for-seniors-canada.html", '<div class="faq-item">', '<details class="faq-item">'), "tests/test_template_parity.py::test_faq_uses_the_click_to_open_markup", []),
    ("browser: FAQ stops working from the keyboard", sub("js/main.js", "if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }", ""), "tests/test_ui_interactions.py::test_faq_works_from_the_keyboard", ["--quick"]),
    ("browser: sidebar falls below the article on desktop", append("css/style.css", "\n.article-layout { display: block !important; }\n"), "tests/test_ui_pages.py::test_articles_are_two_columns_on_desktop_and_stacked_on_phones", ["--quick"]),
    ("browser: JavaScript error on every page", append("js/main.js", "\nthrow new Error('boom');\n"), "tests/test_ui_pages.py::test_loads_without_errors", ["--quick"]),
    ("browser: sideways scrolling", append("css/style.css", "\nbody { min-width: 2400px; }\n"), "tests/test_ui_pages.py::test_no_sideways_scrolling", ["--quick"]),
    ("browser: toolbar misaligned", append("css/style.css", "\n.page-tools { margin-left: -120px; }\n"), "tests/test_ui_pages.py::test_toolbar_lines_up_with_the_article", ["--quick"]),
    ("browser: toolbar breaks without the share API", append("css/style.css", "\n@media (max-width: 600px) { .page-tools { display: block !important; } .page-tools > * { display: block; margin-bottom: 6px; } }\n"), "tests/test_ui_interactions.py::test_toolbar_grid_is_tidy_with_and_without_the_share_api", ["--quick"]),
    ("browser: tiny buttons on phones", append("css/style.css", "\n@media (max-width: 600px) { .page-tools button, .page-tools a { min-height: 20px; padding: 2px 6px; } }\n"), "tests/test_ui_pages.py::test_touch_targets_on_phones", ["--quick"]),
    ("browser: print scroll-jump bug is back", sub("js/main.js", "    if (savedY !== null) {\n      const y", "    if (false) {\n      const y"), "tests/test_ui_interactions.py::test_print_page_restores_scroll_position", ["--quick"]),
    ("browser: print leaves the sidebar in", append("css/style.css", "\n@media print { aside, .sidebar { display: block !important; } }\n"), "tests/test_ui_print.py::test_print_layout_removes_page_chrome_and_keeps_content", ["--quick"]),
    ("browser: copy link copies the wrong thing", sub("js/main.js", "navigator.clipboard.writeText(url)", "navigator.clipboard.writeText(location.href + '?utm=x')"), "tests/test_ui_interactions.py::test_copy_link_copies_the_canonical_address", ["--quick"]),
    # ---- added in the 2026-10-05 sweep
    ("social: share image is an SVG", sub(PAGE, "re:(<meta property=\"og:image\" content=\"[^\"]*?)\\.(?:jpg|png)\"", r'\1.svg"'), "tests/test_seo.py::test_social_card_is_complete", []),
    ("social: twitter:image missing", sub(PAGE, "re:\\s*<meta name=\"twitter:image\" content=\"[^\"]*\"\\s*/>", ""), "tests/test_seo.py::test_social_card_is_complete", []),
    ("schema: Article loses its image", sub(PAGE, "re:\\n\\s*\"image\": \"[^\"]*\",", ""), "tests/test_seo.py::test_article_schema_is_complete", []),
    ("schema: product list turns back into merchant Offers", sub(PAGE, "re:\"@type\": \"ListItem\",\\s*\"position\": 1,", '"@type": "ListItem", "position": 1, "offers": {"@type": "Offer", "price": "9", "availability": "https://schema.org/InStock"},'), "tests/test_seo.py::test_product_list_is_not_merchant_markup", []),
    ("schema: FAQ questions drift from the visible FAQ", sub(PAGE, "re:(<div class=\"faq-q\"[^>]*>)", r"\1Totally different question? "), "tests/test_seo.py::test_faq_schema_matches_the_visible_faq", []),
    ("honesty: a page claims experience we do not have", sub(PAGE, "</article>", "<p>In our experience this works well.</p></article>"), "tests/test_content_rules.py::test_no_claims_of_experience_the_site_does_not_have", []),
    ("honesty: unsupported superlative", sub(PAGE, "</article>", "<p>An industry-leading device.</p></article>"), "tests/test_content_rules.py::test_no_unsupported_superlatives", []),
    ("honesty: invented numeric score", sub(PAGE, "</article>", "<p>Our score: 9.4/10</p></article>"), "tests/test_content_rules.py::test_no_numeric_scores", []),
    ("honesty: blood pressure monitor called tax claimable", sub(PAGE, "</article>", "<p>A blood pressure monitor qualifies for the Medical Expense Tax Credit.</p></article>"), "tests/test_content_rules.py::test_blood_pressure_monitors_are_not_called_tax_claimable", []),
    ("honesty: health page loses every source link", sub("blog/best-hearing-aids-for-seniors.html", "re:<a href=\"https://[^\"]*(?:cdc|fda|nih|medicare|irs|iii|nidcd|nhlbi|hearingtracker|statcan|canada|va\\.gov)[^\"]*\"[^>]*>", "<a href=\"#\">", count=0), "tests/test_content_rules.py::test_health_pages_link_to_their_sources", []),
    ("honesty: health notice removed", sub("blog/best-hearing-aids-for-seniors.html", "re:<!-- health-note -->.*?<!-- /health-note -->", ""), "tests/test_health_note.py::test_health_page_has_the_notice", []),
    ("honesty: How We Chose box removed", sub("blog/best-tablets-for-seniors.html", "re:(?s)<!-- how-we-chose -->.*?<!-- /how-we-chose -->", ""), "tests/test_how_we_chose.py", []),
    ("honesty: a 5/5 ease score appears", sub("blog/best-tablets-for-seniors.html", "</article>", "<p>Ease of setup: 5/5</p></article>"), "tests/test_content_rules.py::test_no_numeric_scores", []),
    ("honesty: Amazon star rating and review count shown", sub("blog/best-tablets-for-seniors.html", "</article>", "<p>With 4,800 reviews and a 4.4 stars average.</p></article>"), "tests/test_content_rules.py::test_no_amazon_ratings_or_invented_review_claims", []),
    ("honesty: customers consistently report claim", sub("blog/best-tablets-for-seniors.html", "</article>", "<p>Customers consistently report easy setup.</p></article>"), "tests/test_content_rules.py::test_no_amazon_ratings_or_invented_review_claims", []),
    ("structure: a guide loses its table of contents", sub("guides/hearing-aids.html", "re:(?s)<!-- guide-toc -->.*?<!-- /guide-toc -->", ""), "tests/test_guides_structure.py::test_guide_follows_the_layout", []),
    ("structure: Canada twin loses its How We Chose box", sub("blog/best-tablets-for-seniors-canada.html", "re:(?s)<!-- how-we-chose -->.*?<!-- /how-we-chose -->", ""), "tests/test_structure_pairs.py", []),
    ("structure: a gift guide gets a second disclosure box", sub("gift-guides/tech-gifts-for-elderly-parents.html", '<div class="article-body">', '<div class="article-body"><div class="affiliate-box">x</div>'), "tests/test_guides_structure.py::test_gift_guide_follows_the_layout", []),
    ("seo: robots.txt blocks a noindex stub folder", append("robots.txt", "\nDisallow: /page/\n"), "tests/test_security.py::test_robots_does_not_block_noindex_stubs", []),
    ("affiliate: gift guide loses its membership links", sub("gift-guides/tech-gifts-for-elderly-parents.html", "amazon.com/amazonprime?tag=techfordad-gifts-20", "amazon.com/x", count=-1), "tests/test_content_rules.py::test_gift_guides_keep_their_membership_links", []),
    ("browser: gift block jumps after the page paints", sub("css/style.css", 'html[data-gifts="peak"] main#main { display: grid; grid-template-columns: minmax(0, 1fr); }', ""), "tests/test_ui_pages.py::test_home_gift_block_order_is_set_by_css_and_does_not_shift", []),
    ("generator: a gift guide drifts from build_gift_guides.py", sub("gift-guides/tech-gifts-for-elderly-parents.html", 'class="perk-note"', 'class="perk-changed"'), "tests/test_generated.py::test_repo_check_script", []),
    ("honesty: 'seniors told us' claim", sub(PAGE, "</article>", "<p>Seniors told us the speakers were too quiet.</p></article>"), "tests/test_content_rules.py::test_no_claims_of_experience_the_site_does_not_have", []),
    ("badge: shows the wrong country", sub("js/main.js", "const isCa = /-canada\\.html$/.test(location.pathname);", "const isCa = !/-canada\\.html$/.test(location.pathname);"), "tests/test_ui_pages.py::test_country_badge_says_which_country_the_page_is_for", ["--quick"]),
    ("badge: switch link jumps to another host", sub("js/main.js", "new URL(pair.href, location.href).pathname", "pair.href"), "tests/test_ui_pages.py::test_country_badge_says_which_country_the_page_is_for", ["--quick"]),
    ("badge: too small to tap", append("css/style.css", "\n.country-badge-pill { min-height: 20px !important; padding: 0 6px !important; }\n"), "tests/test_ui_pages.py::test_country_badge_says_which_country_the_page_is_for", ["--quick"]),
    ("badge: printed on paper", append("css/style.css", "\n@media print { .country-badge { display: block !important; } }\n"), "tests/test_ui_print.py::test_country_badge_is_not_printed", ["--quick"]),
]


def main(only=None):
    todo = [m for m in MUTATIONS if not only or only.lower() in m[0].lower()]
    missed = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, mutate, selector, extra in todo:
            work = Path(tmp) / "site"
            if work.exists():
                shutil.rmtree(work)
            shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache"))
            mutate(work)
            run = subprocess.run([sys.executable, "-m", "pytest", selector, "-x", "-q", "-p", "no:cacheprovider", *extra],
                                 cwd=work, capture_output=True, text=True)
            caught = run.returncode != 0
            print(f"{'caught' if caught else 'MISSED':7s} {name}", flush=True)
            if not caught:
                missed.append(name)
    print(f"\n{len(todo) - len(missed)} of {len(todo)} problems were caught.")
    if missed:
        print("BLIND SPOTS (the suite did not notice):\n  " + "\n  ".join(missed))
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
