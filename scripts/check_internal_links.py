#!/usr/bin/env python3
"""
Find internal links that point at a page that doesn't exist.

A 404 on an internal link wastes crawl budget and loses the link-equity the
"Keep Reading" / nav / related-article wiring is meant to build — the kind of
mechanical SEO issue that's cheap to catch here instead of waiting for
Search Console to report it weeks later.

Root-relative hrefs (`/blog/...`) are resolved against the SITE ROOT, not the
linking file's own directory — resolving them the naive way produced 222
false positives the first time this was written.

    python3 scripts/check_internal_links.py            # exits 1 and prints broken links
"""
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent.parent
HREF_RE = re.compile(r'href="([^"]+)"')
SITE = "https://www.techfordad.com"


def resolve(href: str, page: Path) -> Path | None:
    href = href.split('#')[0].split('?')[0]
    if not href or href.startswith(('mailto:', 'tel:', 'javascript:')):
        return None
    if href.startswith(SITE):
        href = urlparse(href).path
    if href.startswith('http://') or href.startswith('https://'):
        return None  # external, not this script's job
    if href.startswith('/'):
        target = ROOT / href.lstrip('/')
    else:
        target = (page.parent / href).resolve()
    if target.suffix == '' and not target.exists():
        target = target.with_suffix('.html')
    return target


def main():
    pages = [*ROOT.glob('*.html'), *ROOT.glob('blog/*.html'), *ROOT.glob('guides/*.html'),
             *ROOT.glob('gift-guides/*.html')]
    broken = []
    for page in pages:
        html = page.read_text(encoding='utf-8')
        for m in HREF_RE.finditer(html):
            target = resolve(m.group(1), page)
            if target is None:
                continue
            if not target.exists():
                broken.append((page.relative_to(ROOT).as_posix(), m.group(1)))
    if broken:
        print(f'Found {len(broken)} broken internal link(s):')
        for page, href in broken:
            print(f'  {page} -> {href}')
        sys.exit(1)
    print(f'OK: internal links checked ({len(pages)} pages, 0 broken)')


if __name__ == '__main__':
    main()
