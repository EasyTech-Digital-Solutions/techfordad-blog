"""Write the "How We Chose" box at the BOTTOM of each article (just before the sources box), from scripts/how_we_chose.json.

It used to sit near the top of four US pages only, with claims the site cannot back (measured against ergonomic standards, thousands of
reviews analysed). This keeps every article's box short, in the same place, and limited to what TechForDad really does: it reads
manufacturer specifications, published expert and buyer reviews and accessibility guidance, and does not test products. Canada pages add
one sentence about Canadian availability and CAD prices.

Never hand-edit the `<!-- how-we-chose -->` block. Add a page to the JSON and run `python3 scripts/build_nav.py`.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "scripts" / "how_we_chose.json").read_text(encoding="utf-8"))

BLOCK_RE = re.compile(r"[ \t]*<!-- how-we-chose -->.*?<!-- /how-we-chose -->[ \t]*\r?\n\r?\n?", re.S)
# the old box that used to sit near the top of the page
LEGACY_RE = re.compile(r'[ \t]*<div class="toc"[^>]*>\s*<p class="toc-title">How We (?:Chose|Ranked|Evaluated|Researched)[^<]*</p>.*?</div>\s*\n?', re.S)


def block(rel, cat):
    noun = DATA["categories"][cat]["noun"]
    canada = rel.endswith("-canada.html") or rel.endswith("-canada.html")
    extra = " For Canada we also check that each model is sold here and show prices in Canadian dollars (CAD)." if canada else ""
    return (
        "    <!-- how-we-chose -->\n"
        '    <div class="toc" style="background:#f0f9ff; border-color:#0ea5e9;">\n'
        f'      <p class="toc-title">How We Chose These {noun}</p>\n'
        "      <p>We choose from manufacturer specifications, published expert and buyer reviews, and accessibility guidance. We do not test the "
        'products ourselves; see <a href="../how-we-review.html" style="text-decoration:underline">how we review products</a>.' + extra + "</p>\n"
        f"      <p><strong>What we weighed most:</strong> {DATA['categories'][cat]['criteria']}.</p>\n"
        "    </div>\n"
        "    <!-- /how-we-chose -->\n\n"
    )


def main():
    written, problems = 0, []
    for rel, cat in DATA["pages"].items():
        path = ROOT / rel
        original = path.read_text(encoding="utf-8")
        text = LEGACY_RE.sub("", BLOCK_RE.sub("", original))
        marker = next((m for m in ("<!-- sources -->", "<!-- gift-links -->", "<!-- related -->", "</article>") if m in text), None)
        if not marker:
            problems.append(rel)
            continue
        i = text.index(marker)
        # keep the box inside the article column: step back to the start of the marker's line
        i = text.rfind("\n", 0, i) + 1
        new = text[:i] + block(rel, cat) + text[i:]
        if new != original:
            path.write_text(new, encoding="utf-8")
            written += 1
    print(f"how we chose: {written} pages written" + (f" (no insertion point: {problems})" if problems else ""))


if __name__ == "__main__":
    main()
