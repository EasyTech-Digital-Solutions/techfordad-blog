#!/usr/bin/env python3
"""Rename the sidebar "Quick Picks" box to "Our Top Picks" and make each entry link to its review section.

    python3 scripts/build_sidebar_picks.py          # write
    python3 scripts/build_sidebar_picks.py --check  # verify only, exit 1 on problems

The sidebar lists the top picks in ranking order, which is also the order of the product sections in the
article, so entry N links to product section N (a section is an <h2 id="..."> followed by a product card).
Wherever an entry's name also matches a section's product name, the two must agree, otherwise the page is
skipped and reported. Entries that already contain a link (e.g. straight to Amazon) are left as they are.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TITLE = "Our Top Picks"
BOX_RE = re.compile(r'(<div class="sidebar-box">\s*<h3>)(?:Quick Picks|Our Picks|Our Top Picks)(</h3>)(.*?)(?=<div class="sidebar-box">|<p class="disclaimer"|</aside>)', re.S)
ITEM_RE = re.compile(r'<div class="quick-pick">.*?</span>\s*</div>\s*</div>', re.S)
NAME_RE = re.compile(r"<strong>(.*?)</strong>", re.S)
problems = []
notes = []


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write(p, t):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", re.sub(r"<[^>]+>", "", s).lower().replace("&amp;", "and")).strip()


def sections(text):
    """Product sections in document order: (id, normalised product name)."""
    out = []
    for m in re.finditer(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>(.*?)(?=<h2 |\Z)', text, re.S):
        if "product-card" in m.group(3)[:700]:
            h3 = re.search(r"<h3[^>]*>(.*?)</h3>", m.group(3), re.S)
            out.append((m.group(1), norm(h3.group(1)) if h3 else norm(m.group(2))))
    return out


def process(path, check):
    rel = path.relative_to(ROOT).as_posix()
    old = read(path)
    m = BOX_RE.search(old)
    if not m:
        return
    secs = sections(old)
    body = m.group(3)
    items = ITEM_RE.findall(body)
    ok = len(items) <= len(secs)
    new_body = body
    if not ok:
        problems.append(f"{rel}: {len(items)} sidebar picks but only {len(secs)} product sections")
    else:
        for i, item in enumerate(items):
            if "<a " in item:
                continue
            nm = NAME_RE.search(item)
            if not nm:
                continue
            sid, sname = secs[i]
            n = norm(nm.group(1))
            named = [s for s, sn in secs if n and (n in sn or sn in n)]
            if named and sid not in named:
                problems.append(f"{rel}: sidebar entry {i + 1} '{nm.group(1)}' matches section #{named[0]}, not #{sid} by position")
                ok = False
                break
            new_item = item.replace(nm.group(0), f'<a href="#{sid}">{nm.group(0)}</a>', 1)
            new_body = new_body.replace(item, new_item, 1)
    if not ok:
        return
    new = old[:m.start()] + m.group(1) + TITLE + m.group(2) + new_body + old[m.start() + len(m.group(0)):]
    if new != old:
        if check:
            problems.append(f"{rel}: sidebar picks not renamed/linked (run build_sidebar_picks.py)")
        else:
            write(path, new)


def main():
    check = "--check" in sys.argv
    for path in sorted(ROOT.glob("blog/*.html")):
        process(path, check)
    if problems:
        print("\n".join(f"x {p}" for p in problems))
        sys.exit(1)
    print("sidebar picks OK" if check else "sidebar picks written")


if __name__ == "__main__":
    main()
