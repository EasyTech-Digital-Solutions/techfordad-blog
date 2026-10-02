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
