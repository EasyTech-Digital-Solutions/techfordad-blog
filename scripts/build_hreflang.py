#!/usr/bin/env python3
"""Add reciprocal hreflang to the genuine US / Canada article pairs.

    python3 scripts/build_hreflang.py          # write tags + sitemap alternates
    python3 scripts/build_hreflang.py --check  # verify only, exit 1 on problems

Each pair gets, in its <head> (right after the canonical) and in sitemap.xml:
    en-US -> US page, en-CA -> Canada page, x-default -> US page
Every page keeps its own self-referencing canonical. A pair is skipped when either page is
missing or noindex (hreflang to a noindex page is ignored by Google), and pages with no twin
get nothing. Add a new pair to PAIRS below; never pair pages that are not translations of the
same topic. build_nav.py runs this at the end.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://www.techfordad.com"

# (US file, Canada file) in blog/
PAIRS = [
    ("best-blood-pressure-monitors-for-seniors.html", "best-blood-pressure-monitors-canada.html"),
    ("best-cell-phones-for-seniors.html", "best-cell-phones-for-seniors-canada.html"),
    ("best-cordless-phones-for-seniors.html", "best-cordless-phones-for-seniors-canada.html"),
    ("best-e-readers-for-seniors.html", "best-e-readers-for-seniors-canada.html"),
    ("best-gps-trackers-for-seniors.html", "best-gps-trackers-for-seniors-canada.html"),
    ("best-hearing-aids-for-seniors.html", "best-hearing-aids-canada.html"),
    ("best-home-security-for-seniors.html", "best-home-security-for-seniors-canada.html"),
    ("best-medical-alert-systems.html", "best-medical-alert-systems-canada.html"),
    ("best-smartwatches-for-seniors.html", "best-smartwatches-for-seniors-canada.html"),
    ("best-tablets-for-seniors.html", "best-tablets-for-seniors-canada.html"),
    ("best-video-doorbells-for-seniors.html", "best-video-doorbells-for-seniors-canada.html"),
]

HEAD_RE = re.compile(r'[ \t]*<!-- hreflang -->.*?<!-- /hreflang -->[ \t]*\r?\n?', re.S)
CANON_RE = re.compile(r'([ \t]*)(<link rel="canonical" href="([^"]+)"\s*/?>)([ \t]*\r?\n)')
XH_NS = 'xmlns:xhtml="http://www.w3.org/1999/xhtml"'
problems = []


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write(p, text):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def url(name):
    return f"{SITE}/blog/{name}"


def live_pairs():
    out = []
    for us, ca in PAIRS:
        ok = True
        for name in (us, ca):
            path = ROOT / "blog" / name
            if not path.exists():
                problems.append(f"{name}: pair page missing")
                ok = False
            elif re.search(r'<meta name="robots"[^>]*noindex', read(path)):
                ok = False  # deliberate: noindex pages are excluded
        if ok:
            out.append((us, ca))
    return out


def tags(us, ca, indent, nl):
    lines = [
        "<!-- hreflang -->",
        f'<link rel="alternate" hreflang="en-US" href="{url(us)}"/>',
        f'<link rel="alternate" hreflang="en-CA" href="{url(ca)}"/>',
        f'<link rel="alternate" hreflang="x-default" href="{url(us)}"/>',
        "<!-- /hreflang -->",
    ]
    return "".join(f"{indent}{l}{nl}" for l in lines)


def apply_head(name, us, ca, check):
    path = ROOT / "blog" / name
    text = read(path)
    base = HEAD_RE.sub("", text)
    m = CANON_RE.search(base)
    if not m:
        problems.append(f"{name}: no canonical link found")
        return
    if m.group(3) != url(name):
        problems.append(f"{name}: canonical {m.group(3)} is not self-referencing")
    nl = "\r\n" if "\r\n" in m.group(4) else "\n"
    new = base[:m.end()] + tags(us, ca, m.group(1), nl) + base[m.end():]
    if check:
        if new != text:
            problems.append(f"{name}: hreflang block missing or out of date (run build_hreflang.py)")
    elif new != text:
        write(path, new)


def alt_lines(us, ca, indent, nl):
    return "".join(f"{indent}{l}{nl}" for l in [
        f'<xhtml:link rel="alternate" hreflang="en-US" href="{url(us)}"/>',
        f'<xhtml:link rel="alternate" hreflang="en-CA" href="{url(ca)}"/>',
        f'<xhtml:link rel="alternate" hreflang="x-default" href="{url(us)}"/>',
    ])


def apply_sitemap(pairs, check):
    path = ROOT / "sitemap.xml"
    text = read(path)
    nl = "\r\n" if "\r\n" in text else "\n"
    new = re.sub(r'[ \t]*<xhtml:link [^>]*/>[ \t]*\r?\n', "", text)
    if XH_NS not in new:
        new = new.replace("<urlset ", f"<urlset {XH_NS} ", 1)
    for us, ca in pairs:
        for name in (us, ca):
            pat = re.compile(r'(<loc>' + re.escape(url(name)) + r'</loc>[ \t]*\r?\n)([ \t]*)')
            m = pat.search(new)
            if not m:
                problems.append(f"sitemap.xml: {name} not listed")
                continue
            new = new[:m.end(1)] + alt_lines(us, ca, m.group(2), nl) + new[m.end(1):]
    if check:
        if new != text:
            problems.append("sitemap.xml: hreflang alternates missing or out of date")
    elif new != text:
        write(path, new)


def verify(pairs):
    """Every hreflang target exists, is indexable, and carries the same set (reciprocity)."""
    for us, ca in pairs:
        for name in (us, ca):
            text = read(ROOT / "blog" / name)
            found = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', text))
            want = {"en-US": url(us), "en-CA": url(ca), "x-default": url(us)}
            if found != want:
                problems.append(f"{name}: hreflang set {found} != {want}")
    paired = {n for pr in pairs for n in pr}
    for path in (ROOT).rglob("*.html"):
        if ".git" in path.parts:
            continue
        if path.parent.name == "blog" and path.name in paired:
            continue
        if 'hreflang="' in read(path):
            problems.append(f"{path.relative_to(ROOT).as_posix()}: has hreflang but is not in a live pair")


def main():
    check = "--check" in sys.argv
    pairs = live_pairs()
    for us, ca in pairs:
        apply_head(us, us, ca, check)
        apply_head(ca, us, ca, check)
    apply_sitemap(pairs, check)
    verify(pairs)
    if problems:
        print("\n".join(f"x {p}" for p in problems))
        sys.exit(1)
    print(f"hreflang: {len(pairs)} pairs ({len(pairs) * 2} pages) {'OK' if check else 'written'}")


if __name__ == "__main__":
    main()
