"""Place the manual AdSense slots on every indexable review (blog/*.html with a sidebar), in spots that do not get in the readers' way.

Format: rectangle (300x250 or 336x280) on every slot, so a filled ad never grows past the 280px the slot reserves (a responsive 'auto' unit
filled at 438px on phones and would have pushed the page). Why manual: Auto ads inserted up to eight 412px units per page, one above the hero image (a 0.4 to 0.5 layout shift on phones), others inside the
table of contents and the "Which One" list. Here the site owner decides where ads go, each slot has its height reserved (no shift), and no ad
ever sits in a list, a table, a card or above the page's first screen. Config: scripts/ads.json (a slot is written only when its id is set).

Which pages carry ads (docs/page-structure.md, Ads): indexable reviews, the home page, guides and gift guides. Every other page (About, Contact,
Our Story, How We Review, Privacy, Affiliate Disclosure, the three index pages, noindex pages, redirect stubs, the 404) must NOT load the AdSense script at all,
which also removes Auto ads, anchor and vignette from them: AdSense does not allow ads on navigation, error or low-content pages. This script writes or
removes the script tag per page type, so a new page cannot pick it up by accident.

Slots on reviews, in page order:
  in_article  1. just before the first product review   2. one or two more at paragraph breaks in the buying guide (pages of 3,000+ words: one; 4,200+: two;
              always 350+ words from any other ad)   3. just before the FAQ
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
            f'data-ad-format="rectangle" data-full-width-responsive="false"></ins>\n'
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


FORBIDDEN_CLASSES = ('class="product-card', 'class="toc"', 'class="faq-item"', 'class="perk-offers"')
LONG_PAGE_WORDS = (3000, 4200)  # words in the article: one extra slot from the first, two from the second
MIN_WORDS_BETWEEN_ADS = 350


def inside_forbidden(text, pos):
    """The tag or class name of the list, table, card, contents box, FAQ item or offers box that contains `pos`, else None."""
    before = text[:pos]
    for tag, close in (("<ul", "</ul>"), ("<ol", "</ol>"), ("<table", "</table>")):
        if before.rfind(tag) > before.rfind(close):
            return tag
    for cls in FORBIDDEN_CLASSES:
        i = before.rfind(cls)
        if i != -1 and before[i:].count("<div") - before[i:].count("</div>") > 0:
            return cls
    return None


def words(fragment):
    return len(re.sub(r"<[^>]+>", " ", fragment).split())


def pick_spread(text, cands, start, end, taken, n):
    """From candidate insertion points, pick up to n spread evenly by word count between `start` and `end`, each at least
    MIN_WORDS_BETWEEN_ADS words from the ends and from every position in `taken` (and from each other)."""
    if n <= 0 or end <= start or not cands:
        return []
    total = words(text[start:end])
    picks = []
    for k in range(1, n + 1):
        target = total * k / (n + 1)
        best = None
        for pos in cands:
            w = words(text[start:pos])
            ok = all(words(text[min(pos, t):max(pos, t)]) >= MIN_WORDS_BETWEEN_ADS for t in [*taken, *picks, start, end])
            if ok and (best is None or abs(w - target) < abs(best[0] - target)):
                best = (w, pos)
        if best:
            picks.append(best[1])
    return picks


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


def place(text, first_product_id=None, rel=None, product_ids=None):
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
    h2pos = dict(ids)
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
    # 2. one or two more, by page length: between two product reviews (after a verdict, before the next product's heading, so a few hundred
    #    words separate it from the previous Check Price button) or at a paragraph break in the buying guide after the comparison table
    if "faq" in names and first_product_id in names:
        art_words = words(text[a0:a1])
        n_mid = 0 if art_words < LONG_PAGE_WORDS[0] else 1 if art_words < LONG_PAGE_WORDS[1] else 2
        b = block(cfg, "in_article", "article")
        if b and n_mid:
            start = _line_start(text, dict(ids)[first_product_id])
            end = _line_start(text, dict(ids)["faq"])
            prods = [n for n in (product_ids or []) if n in h2pos]
            cands = [_line_start(text, h2pos[n]) for n in prods[1:]]  # before product #2, #3, ...
            if "comparison" in h2pos:
                j = text.find("</table>", h2pos["comparison"])
                for m in re.finditer(r"</p>\n(?=\s*<p[ >])|\n(?=[ \t]*<h2[ >])", text[j:end] if j != -1 else ""):
                    pos = j + m.end()
                    if not inside_forbidden(text, pos):
                        cands.append(pos)
            cands = [c for c in cands if not inside_forbidden(text, c)]
            for pos in pick_spread(text, sorted(set(cands)), start, end, [pos for pos, _ in inserts], n_mid):
                inserts.append((pos, b))
    # 3. before the FAQ
    if "faq" in names:
        b = block(cfg, "in_article", "article")
        if b:
            inserts.append((at_line_start(dict(ids)["faq"]), b))
    # keep the ads in the article at least MIN_WORDS_BETWEEN_ADS words apart: on a short page the later of two close slots is dropped
    inserts.sort(key=lambda x: x[0])
    kept = []
    for pos, b in inserts:
        if not kept or words(text[kept[-1][0]:pos]) >= MIN_WORDS_BETWEEN_ADS:
            kept.append((pos, b))
    inserts = kept
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
        new = manage_script(place(text, first, rel, (B.PAGES.get(rel) or (None, []))[1]), kind, cfg["client"])
        if new != text:
            path.write_text(new, encoding="utf-8")
            written += 1
    print(f"ads: {written} pages written" + ("" if any(cfg["slots"].values()) else " (no slot ids set in scripts/ads.json: slots are off)"))


if __name__ == "__main__":
    main()
