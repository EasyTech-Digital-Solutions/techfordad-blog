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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_gift_guides  # noqa: E402  (source of truth for the gift guide list)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_VERSION = "20261001"

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
        return f.read().replace("\r\n", "\n")  # Windows checkouts use CRLF; the patterns below expect LF


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


GIFT_RE = re.compile(r'[ \t]*<a href="[^"]*gift-guides/index\.html">Gift Guides</a>[ \t]*\n?')
GIFT_BAR_RE = re.compile(r'[ \t]*<!-- gift-bar -->.*?<!-- /gift-bar -->[ \t]*\n?', re.S)


def render_gift_bar(base):
    href = base.replace("blog/", "gift-guides/") + "index.html"
    return f"""<!-- gift-bar -->
<div class="gift-bar" id="gift-bar" role="region" aria-label="Gift guides announcement">
  <div class="gift-bar-inner">
    <p class="gift-bar-text"><strong>Gift season:</strong> tech gifts your parents will actually use.</p>
    <a class="gift-bar-link" href="{href}">See the gift guides <span aria-hidden="true">&rarr;</span></a>
    <button type="button" class="gift-bar-close" aria-label="Dismiss this announcement">&times;</button>
  </div>
</div>
<!-- /gift-bar -->
"""


GIFT_BLOCK_RE = re.compile(r'[ \t]*<!-- gift-dropdown -->.*?<!-- /gift-dropdown -->[ \t]*\n?', re.S)


def render_gifts(base, indent):
    gbase = base.replace("blog/", "gift-guides/")
    pad = " " * indent
    lines = [
        f"{pad}<!-- gift-dropdown -->",
        f'{pad}<div class="nav-dropdown nav-dropdown-gifts">',
        f'{pad}  <button type="button" class="nav-dropdown-toggle" aria-expanded="false" aria-haspopup="true">Gift Guides <span class="caret" aria-hidden="true"></span></button>',
        f'{pad}  <div class="nav-dropdown-menu">',
        f'{pad}    <a class="nav-dropdown-all" href="{gbase}index.html">Browse all gift guides &rarr;</a>',
    ]
    for g in build_gift_guides.GUIDES:
        lines.append(f'{pad}    <a href="{gbase}{g["slug"]}.html">{html.escape(g["short"])}</a>')
    lines += [f"{pad}  </div>", f"{pad}</div>", f"{pad}<!-- /gift-dropdown -->", ""]
    return "\n".join(lines)


GUIDE_LABELS = {
    "home-safety-checklist.html": "Home safety checklist",
    "fall-prevention-tech.html": "Fall prevention technology",
    "7-tech-essentials-checklist.html": "7 tech essentials for a senior home",
    "gps-trackers.html": "GPS trackers for dementia",
    "hearing-aids.html": "Hearing aid buying guide",
    "caregiver-resources.html": "Caregiver resources",
}
GUIDES_BLOCK_RE = re.compile(r'[ \t]*<!-- guides-dropdown -->.*?<!-- /guides-dropdown -->[ \t]*\n?', re.S)


def collect_guides():
    items = []
    for path in sorted(glob.glob(os.path.join(ROOT, "guides", "*.html"))):
        name = os.path.basename(path)
        if name == "index.html":
            continue
        text = read(path)
        if re.search(r'<meta[^>]+name="robots"[^>]+noindex', text, re.I) or 'http-equiv="refresh"' in text:
            continue  # noindex pages and redirect stubs stay out of the menu
        m = re.search(r"<title>(.*?)</title>", text, re.S)
        items.append((GUIDE_LABELS.get(name) or clean_title(m.group(1) if m else name), name))
    order = {name: i for i, name in enumerate(GUIDE_LABELS)}
    items.sort(key=lambda item: order.get(item[1], len(order)))
    return items


def render_guides(base, indent):
    gbase = base.replace("blog/", "guides/")
    pad = " " * indent
    lines = [
        f"{pad}<!-- guides-dropdown -->",
        f'{pad}<div class="nav-dropdown nav-dropdown-guides">',
        f'{pad}  <button type="button" class="nav-dropdown-toggle" aria-expanded="false" aria-haspopup="true">Guides <span class="caret" aria-hidden="true"></span></button>',
        f'{pad}  <div class="nav-dropdown-menu">',
        f'{pad}    <a class="nav-dropdown-all" href="{gbase}index.html">Browse all guides &rarr;</a>',
    ]
    for label, name in collect_guides():
        lines.append(f'{pad}    <a href="{gbase}{name}">{html.escape(label)}</a>')
    lines += [f"{pad}  </div>", f"{pad}</div>", f"{pad}<!-- /guides-dropdown -->", ""]
    return "\n".join(lines)


