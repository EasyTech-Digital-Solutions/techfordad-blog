"""The repo's own check scripts, run as tests, so one command covers them all."""
import subprocess
import sys

import pytest

import pages as P

CHECKS = {
    "check_site.py --all (prices, JSON-LD, title/description length, og:image)": ["scripts/check_site.py", "--all"],
    "check_internal_links.py (every internal link resolves)": ["scripts/check_internal_links.py"],
    "build_nav.py --check (nav, hreflang, related, sources, buying summary, product schema, CTAs, asset versions)": ["scripts/build_nav.py", "--check"],
}


@pytest.mark.parametrize("name", list(CHECKS), ids=list(CHECKS))
def test_repo_check_script(name):
    run = subprocess.run([sys.executable, *CHECKS[name]], cwd=P.ROOT, capture_output=True, text=True)
    assert run.returncode == 0, (run.stdout + run.stderr)[-2500:]
