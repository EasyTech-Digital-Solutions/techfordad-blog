"""Place the manual AdSense slots on every indexable review (blog/*.html with a sidebar), in spots that do not get in the readers' way.

Why manual: Auto ads inserted up to eight 412px units per page, one above the hero image (a 0.4 to 0.5 layout shift on phones), others inside the
table of contents and the "Which One" list. Here the site owner decides where ads go, each slot has its height reserved (no shift), and no ad
ever sits in a list, a table, a card or above the page's first screen. Config: scripts/ads.json (a slot is written only when its id is set).

Which pages carry ads (docs/page-structure.md, Ads): indexable reviews, the home page, guides and gift guides. Every other page (About, Contact,
Our Story, How We Review, Privacy, Affiliate Disclosure, the three index pages, noindex pages, redirect stubs, the 404) must NOT load the AdSense script at all,
which also removes Auto ads, anchor and vignette from them: AdSense does not allow ads on navigation, error or low-content pages. This script writes or
removes the script tag per page type, so a new page cannot pick it up by accident.

Slots on reviews, in page order:
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


SCRIPT_LINE = '  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client}" crossorigin="anonymous"></script>\n'
SCRIPT_RE = re.compile(r'[ \t]*<script async src="https://pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js\?client=[^"]+" crossorigin="anonymous"></script>\n')
ACCOUNT_RE = re.compile(r'(<meta name="google-adsense-account" content="[^"]+"/>\n)')
INDEX_PAGES = ("blog/index.html", "guides/index.html", "gift-guides/index.html")


def page_kind(rel, text):
    """'review', 'home', 'guide', 'gift' for pages that carry ads; None for every page that must stay ad-free."""
    if 'http-equiv="refresh"' in text or "noindex" in text[:5000] or rel in INDEX_PAGES:
        return None
    if rel == "index.html":
        return "home"
    if rel.startswith("blog/"):
        return "review" if is_indexable_review(text) else None
    if rel.startswith("guides/"):
        return "guide"
    if rel.startswith("gift-guides/"):
        return "gift"
    return None  # about, contact, privacy, affiliate disclosure, how we review, our story, 404 and any other top-level page


def manage_script(text, kind, client):
    """The AdSense script is present on ad pages and absent everywhere else."""
    has = bool(SCRIPT_RE.search(text))
    if kind is None:
        return SCRIPT_RE.sub("", text) if has else text
    if has or not ACCOUNT_RE.search(text):
        return text
    return ACCOUNT_RE.sub(lambda m: m.group(1) + SCRIPT_LINE.format(client=client), text, count=1)


def _line_start(text, pos):
    return text.rfind("\n", 0, pos) + 1


def _before_offers(text, pos):
    """Move an insertion point above any Amazon offer block (perk-line / perk-note) that sits right in front of a heading."""
    for _ in range(3):
        head = text[:pos].rstrip()
        m = None
        if head.endswith("</aside>"):
            i = head.rfind('<aside class="perk-note"')
            m = i if i != -1 and "<h2" not in head[i:] else None
        elif head.endswith("</p>"):
            i = head.rfind('<p class="perk-line"')
            m = i if i != -1 and "<h2" not in head[i:] else None
        if m is None:
            break
        pos = _line_start(text, m)
    return pos


def place_home(text, cfg):
    out = []
    for heading in ("In-Depth Guides for Caregivers", "Guides for Canadian Families"):
        i = text.find(f"<h2>{heading}</h2>")
        j = text.find("</section>", i) if i != -1 else -1
        b = block(cfg, "in_article", "home")
        if j != -1 and b:
            k = j + len("</section>\n")
            out.append((k, b))
    return out


def place_guide(text, cfg):
    out = []
    a0 = text.find('<div class="about-body">')
    toc_end = text.find("<!-- /guide-toc -->")
    stop = min([x for x in (text.find("<!-- sources -->"), text.find("<!-- related -->")) if x != -1] or [len(text)])
    if a0 == -1 or toc_end == -1:
        return out
    secs = [m for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", text[toc_end:stop], re.S)
            if not re.sub(r"<[^>]+>", "", m.group(1)).strip().startswith(("Related", "Sources", "Keep Reading", "Free Caregiver"))]
    b = block(cfg, "in_article", "article")
    if not b or len(secs) < 2:
        return out
    out.append((_line_start(text, toc_end + secs[0].start()), b))
    if len(secs) >= 6:
        out.append((_line_start(text, toc_end + secs[len(secs) // 2].start()), b))
    rel_h2 = re.search(r"<h2[^>]*>\s*Related", text[toc_end:])
    cand = [x for x in (text.find("<!-- sources -->"), (toc_end + rel_h2.start()) if rel_h2 else -1, text.find("<!-- related -->")) if x != -1 and x > toc_end]
    if cand:
        out.append((_line_start(text, min(cand)), b))
    return out


def place_gift(text, cfg):
    out = []
    b = block(cfg, "in_article", "article")
    if not b:
        return out
    h = {m.group(1): m.start() for m in re.finditer(r'<h2 id="([^"]+)"', text)}
    order = sorted(h.items(), key=lambda kv: kv[1])
    names = [n for n, _ in order]
    if "picks" in h:
        out.append((_before_offers(text, _line_start(text, h["picks"])), b))
        after = [n for n in names[names.index("picks") + 1:] if n not in ("faq", "related")]
        if after:
            out.append((_line_start(text, h[after[0]]), b))
    if "faq" in h:
        out.append((_before_offers(text, _line_start(text, h["faq"])), b))
    return out


def place(text, first_product_id=None, rel=None):
    """Return the page with ad blocks (re)written; no-op when no slot is configured."""
    cfg = config()
    text = BLOCK_RE.sub("", text)
    kind = page_kind(rel, text) if rel else ("review" if is_indexable_review(text) else None)
    if kind is None or not any(cfg["slots"].values()):
        return text
    if kind in ("home", "guide", "gift"):
        found = {"home": place_home, "guide": place_guide, "gift": place_gift}[kind](text, cfg)
        for pos, b in sorted(found, key=lambda x: -x[0]):
            text = text[:pos] + b + text[pos:]
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


def pages():
    for pattern in ("*.html", "blog/*.html", "guides/*.html", "gift-guides/*.html"):
        for path in sorted(ROOT.glob(pattern)):
            yield path.relative_to(ROOT).as_posix(), path


def main():
    import build_buying_summary as B
    cfg = config()
    written = 0
    for rel, path in pages():
        text = path.read_text(encoding="utf-8")
        kind = page_kind(rel, text)
        first = (B.PAGES.get(rel) or (None, [None]))[1][0]
        new = manage_script(place(text, first, rel), kind, cfg["client"])
        if new != text:
            path.write_text(new, encoding="utf-8")
            written += 1
    print(f"ads: {written} pages written" + ("" if any(cfg["slots"].values()) else " (no slot ids set in scripts/ads.json: slots are off)"))


if __name__ == "__main__":
    main()
