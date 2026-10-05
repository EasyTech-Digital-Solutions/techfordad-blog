"""Every mapped article has one "How We Chose" box at the bottom (written by scripts/build_how_we_chose.py)."""
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import pages as P  # noqa: E402

PAGES = sorted(json.loads((P.ROOT / "scripts/how_we_chose.json").read_text())["pages"])


@pytest.mark.parametrize("rel", PAGES)
def test_one_box_after_products_and_faq(rel):
    text = P.read(rel)
    assert text.count("<!-- how-we-chose -->") == 1, f"{rel}: expected exactly one How We Chose block"
    pos = text.index("<!-- how-we-chose -->")
    assert text.count("How We Chose These") == 1, f"{rel}: duplicate How We Chose heading"
    assert pos > text.rindex('class="product-card'), f"{rel}: box sits above the products"
    assert pos > text.rindex('class="faq-item'), f"{rel}: box sits above the FAQ"
    block = text[pos:text.index("<!-- /how-we-chose -->")]
    assert "do not test the products ourselves" in block
    assert 'href="../how-we-review.html"' in block
    if rel.endswith("-canada.html"):
        assert "Canadian dollars (CAD)" in block
    else:
        assert "Canadian dollars" not in block
