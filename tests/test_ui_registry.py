"""The guard that keeps these tests current as the design changes.

Every section of css/style.css (the `/* ===== NAME ===== */` banners) must be listed in tests/data/ui_components.json
together with the tests that cover it. Add a new section of CSS and this test fails until you:
    1. add a line to the registry saying which test covers it, and
    2. if no existing test covers it (a new button, a new interaction, a new kind of box), write one.
"""
import json
import re

import pages as P

REGISTRY = json.loads((P.ROOT / "tests" / "data" / "ui_components.json").read_text(encoding="utf-8"))["components"]
BANNER = re.compile(r"^/\*\s*=====\s*(.+?)\s*(?:=====\s*)?(?:\*/)?\s*$")


def css_sections():
    out = []
    for line in (P.ROOT / "css" / "style.css").read_text(encoding="utf-8").splitlines():
        m = BANNER.match(line)
        if m:
            name = re.split(r"\s+\(|\s+—|\s+=====", m.group(1))[0].strip()
            out.append(name)
    return out


def test_every_css_section_is_registered():
    missing = [s for s in css_sections() if s not in REGISTRY]
    assert not missing, (
        "css/style.css has sections that tests/data/ui_components.json does not know about:\n  " + "\n  ".join(missing)
        + "\n\nAdd each one to the registry with the test(s) that cover it. If nothing covers it yet, write the test first: "
          "see tests/README.md, 'When you change the UI'.")


def test_registry_has_no_stale_sections():
    sections = set(css_sections())
    stale = [k for k in REGISTRY if k not in sections]
    assert not stale, f"registry lists CSS sections that no longer exist (remove them): {stale}"


def test_every_section_names_real_tests():
    problems = []
    for name, entry in REGISTRY.items():
        covered = entry.get("covered_by", [])
        if not covered:
            problems.append(f"{name}: covered_by is empty")
        for ref in covered:
            file = ref.split("::")[0]
            path = P.ROOT / "tests" / file
            if not path.is_file():
                problems.append(f"{name}: {ref} (no such test file)")
            elif "::" in ref and ref.split("::")[1] not in path.read_text(encoding="utf-8"):
                problems.append(f"{name}: {ref} (no test with that name)")
    assert not problems, "\n".join(problems)


def test_every_css_comment_is_closed():
    """An unterminated /* comment silently swallows the rules after it (it once removed the country badge's styling)."""
    css = (P.ROOT / "css" / "style.css").read_text(encoding="utf-8")
    assert css.count("/*") == css.count("*/"), f"css/style.css has {css.count('/*')} comment openers and {css.count('*/')} closers"
    depth = 0
    for m in re.finditer(r"/\*|\*/", css):
        depth += 1 if m.group(0) == "/*" else -1
        assert depth in (0, 1), f"nested or unmatched comment near character {m.start()}"
