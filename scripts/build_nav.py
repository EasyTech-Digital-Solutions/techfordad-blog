#!/usr/bin/env python3
"""Regenerate the "All Reviews" dropdown in the site header on every page.

The site is hand-authored static HTML, so the header is copied into each page.
This script rewrites the marked dropdown block in every page's <nav id="site-nav">
from the current contents of blog/, so a new article shows up in the menu after:

    python3 scripts/build_nav.py

It is idempotent. The first run replaces the plain "All Reviews" link; later runs
replace the block between the <!-- nav-dropdown --> markers. Pages marked noindex
are left out of the menu. Articles ending in -canada.html go under Canada, the
rest under USA.
"""
import glob
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_VERSION = "20260929"

# Short menu labels. Anything not listed falls back to a cleaned-up page title.
LABELS = {
    "best-medical-alert-systems.html": "Medical alert systems",
    "medical-alert-no-monthly-fee.html": "Medical alerts, no monthly fee",
    "life-alert-vs-medical-guardian.html": "Life Alert vs Medical Guardian",
    "best-cell-phones-for-seniors.html": "Cell phones",
    "jitterbug-vs-iphone-for-seniors.html": "Jitterbug vs iPhone",
    "best-cordless-phones-for-seniors.html": "Cordless phones",
    "best-tablets-for-seniors.html": "Tablets",
    "how-to-set-up-ipad-for-elderly-parent.html": "iPad setup for parents",
    "best-e-readers-for-seniors.html": "E-readers",
    "best-smartwatches-for-seniors.html": "Smartwatches",
    "best-gps-trackers-for-seniors.html": "GPS trackers",
    "best-hearing-aids-for-seniors.html": "Hearing aids",
    "best-blood-pressure-monitors-for-seniors.html": "Blood pressure monitors",
    "best-home-security-for-seniors.html": "Home security",
    "best-smart-home-devices-for-seniors.html": "Smart home devices",
    "best-alexa-devices-for-seniors.html": "Alexa devices",
    "best-pill-organizers-for-seniors.html": "Pill organizers",
    "best-sleep-trackers-for-seniors.html": "Sleep trackers",
    "best-tv-remotes-for-seniors.html": "TV remotes",
    "best-medical-alert-systems-canada.html": "Medical alert systems",
    "best-hearing-aids-canada.html": "Hearing aids",
    "best-cell-phones-for-seniors-canada.html": "Cell phones",
    "best-cell-phone-plans-for-seniors-canada.html": "Cell phone plans",
    "best-cordless-phones-for-seniors-canada.html": "Cordless phones",
    "best-tablets-for-seniors-canada.html": "Tablets",
    "best-e-readers-for-seniors-canada.html": "E-readers",
    "best-smartwatches-for-seniors-canada.html": "Smartwatches",
    "best-gps-trackers-for-seniors-canada.html": "GPS trackers",
    "best-blood-pressure-monitors-canada.html": "Blood pressure monitors",
    "best-home-security-for-seniors-canada.html": "Home security",
    "best-video-doorbells-for-seniors-canada.html": "Video doorbells",
}

NAV_RE = re.compile(r'(<nav id="site-nav">)(.*?)(</nav>)', re.S)
BLOCK_RE = re.compile(r'[ \t]*<!-- nav-dropdown -->.*?<!-- /nav-dropdown -->[ \t]*\n?', re.S)
PLAIN_RE = re.compile(r'[ \t]*<a href="((?:\.\./|/)?blog/)index\.html">All Reviews</a>[ \t]*\n?')


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def clean_title(title):
    t = html.unescape(title).split("|")[0].strip()
    t = re.sub(r"\b20\d\d\b", "", t)
    t = re.sub(r"\b(for Seniors|for Elderly Parents|in Canada|Canada)\b", "", t, flags=re.I)
    t = re.sub(r"^(Best|Top)\s+", "", t, flags=re.I)
    t = re.sub(r"[:\-]\s*(Reviewed.*|Compared.*)$", "", t)
    t = re.sub(r"\s+", " ", t).strip(" :-")
    return t[:1].upper() + t[1:]


