"""Accessibility scan (axe-core) on every page. Existing problems are recorded in a baseline: new ones fail.

    pytest tests/test_ui_a11y.py                      # compare against tests/data/a11y_known_issues.json
    pytest tests/test_ui_a11y.py --update-baseline    # rewrite the baseline (review the git diff first!)

The baseline only ever gets smaller: a new problem, or MORE elements with an existing problem, fails; fixing a
problem completely also fails until its line is removed, so the file stays honest.
"""
import json

import pytest
from axe_playwright_python.sync_playwright import Axe

pytestmark = pytest.mark.slow

BASELINE = json.loads((__import__("pages").ROOT / "tests/data/a11y_known_issues.json").read_text(encoding="utf-8")) \
    if (__import__("pages").ROOT / "tests/data/a11y_known_issues.json").exists() else {"pages": {}}
STORE: dict[str, dict[str, int]] = {}


@pytest.fixture(scope="session", autouse=True)
def _write_baseline_when_asked(request):
    yield
    if request.config.getoption("--update-baseline") and STORE:
        path = __import__("pages").ROOT / "tests/data/a11y_known_issues.json"
        doc = {
            "_readme": "Accessibility problems (axe-core rule -> number of elements) that exist today, per page. The suite fails if a page gets a NEW problem or MORE elements with an existing one. Fix problems and re-run with --update-baseline to shrink this file; never grow it to make a test pass.",
            "pages": {k: STORE[k] for k in sorted(STORE) if STORE[k]},
        }
        path.write_text(json.dumps(doc, indent=1, sort_keys=False) + "\n", encoding="utf-8")


def test_accessibility(page, sessions, request):
    pg, *_ = sessions("desktop").open(page)
    result = Axe().run(pg)
    pg.close()
    found = {v["id"]: len(v["nodes"]) for v in result.response["violations"]}
    if request.config.getoption("--update-baseline"):
        STORE[page] = found
        return
    known = BASELINE["pages"].get(page, {})
    worse = {r: f"{n} elements (known: {known.get(r, 0)})" for r, n in found.items() if n > known.get(r, 0)}
    fixed = [r for r in known if r not in found]
    assert not worse, ("new accessibility problems (fix them; see https://dequeuniversity.com/rules/axe/ for each rule id):\n  "
                       + "\n  ".join(f"{r}: {d}" for r, d in worse.items()))
    assert not fixed, f"fixed! remove these from tests/data/a11y_known_issues.json (run with --update-baseline): {fixed}"


# axe only flags some colour-only links, so this checks the rule directly (WCAG 1.4.1): a link that sits inside a
# sentence needs more than a colour change to be recognised as a link: an underline, a border, or a bolder weight.
INDISTINGUISHABLE_LINKS_JS = """() => {
  const bad = [];
  const words = (n) => (n.textContent || '').trim().split(/\\s+/).filter(Boolean).length;
  for (const a of document.querySelectorAll('p a, li a, td a, dd a, .note a')) {
    if (a.closest('nav, header, footer, .toc, .toc-box, .related-guides, .sidebar-box, .sources li, .quick-pick, .page-tools, .table-tools, .perk-note, .perk-cta, .card, .breadcrumb')) continue;
    const block = a.closest('p, li, td, dd, .note');
    if (!block || getComputedStyle(a).display === 'block') continue;
    const around = words(block) - words(a);               // other words in the same sentence/paragraph
    if (around < 3 || !a.getBoundingClientRect().width) continue;
    const cs = getComputedStyle(a), ps = getComputedStyle(block);
    const underlined = cs.textDecorationLine.includes('underline');
    const border = parseFloat(cs.borderBottomWidth) > 0;
    const bolder = parseInt(cs.fontWeight) >= parseInt(ps.fontWeight) + 200;
    const isButton = parseFloat(cs.paddingLeft) >= 8 && cs.backgroundColor !== 'rgba(0, 0, 0, 0)';
    if (!underlined && !border && !bolder && !isButton) bad.push(a.textContent.trim().slice(0, 40) + ' -> ' + (a.getAttribute('href') || '').slice(0, 40));
  }
  return bad;
}"""


def test_links_in_sentences_are_not_colour_only(page, sessions):
    pg, *_ = sessions("desktop").open(page)
    bad = pg.evaluate(INDISTINGUISHABLE_LINKS_JS)
    pg.close()
    assert not bad, f"links inside running text that look like plain text (add an underline): {bad[:6]}"
