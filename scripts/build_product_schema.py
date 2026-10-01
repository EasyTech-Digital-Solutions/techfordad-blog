"""Add Product/Offer JSON-LD for every product card on a "Best X" article.

The site had Article, FAQPage and BreadcrumbList schema but nothing telling
Google what products are being compared, or their prices. This reads each
article's own product-card markup (the same cards a visitor sees) and
writes an ItemList of Products with Offers into a new <!-- product-schema -->
block in <head>, right before </head>.

Deliberately NOT added: review/aggregateRating. The "Our Score: X/10" shown
on cards is TechForDad's own editorial judgment, not a crowd-sourced rating;
tagging it as AggregateRating would misrepresent an opinion as a review
count to Google, the structured-data equivalent of the fabricated-testing
claims removed earlier from this site. Price is a verifiable fact, so only
price is added.

Usage: python3 build_product_schema.py [--check]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted((ROOT / "blog").glob("*.html")) + sorted((ROOT / "gift-guides").glob("*.html"))
SITE = "https://www.techfordad.com"

BLOCK_RE = re.compile(r'[ \t]*<!-- product-schema -->.*?<!-- /product-schema -->[ \t]*\r?\n?', re.S)
CARD_SPLIT = re.compile(r'(?=<div class="product-card)')
H3_RE = re.compile(r'<h3[^>]*>(.*?)</h3>', re.S)
SPEC_PRICE_RE = re.compile(
    r'<span class="spec-label">(?:Price|Cost|Monthly Cost|Monthly Fee|Device Cost|'
    r'Upfront Cost|Equipment)</span>'
    r'<span class="spec-val">(.*?)</span>', re.S)
PRODUCT_PRICE_RE = re.compile(r'<div class="product-price">(.*?)</div>', re.S)
LINK_RE = re.compile(r'<a href="(https://www\.amazon\.[a-z.]+/[^"]*)"[^>]*class="btn-check-price"', re.S)
DOLLAR_RE = re.compile(r'\$\s?([\d,]+(?:\.\d{1,2})?)')
TAG_RE = re.compile(r'<[^>]+>')
problems = []


def strip_tags(s):
    return re.sub(r'\s+', ' ', TAG_RE.sub('', s)).strip()


def extract_cards(html):
    """Split the whole page on product-card boundaries; each chunk up to the
    next one (or 4000 chars, to bound a runaway match) is one card."""
    cards = []
    starts = [m.start() for m in CARD_SPLIT.finditer(html)]
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else min(start + 6000, len(html))
        chunk = html[start:end]
        h3 = H3_RE.search(chunk)
        if not h3:
            continue
        name = strip_tags(h3.group(1))
        price_m = SPEC_PRICE_RE.search(chunk) or PRODUCT_PRICE_RE.search(chunk)
        price_text = strip_tags(price_m.group(1)) if price_m else ""
        link_m = LINK_RE.search(chunk)
        url = link_m.group(1) if link_m else None
        cards.append({"name": name, "price_text": price_text, "url": url})
    return cards


def parse_price(text):
    m = DOLLAR_RE.search(text)
    if not m:
        return None
    return m.group(1).replace(",", "")


def build_schema(cards, currency):
    items = []
    for i, c in enumerate(cards, 1):
        product = {"@type": "Product", "name": c["name"]}
        if c["url"]:
            product["url"] = c["url"]
        price = parse_price(c["price_text"])
        if price and c["url"]:
            product["offers"] = {
                "@type": "Offer",
                "price": price,
                "priceCurrency": currency,
                "availability": "https://schema.org/InStock",
                "url": c["url"],
            }
        items.append({"@type": "ListItem", "position": i, "item": product})
    if not items:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": items,
    }


def apply_page(path, check):
    html = path.read_text(encoding="utf-8")
    base = BLOCK_RE.sub("", html)
    if "product-card" not in base:
        return  # a vs-article or guide with no ranked product cards; skip
    cards = extract_cards(base)
    cards = [c for c in cards if c["name"]]
    if not cards:
        problems.append(f"{path.name}: has product-card markup but no cards parsed")
        return
    currency = "CAD" if 'lang="en-CA"' in base else "USD"
    schema = build_schema(cards, currency)
    if schema is None:
        return
    block_json = json.dumps(schema, ensure_ascii=False, indent=2)
    block = (
        "  <!-- product-schema -->\n"
        '  <script type="application/ld+json">\n'
        f"  {block_json}\n"
        "  </script>\n"
        "  <!-- /product-schema -->\n"
    )
    if "</head>" not in base:
        problems.append(f"{path.name}: no </head> found")
        return
    new = base.replace("</head>", block + "</head>", 1)
    if check:
        if new != html:
            problems.append(f"{path.name}: product schema missing or out of date (run build_product_schema.py)")
    elif new != html:
        path.write_text(new, encoding="utf-8")


def main():
    check = "--check" in sys.argv
    n = 0
    for p in PAGES:
        before = p.read_text(encoding="utf-8")
        apply_page(p, check)
        after = p.read_text(encoding="utf-8")
        if before != after:
            n += 1
    if problems:
        print("\n".join(f"x {msg}" for msg in problems))
        sys.exit(1)
    print(f"product schema: {n} pages {'OK' if check else 'written'}")


if __name__ == "__main__":
    main()
