#!/usr/bin/env python3
"""
Build a product/price inventory of every article, guide and the homepage.

Used by the monthly content audit so research starts from one list instead of
re-reading 40 HTML files. Products that appear on several pages are grouped,
so each one is researched once and fixed everywhere.

    python3 scripts/audit_inventory.py            # markdown report to stdout
    python3 scripts/audit_inventory.py --json     # machine-readable
"""
import html as htmllib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
PRICE_RE = re.compile(r'(?:CA)?\$[\d,]+(?:\.\d{2})?(?:\s?CAD)?(?:/mo(?:nth)?|/year|/yr|/pair)?')
PRICE_LABEL_RE = re.compile(r'price|cost|fee', re.I)


def text_of(html: str) -> str:
    html = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html)).strip()


def product_cards(html: str) -> list[dict]:
    cards = []
    for chunk in re.split(r'<div class="product-card', html)[1:]:
        chunk = chunk[:8000]
        name = re.search(r'<h3>(.*?)</h3>', chunk, re.S)
        name = re.sub(r'<[^>]+>', '', name.group(1)).strip() if name else '?'
        specs = re.findall(r'spec-label">([^<]*)</span><span class="spec-val">([^<]*)<', chunk)
        prices = [f'{k}: {v}' for k, v in specs if PRICE_LABEL_RE.search(k)]
        # Canada cards keep the price in a .product-price line instead of specs
        pp = re.search(r'class="product-price">([^<]*)<', chunk)
        if pp:
            prices.append(pp.group(1).strip())
        links = re.findall(r'href="(https://www\.amazon\.[a-z.]+/[^"]+)"', chunk)
        cards.append({'name': name, 'prices': prices, 'amazon_links': links[:2]})
    return cards


def price_mentions(html: str) -> list[str]:
    """Every price outside the cards, with a little context, de-duplicated."""
    text = text_of(html)
    seen, out = set(), []
    for m in PRICE_RE.finditer(text):
        ctx = text[max(0, m.start() - 70):m.end() + 25]
        key = (m.group(0), ctx[40:110])
        if key not in seen:
            seen.add(key)
            out.append(ctx)
    return out


def page_meta(path: Path, html: str) -> dict:
    def grab(pattern):
        m = re.search(pattern, html, re.S)
        return m.group(1).strip() if m else None

    og = grab(r'property="og:image" content="([^"]+)"')
    og_ok = None
    if og:
        local = og.replace('https://www.techfordad.com/', '')
        og_ok = (ROOT / local).exists()
    hero = grab(r'<div class="article-hero">\s*<img src="([^"]+)"')
    hero_ok = (path.parent / hero).resolve().exists() if hero else None
    title = grab(r'<title>(.*?)</title>')
    desc = grab(r'<meta name="description" content="([^"]*)"')
    return {
        'title': title,
        'title_len': len(htmllib.unescape(title or '')),
        'description_len': len(htmllib.unescape(desc or '')),
        'date_modified': grab(r'"dateModified"\s*:\s*"([^"]+)"'),
        'updated_badge': grab(r'Updated (\w+ \d{4})'),
        'og_image': og,
        'og_image_exists': og_ok,
        'hero_image': hero,
        'hero_image_exists': hero_ok,
        'canada': 'lang="en-CA"' in html,
    }


def normalize(name: str) -> str:
    """Loose key so 'Apple Watch SE (3rd Gen, 2025)' and 'Apple Watch SE' group together."""
    n = re.sub(r'\(.*?\)', '', name.lower())
    n = re.sub(r'&amp;|[^a-z0-9+ ]', ' ', n)
    return ' '.join(n.split()[:4])


def main():
    pages = sorted((ROOT / 'blog').glob('*.html')) + sorted((ROOT / 'guides').glob('*.html'))
    pages = [p for p in pages if p.name != 'index.html'] + [ROOT / 'index.html']
    report, products = [], defaultdict(list)
    for p in pages:
        html = p.read_text(encoding='utf-8')
        rel = p.relative_to(ROOT).as_posix()
        cards = product_cards(html)
        entry = {'file': rel, **page_meta(p, html), 'products': cards,
                 'price_mentions': price_mentions(html)}
        report.append(entry)
        for c in cards:
            products[normalize(c['name'])].append({'file': rel, 'name': c['name'], 'prices': c['prices']})

    if '--json' in sys.argv:
        json.dump({'pages': report, 'products': products}, sys.stdout, indent=2)
        return

    print(f'# Inventory: {len(report)} pages, {len(products)} distinct products\n')
    print('## Products by name (research each once, fix every page it appears on)\n')
    for key in sorted(products):
        rows = products[key]
        print(f'- **{rows[0]["name"]}**')
        for r in rows:
            print(f'  - {r["file"]}: {"; ".join(r["prices"]) or "(no price in card)"}')
    print('\n## Page checks\n')
    for e in report:
        flags = []
        if e['title_len'] > 60: flags.append(f'title {e["title_len"]} chars')
        if e['description_len'] > 160: flags.append(f'description {e["description_len"]} chars')
        if e['og_image_exists'] is False: flags.append('og:image file missing')
        if e['og_image'] and e['og_image'].endswith('og-default.svg'): flags.append('og:image is the default')
        if e['file'].startswith('blog/') and not e['hero_image']: flags.append('no hero image')
        if e['hero_image_exists'] is False: flags.append('hero image file missing')
        print(f'- {e["file"]} (modified {e["date_modified"]}, badge {e["updated_badge"]})'
              + (f' — ⚠ {", ".join(flags)}' if flags else ''))
    print('\n## Every price mention, by page (includes guides and prose, not just cards)\n')
    for e in report:
        print(f'### {e["file"]}')
        for ctx in e['price_mentions']:
            print(f'- …{ctx}')
        print()


if __name__ == '__main__':
    main()
