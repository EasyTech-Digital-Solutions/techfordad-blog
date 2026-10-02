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
    ("browser: JavaScript error on every page", append("js/main.js", "\nthrow new Error('boom');\n"), "tests/test_ui_pages.py::test_loads_without_errors", ["--quick"]),
    ("browser: sideways scrolling", append("css/style.css", "\nbody { min-width: 2400px; }\n"), "tests/test_ui_pages.py::test_no_sideways_scrolling", ["--quick"]),
    ("browser: toolbar misaligned", append("css/style.css", "\n.page-tools { margin-left: -120px; }\n"), "tests/test_ui_pages.py::test_toolbar_lines_up_with_the_article", ["--quick"]),
    ("browser: tiny buttons on phones", append("css/style.css", "\n@media (max-width: 600px) { .page-tools button, .page-tools a { min-height: 20px; padding: 2px 6px; } }\n"), "tests/test_ui_pages.py::test_touch_targets_on_phones", ["--quick"]),
    ("browser: print scroll-jump bug is back", sub("js/main.js", "    if (savedY !== null) {\n      const y", "    if (false) {\n      const y"), "tests/test_ui_interactions.py::test_print_page_restores_scroll_position", ["--quick"]),
    ("browser: print leaves the sidebar in", append("css/style.css", "\n@media print { aside, .sidebar { display: block !important; } }\n"), "tests/test_ui_print.py::test_print_layout_removes_page_chrome_and_keeps_content", ["--quick"]),
    ("browser: copy link copies the wrong thing", sub("js/main.js", "navigator.clipboard.writeText(url)", "navigator.clipboard.writeText(location.href + '?utm=x')"), "tests/test_ui_interactions.py::test_copy_link_copies_the_canonical_address", ["--quick"]),
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
