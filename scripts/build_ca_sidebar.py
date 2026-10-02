#!/usr/bin/env python3
"""Fill the right-hand sidebar (Our Top Picks, Related Guides, affiliate note) on the Canada articles.

    python3 scripts/build_ca_sidebar.py          # write
    python3 scripts/build_ca_sidebar.py --check  # verify only, exit 1 on problems

The USA articles keep their sidebar by hand (build_sidebar_picks.py only tidies it). The Canada articles use the same
two-column layout, but their sidebar is generated, between <!-- ca-sidebar --> markers inside <aside class="article-sidebar">:

  * Our Top Picks: one entry per item of the page's own "Which One Should You Buy?" list (same order, same #links),
    with a short label and the price shown there.
  * Related Guides: the first two pages from the topic map in build_related.py (Canada versions), with their blurbs.
  * The affiliate note.

A Canada article without a pick list (the plans guide) just gets Related Guides and the note. The script is idempotent
and is run by build_nav.py. Labels are shortened by shorten_label(); if a label reads badly, add it to OVERRIDES.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_related as BR  # noqa: E402  (topic map and relative-link helper)

ROOT = Path(__file__).resolve().parent.parent
BLOCK_RE = re.compile(r"([ \t]*)<!-- ca-sidebar -->.*?<!-- /ca-sidebar -->", re.S)
LIST_RE = re.compile(r'<ul class="buy-decision">(.*?)</ul>', re.S)
ITEM_RE = re.compile(r"<li>(.*?)</li>", re.S)
problems = []

# Labels that do not shorten well by rule. Key: the label as written in the pick list.
OVERRIDES = {
    "Best If Your Parent Is Already in the Amazon Ecosystem": "Best for Amazon Users",
    "Best for Tech-Comfortable Seniors (No Monthly Fee)": "Best for Tech-Comfortable",
    "Best for Seniors Who Want Physical Buttons": "Best for Physical Buttons",
    "Best for Long-Distance Family Caregiving": "Best for Long-Distance Care",
    "Best for Households with Multiple Users": "Best for Multiple Users",
    "Best GPS Tracker for Seniors with Dementia": "Best for Dementia",
    "Best Battery Life for Active Seniors": "Best Battery Life",
    "Best for Speech in Noisy Environments": "Best in Noisy Places",
}


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def write(p, text):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def shorten_label(label):
    label = plain(label).rstrip(":").strip()
    for start, short in OVERRIDES.items():
        if label.startswith(start):
            return short
    s = re.sub(r"\s+(for|in)\s+(Most\s+)?(Canadian|Canada)\b.*$", "", label)
    s = re.sub(r"\s+(for\s+Seniors|with|If|Who|Without)\b.*$", "", s)
    if len(s.split()) < 2:
        s = " ".join(label.split()[:4])
    if len(s) > 34:
        s = s[:34].rsplit(" ", 1)[0]
    return s


def shorten_price(price):
    p = plain(price).replace(" CAD", "").strip()
    if len(p) > 22:
        m = re.search(r"\$[\d,]+(?:\.\d+)?", p)
        p = f"From ~{m.group(0)}" if m else ""
    return p


def picks(text):
    """[(anchor, product name, short label, price)] from the page's 'Which One Should You Buy?' list."""
    m = LIST_RE.search(text)
    out = []
    if not m:
        return out
    for li in ITEM_RE.findall(m.group(1)):
        lab = re.search(r"<strong>(.*?)</strong>", li, re.S)
        a = re.search(r'<a href="#([^"]+)">(.*?)</a>', li, re.S)
        price = re.search(r"</a>\s*\((.*?)\)\s*(?:<span|$)", li, re.S)
        if not (lab and a):
            problems.append("pick list item without a label or #link: " + plain(li)[:60])
            continue
        out.append((a.group(1), plain(a.group(2)), shorten_label(lab.group(1)), shorten_price(price.group(1)) if price else ""))
    return out


def esc(s):
    return html.escape(s, quote=False)


def render(path, text):
    lines = ["<!-- ca-sidebar -->"]
    items = picks(text)
    if items:
        lines += ['    <div class="sidebar-box">', "      <h3>Our Top Picks</h3>"]
        for n, (anchor, name, label, price) in enumerate(items, 1):
            sub = f"{label} · {price}" if price else label
            lines += ['      <div class="quick-pick">', f'        <div class="quick-num{" gold" if n == 1 else ""}">{n}</div>',
                      '        <div class="quick-info">', f'          <a href="#{anchor}"><strong>{esc(name)}</strong></a>',
                      f"          <span>{esc(sub)}</span>", "        </div>", "      </div>"]
        lines.append("    </div>")
    rel_items = BR.entries(path)[:2]
    if rel_items:
        lines += ['    <div class="sidebar-box">', "      <h3>Related Guides</h3>"]
        for target, title, blurb in rel_items:
            lines += ['      <div class="quick-pick">', '        <div class="quick-info">',
                      f'          <a href="{BR.rel(path, target)}"><strong>{esc(plain(title))} →</strong></a>',
                      f"          <span>{esc(plain(blurb))}</span>", "        </div>", "      </div>"]
        lines.append("    </div>")
    lines += ['    <p class="disclaimer"><strong>Affiliate Disclosure:</strong> We earn a small commission if you purchase through our links. '
              'This never influences our rankings.</p>', "    <!-- /ca-sidebar -->"]
    return "\n".join(lines)


def main():
    check = "--check" in sys.argv
    done = 0
    for p in sorted(ROOT.glob("blog/*.html")):
        path = p.relative_to(ROOT).as_posix()
        if BR.country_of(path) != "ca" or BR.noindex(path) or BR.is_stub(path):
            continue
        text = read(p)
        m = BLOCK_RE.search(text)
        if not m:
            problems.append(f"{path}: no <!-- ca-sidebar --> block inside the sidebar")
            continue
        new = text[:m.start()] + "    " + render(path, text).lstrip() + text[m.end():]
        if check:
            if new != text:
                problems.append(f"{path}: sidebar out of date (run build_ca_sidebar.py)")
        elif new != text:
            write(p, new)
        done += 1
    if problems:
        print("\n".join(f"x {p}" for p in problems))
        sys.exit(1)
    print(f"canada sidebar: {done} pages {'OK' if check else 'written'}")


if __name__ == "__main__":
    main()