# On pages inside guides/ the link is written as plain "index.html", elsewhere as ".../guides/index.html".
GUIDES_LINK_RE = re.compile(r'[ \t]*<a href="(?:[^"]*guides/)?index\.html">Guides</a>[ \t]*\n?')

ABOUT_ITEMS = [
    ("About Us", "about.html"),
    ("Our Story", "our-story.html"),
    ("Contact", "contact.html"),
    ("Privacy Policy", "privacy-policy.html"),
    ("How We Review", "how-we-review.html"),
    ("Affiliate Disclosure", "affiliate-disclosure.html"),
]
ABOUT_LINK_RE = re.compile(r'[ \t]*<a href="(?:\.\./|/)?about\.html">About</a>[ \t]*\n?')
ABOUT_BLOCK_RE = re.compile(r'[ \t]*<!-- about-dropdown -->.*?<!-- /about-dropdown -->[ \t]*\n?', re.S)


def render_about(base, indent):
    root = base.replace("blog/", "")
    pad = " " * indent
    lines = [
        f"{pad}<!-- about-dropdown -->",
        f'{pad}<div class="nav-dropdown nav-dropdown-about">',
        f'{pad}  <button type="button" class="nav-dropdown-toggle" aria-expanded="false" aria-haspopup="true">About <span class="caret" aria-hidden="true"></span></button>',
        f'{pad}  <div class="nav-dropdown-menu">',
    ]
    for label, name in ABOUT_ITEMS:
        lines.append(f'{pad}    <a href="{root}{name}">{html.escape(label)}</a>')
    lines += [f"{pad}  </div>", f"{pad}</div>", f"{pad}<!-- /about-dropdown -->", ""]
    return "\n".join(lines)
SEASON_RE = re.compile(r'[ \t]*<script src="[^"]*js/season\.js[^"]*"></script>[ \t]*\n?')
CSS_LINK_RE = re.compile(r'([ \t]*)<link rel="stylesheet" href="((?:\.\./|/)?)css/style\.css[^"]*"\s*/?>[ \t]*\n')


def inject_season_script(text):
    """Load js/season.js right after the stylesheet so the seasonal theme is set before first paint."""
    text = SEASON_RE.sub("", text)
    m = CSS_LINK_RE.search(text)
    if not m:
        return text
    tag = f'{m.group(1)}<script src="{m.group(2)}js/season.js?v={ASSET_VERSION}"></script>\n'
    return text[:m.end()] + tag + text[m.end():]


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

    # Top-level "Gift Guides" link, placed just before "Guides"
    new_inner = GIFT_RE.sub("", GIFT_BLOCK_RE.sub("", new_inner))
    gm = GUIDES_BLOCK_RE.search(new_inner) or GUIDES_LINK_RE.search(new_inner)
    if gm:
        indent = len(gm.group(0)) - len(gm.group(0).lstrip(" \t"))
        new_inner = new_inner[:gm.start()] + render_gifts(base, indent) + render_guides(base, indent) + new_inner[gm.end():]
    am = ABOUT_BLOCK_RE.search(new_inner) or ABOUT_LINK_RE.search(new_inner)
    if am:
        indent = len(am.group(0)) - len(am.group(0).lstrip(" \t"))
        new_inner = new_inner[:am.start()] + render_about(base, indent) + new_inner[am.end():]

    new = text[:m.start(2)] + new_inner + text[m.end(2):]
    new = GIFT_BAR_RE.sub("", new)
    if "gift-guides" not in os.path.relpath(path, ROOT).replace("\\", "/").split("/")[0]:
        hm = re.search(r"\n<header>", new)
        if hm:
            new = new[:hm.start() + 1] + render_gift_bar(base) + new[hm.start() + 1:]
    new = re.sub(r'(css/style\.css)(\?v=\d+)?"', rf'\1?v={ASSET_VERSION}"', new)
    new = re.sub(r'(js/main\.js)(\?v=\d+)?"', rf'\1?v={ASSET_VERSION}"', new)
    new = inject_season_script(new)
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
    import build_hreflang
    build_hreflang.main()


if __name__ == "__main__":
    main()
