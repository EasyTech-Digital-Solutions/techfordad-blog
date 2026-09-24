#!/usr/bin/env python3
"""
Pre-commit checks for content edits. Exits 1 if anything is wrong.

    python3 scripts/check_site.py          # check pages changed vs HEAD + products.json
    python3 scripts/check_site.py --all    # check every page

Checks:
- products.json: every tracked price appears in its page, and no two products
  on the same page share a dollar amount (the weekly price bot replaces by
  amount, so a shared amount would overwrite the other product's price).
- Each page: JSON-LD parses, tag balance unchanged vs HEAD, dateModified and
  the visible "Updated <Month Year>" badge agree, title <= 60 and meta
  description <= 160 chars, og:image file exists.
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
AMOUNT_RE = re.compile(r'\$[\d,]+(?:\.\d{2})?')
TAGS = ['div', 'ul', 'ol', 'li', 'p', 'table', 'tr', 'td', 'h2', 'h3', 'a', 'em', 'strong', 'section']
problems = []


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, encoding='utf-8').stdout


def balance(html):
    return {t: len(re.findall(rf'<{t}[\s>]', html)) - len(re.findall(rf'</{t}>', html)) for t in TAGS}


def check_products():
    for article in json.loads((ROOT / 'scripts' / 'products.json').read_text()):
        path = ROOT / article['file']
        if not path.exists():
            problems.append(f'products.json: {article["file"]} does not exist')
            continue
        html = path.read_text(encoding='utf-8')
        amounts = [AMOUNT_RE.match(p['price']).group(0) for p in article['products']]
        for product, amount in zip(article['products'], amounts):
            hits = len(re.findall(r'(?<![\d,.])' + re.escape(amount) + r'(?!\.?\d)', html))
            if hits == 0:
                problems.append(f'products.json: {product["name"]} {amount} not found in {article["file"]}')
            if amounts.count(amount) > 1:
                problems.append(f'products.json: {amount} tracked twice in {article["file"]} ({product["name"]})')


def check_page(rel):
    path = ROOT / rel
    html = path.read_text(encoding='utf-8')
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(m.group(1))
        except json.JSONDecodeError as e:
            problems.append(f'{rel}: invalid JSON-LD ({e})')
    old = git('show', f'HEAD:{rel}')
    if old:
        before, after = balance(old), balance(html)
        changed = {t: (before[t], after[t]) for t in TAGS if before[t] != after[t]}
        if changed:
            problems.append(f'{rel}: tag balance changed vs HEAD {changed}')
    modified = re.search(r'"dateModified"\s*:\s*"(\d{4})-(\d{2})', html)
    badge = re.search(r'Updated (\w+) (\d{4})', html)
    if modified and badge:
        month = date(int(modified.group(1)), int(modified.group(2)), 1).strftime('%B')
        if (badge.group(1), badge.group(2)) != (month, modified.group(1)):
            problems.append(f'{rel}: badge "Updated {badge.group(1)} {badge.group(2)}" != dateModified {modified.group(1)}-{modified.group(2)}')
    title = re.search(r'<title>(.*?)</title>', html, re.S)
    if title and len(title.group(1).strip()) > 60:
        problems.append(f'{rel}: title is {len(title.group(1).strip())} chars (max 60)')
    desc = re.search(r'<meta name="description" content="([^"]*)"', html)
    if desc and len(desc.group(1)) > 160:
        problems.append(f'{rel}: meta description is {len(desc.group(1))} chars (max 160)')
    og = re.search(r'property="og:image" content="https://www\.techfordad\.com/([^"]+)"', html)
    if og and not (ROOT / og.group(1)).exists():
        problems.append(f'{rel}: og:image {og.group(1)} does not exist')


def main():
    if '--all' in sys.argv:
        pages = [p.relative_to(ROOT).as_posix() for p in
                 [*ROOT.glob('blog/*.html'), *ROOT.glob('guides/*.html'), ROOT / 'index.html']]
    else:
        changed = git('diff', '--name-only', 'HEAD').split() + git('ls-files', '--others', '--exclude-standard').split()
        pages = [f for f in changed if f.endswith('.html') and (ROOT / f).exists()]
    check_products()
    for rel in pages:
        check_page(rel)
    if problems:
        print('\n'.join(f'✗ {p}' for p in problems))
        sys.exit(1)
    print(f'✓ products.json and {len(pages)} page(s) OK')


if __name__ == '__main__':
    main()
