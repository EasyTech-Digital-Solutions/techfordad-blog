"""Place the manual AdSense slots on every indexable review (blog/*.html with a sidebar), in spots that do not get in the readers' way.

Why manual: Auto ads inserted up to eight 412px units per page, one above the hero image (a 0.4 to 0.5 layout shift on phones), others inside the
table of contents and the "Which One" list. Here the site owner decides where ads go, each slot has its height reserved (no shift), and no ad
ever sits in a list, a table, a card or above the page's first screen. Config: scripts/ads.json (a slot is written only when its id is set).

Slots, in page order (docs/page-structure.md):
  in_article  1. just before the first product review   2. in the middle of the buying-guide sections (long pages only)   3. just before the FAQ
  after_table just after the comparison table and its button
  sidebar     last box in the sticky sidebar (shown on wide screens only: the sidebar sits below the article on phones)
Blocks sit between <!-- ad:NAME --> markers so the script is idempotent. Never hand-edit them.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
BLOCK_RE = re.compile(r"[ \t]*<!-- ad:[a-z_0-9]+ -->.*?<!-- /ad -->[ \t]*\n\n?", re.S)


def config():
    return json.loads((ROOT / "scripts" / "ads.json").read_text(encoding="utf-8"))


def block(cfg, slot, where):
    sid = cfg["slots"].get(slot, "")
    if not sid:
        return None
    return (f'<!-- ad:{slot} -->\n<div class="ad-slot ad-slot-{where}">\n  <span class="ad-label">Advertisement</span>\n'
            f'  <ins class="adsbygoogle" style="display:block" data-ad-client="{cfg["client"]}" data-ad-slot="{sid}" '
            f'data-ad-format="auto" data-full-width-responsive="true"></ins>\n'
            "  <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>\n</div>\n<!-- /ad -->\n\n")


def is_indexable_review(text):
    return ('<aside class="article-sidebar"' in text and '<article class="article-body"' in text
            and "noindex" not in text[:4000] and 'http-equiv="refresh"' not in text)


def h2_ids(article):
    return [(m.group(1), m.start()) for m in re.finditer(r'<h2 id="([^"]+)"', article)]


def place(text, first_product_id=None):
    """Return the page with ad blocks (re)written; no-op when no slot is configured."""
    cfg = config()
    text = BLOCK_RE.sub("", text)
    if not is_indexable_review(text) or not any(cfg["slots"].values()):
        return text
    a0, a1 = text.index('<article class="article-body"'), text.index("</article>")
    inserts = []  # (position, block)

    def at_line_start(pos):
        return text.rfind("\n", 0, pos) + 1

    ids = h2_ids(text[a0:a1])
    ids = [(i, a0 + p) for i, p in ids]
    names = [i for i, _ in ids]
    # 1. before the first product review
    if first_product_id and first_product_id in names:
        b = block(cfg, "in_article", "article")
        if b:
            inserts.append((at_line_start(dict(ids)[first_product_id]), b))
    # comparison table: right after the table (and its button)
    if "comparison" in names:
        i = text.index('<h2 id="comparison"')
        j = text.find("</table>", i)
        if j != -1:
            k = j + len("</table>")
            wrap = re.match(r"\s*</div>\n", text[k:])
            k = k + wrap.end() if wrap else k
            cta = re.match(r"\s*<!-- table-cta -->.*?<!-- /table-cta -->\n", text[k:], re.S)
            k = k + cta.end() if cta else k
            b = block(cfg, "after_table", "table")
            if b:
                inserts.append((at_line_start(k) if text[k - 1] == "\n" else k, b))
    # 2. middle of the buying-guide sections (between the comparison table and the FAQ), long pages only
    if "comparison" in names and "faq" in names:
        mid = [(i, p) for i, p in ids if names.index("comparison") < names.index(i) < names.index("faq")]
        if len(mid) >= 4:
            b = block(cfg, "in_article", "article")
            if b:
                inserts.append((at_line_start(mid[len(mid) // 2][1]), b))
    # 3. before the FAQ
    if "faq" in names:
        b = block(cfg, "in_article", "article")
        if b:
            inserts.append((at_line_start(dict(ids)["faq"]), b))
    # sidebar: last thing inside the sticky aside
    sb = block(cfg, "sidebar", "sidebar")
    if sb:
        s0 = text.index('<aside class="article-sidebar"')
        s1 = text.index("</aside>", s0)
        inserts.append((at_line_start(s1), "".join(("    " + ln if ln.strip() else ln) for ln in sb.splitlines(True))))
    for pos, b in sorted(inserts, key=lambda x: -x[0]):
        text = text[:pos] + b + text[pos:]
    return text


def main():
    import build_buying_summary as B
    written = 0
    for path in sorted((ROOT / "blog").glob("*.html")):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        first = (B.PAGES.get(rel) or (None, [None]))[1][0]
        new = place(text, first)
        if new != text:
            path.write_text(new, encoding="utf-8")
            written += 1
    print(f"ads: {written} pages written" + ("" if any(config()["slots"].values()) else " (no slot ids set in scripts/ads.json: ads are off)"))


if __name__ == "__main__":
    main()
