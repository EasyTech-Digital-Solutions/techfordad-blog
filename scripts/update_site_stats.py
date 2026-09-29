#!/usr/bin/env python3
"""Keep the homepage "N+ Products Compared" claim honest.

    python3 scripts/update_site_stats.py

Counts the distinct products that have a product card in blog/ and gift-guides/ (same grouping rule
as scripts/audit_inventory.py), takes 75% of that to allow for the same product being named slightly
differently on US and Canada pages, and rounds down to a multiple of 50 (minimum 50). The result is
written into the trust bar in index.html, so the claim can only ever understate the real number.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_inventory import ROOT, normalize, product_cards  # noqa: E402


def distinct_products():
    names = set()
    for folder in ("blog", "gift-guides"):
        for path in sorted((ROOT / folder).glob("*.html")):
            html = path.read_text(encoding="utf-8")
            if 'http-equiv="refresh"' in html:
                continue
            for card in product_cards(html):
                if card["name"] != "?":
                    names.add(normalize(card["name"]))
    return len(names)


def main():
    count = distinct_products()
    claim = max(50, int(count * 0.75) // 50 * 50)
    index = ROOT / "index.html"
    text = index.read_text(encoding="utf-8")
    new, n = re.subn(r"\d+\+ Products Compared", f"{claim}+ Products Compared", text)
    if n and new != text:
        index.write_text(new, encoding="utf-8", newline="")
    print(f"{count} distinct products found -> homepage says \"{claim}+ Products Compared\"" + ("" if n else " (claim text not found)"))


if __name__ == "__main__":
    main()
