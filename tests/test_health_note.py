"""Health pages carry the "not medical advice" notice (written by scripts/build_health_note.py)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_health_note as H  # noqa: E402
import pages as P  # noqa: E402


@pytest.mark.parametrize("rel", H.MEDICAL_PAGES)
def test_health_page_has_the_notice(rel):
    text = P.read(rel)
    assert text.count("<!-- health-note -->") == 1, f"{rel}: expected exactly one health notice"
    block = text.split("<!-- health-note -->")[1].split("<!-- /health-note -->")[0]
    assert "not medical advice" in block
    assert 'href="../how-we-review.html"' in block
    assert "doctor" in block


def test_listed_pages_exist_and_are_indexable():
    for rel in H.MEDICAL_PAGES:
        assert (P.ROOT / rel).exists(), f"{rel} is listed in MEDICAL_PAGES but does not exist"
        assert not P.is_noindex(rel)


def test_notice_only_on_listed_pages():
    for rel in P.all_html():
        if "<!-- health-note -->" in P.read(rel):
            assert rel in H.MEDICAL_PAGES, f"{rel} has a health notice but is not in MEDICAL_PAGES"