def collect():
    usa, canada = [], []
    for path in sorted(glob.glob(os.path.join(ROOT, "blog", "*.html"))):
        name = os.path.basename(path)
        if name == "index.html":
            continue
        text = read(path)
        if re.search(r'<meta[^>]+name="robots"[^>]+noindex', text, re.I):
            continue
        m = re.search(r"<title>(.*?)</title>", text, re.S)
        label = LABELS.get(name) or clean_title(m.group(1) if m else name)
        (canada if name.endswith("-canada.html") else usa).append((label, name))
    order = {name: i for i, name in enumerate(LABELS)}
    for group in (usa, canada):
        group.sort(key=lambda item: order.get(item[1], len(order)))
    return usa, canada


def render(base, usa, canada, indent):
    img = base.replace("blog/", "images/")
    pad = " " * indent

    def col(title, flag, size, alt, items):
        lines = [
            f'{pad}      <div class="nav-dropdown-col">',
            f'{pad}        <span class="nav-dropdown-label"><img class="flag" src="{img}{flag}" alt="" width="{size[0]}" height="{size[1]}">{title}</span>',
        ]
        for label, name in items:
            lines.append(f'{pad}        <a href="{base}{name}">{html.escape(label)}</a>')
        lines.append(f"{pad}      </div>")
        return "\n".join(lines)

    return "\n".join([
        f"{pad}<!-- nav-dropdown -->",
        f'{pad}<div class="nav-dropdown">',
        f'{pad}  <button type="button" class="nav-dropdown-toggle" aria-expanded="false" aria-haspopup="true">All Reviews <span class="caret" aria-hidden="true"></span></button>',
        f'{pad}  <div class="nav-dropdown-menu">',
        f'{pad}    <a class="nav-dropdown-all" href="{base}index.html">Browse all reviews &rarr;</a>',
        f'{pad}    <div class="nav-dropdown-cols">',
        col("USA", "flag-us.svg", (16, 9), "USA", usa),
        col("Canada", "flag-ca.svg", (12, 11), "Canada", canada),
        f"{pad}    </div>",
        f"{pad}  </div>",
        f"{pad}</div>",
        f"{pad}<!-- /nav-dropdown -->",
        "",
    ])


def process(path, usa, canada):
    text = read(path)
    m = NAV_RE.search(text)
    if not m:
        return False
    inner = m.group(2)

    existing = re.search(r'class="nav-dropdown-all" href="((?:\.\./|/)?blog/)index\.html"', inner)
    plain = PLAIN_RE.search(inner)
    if existing:
        base = existing.group(1)
    elif plain:
        base = plain.group(1)
    else:
        return False

    first = BLOCK_RE.search(inner) or plain
    indent = len(first.group(0)) - len(first.group(0).lstrip(" \t"))
    block = render(base, usa, canada, indent)

    if BLOCK_RE.search(inner):
        new_inner = BLOCK_RE.sub(lambda _m: block, inner, count=1)
    else:
        new_inner = PLAIN_RE.sub(lambda _m: block, inner, count=1)

    new = text[:m.start(2)] + new_inner + text[m.end(2):]
    new = re.sub(r'(css/style\.css)(\?v=\d+)?"', rf'\1?v={ASSET_VERSION}"', new)
    new = re.sub(r'(js/main\.js)(\?v=\d+)?"', rf'\1?v={ASSET_VERSION}"', new)
    if new != text:
        write(path, new)
        return True
    return False


def main():
    usa, canada = collect()
    changed = skipped = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)):
        if os.sep + ".git" + os.sep in path:
            continue
        try:
            if process(path, usa, canada):
                changed += 1
        except Exception as exc:  # keep going, report at the end
            skipped += 1
            print(f"skipped {os.path.relpath(path, ROOT)}: {exc}", file=sys.stderr)
    print(f"USA {len(usa)} | Canada {len(canada)} | pages updated {changed} | skipped {skipped}")
    for title, items in (("USA", usa), ("Canada", canada)):
        print(title + ": " + ", ".join(label for label, _ in items))


if __name__ == "__main__":
    main()
