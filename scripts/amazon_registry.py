#!/usr/bin/env python3
"""Registry of every Amazon link on the site, and a check that the pages match it.

    python3 scripts/amazon_registry.py --update   # rebuild scripts/amazon-registry.json from the pages
    python3 scripts/amazon_registry.py            # check the pages against the registry (exit 1 on problems)

scripts/amazon-registry.json lists each distinct Amazon destination once: id, product name, country (us/ca),
URL without the affiliate tag, ASIN when the link is a product page, and the pages that use it.
The check (also run by check_site.py --all) fails when:
  * an Amazon link on any page is not in the registry (add it with --update after reviewing the diff),
  * a link is used on a page the registry does not list for it, or a registry entry is used nowhere,
  * the affiliate tag is wrong for the section (US pages techfordad0b-20, Canada pages abhikar91-20,
    Gift Guides techfordad-gifts-20) or missing,
  * the store does not match the page (a Canada page must link amazon.ca; US, neutral and gift pages amazon.com).
"price" is copied from scripts/products.json for products the weekly price bot tracks there (that file stays
the source of truth for those numbers); it is null otherwise. Manual "note" fields survive --update.
"""
import glob
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote_plus, urlparse

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "scripts" / "amazon-registry.json"
TAGS = {"us": "techfordad0b-20", "ca": "abhikar91-20", "gifts": "techfordad-gifts-20"}
LINK_RE = re.compile(r'<a ((?:(?!>).)*?href="(https?://(?:www\.)?amazon\.(com|ca)[^"]*)"(?:(?!>).)*?)>(.*?)</a>', re.S)
GENERIC = re.compile(r"^(amazon(\.ca)?|check .*|browse .*|see .*|buy .*|here|link)$", re.I)
problems = []


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def pages():
    files = []
    for pat in ("*.html", "blog/*.html", "guides/*.html", "gift-guides/*.html"):
        files += glob.glob(str(ROOT / pat))
    return sorted(Path(f).relative_to(ROOT).as_posix() for f in files)


def page_country(rel):
    return "ca" if rel.endswith("-canada.html") else "us"


def expected_tag(rel, store):
    if store == "ca":
        return TAGS["ca"]
    return TAGS["gifts"] if rel.startswith("gift-guides/") else TAGS["us"]


def canonical(url):
    """Amazon URL without the affiliate tag and other tracking parameters."""
    u = urlparse(html.unescape(url))
    host = "amazon." + ("ca" if u.netloc.endswith(".ca") else "com")
    q = parse_qs(u.query)
    query = ""
    if u.path == "/s" and "k" in q:
        query = "?k=" + quote_plus(" ".join(q["k"][0].split()))
    return f"https://www.{host}{u.path}{query}"


def asin_of(url):
    m = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url)
    return m.group(1) if m else None


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def collect():
    """{canonical url: {store, names Counter, pages set, tags found per page}} plus every raw link occurrence."""
    found = defaultdict(lambda: {"store": None, "names": Counter(), "pages": set()})
    occurrences = []
    for rel in pages():
        text = read(ROOT / rel).replace("\r\n", "\n")
        if 'http-equiv="refresh"' in text:
            continue
        for m in LINK_RE.finditer(text):
            attrs, raw, store, inner = m.group(1), m.group(2), m.group(3), m.group(4)
            url = canonical(raw)
            tag = (parse_qs(urlparse(html.unescape(raw)).query).get("tag") or [None])[0]
            rec = found[url]
            rec["store"] = store
            rec["pages"].add(rel)
            label = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", inner))).strip()
            dp = re.search(r'data-product="([^"]*)"', attrs)
            if dp:
                rec["names"][html.unescape(dp.group(1))] += 3
            elif label and not GENERIC.match(label):
                rec["names"][label] += 1
            occurrences.append((rel, url, store, tag))
    return found, occurrences


def product_name(url, names):
    if names:
        return names.most_common(1)[0][0]
    q = parse_qs(urlparse(url).query)
    if "k" in q:
        return unquote_plus(q["k"][0])
    return url.rsplit("/", 1)[-1]


def tracked_prices():
    """{normalised product name: price} from products.json (owned by the weekly price bot)."""
    out = {}
    try:
        for art in json.loads(read(ROOT / "scripts" / "products.json")):
            for p in art["products"]:
                out[slug(p["name"])] = p["price"]
    except (OSError, ValueError, KeyError):
        pass
    return out


def build(found, old):
    prices = tracked_prices()
    notes = {e["url"]: e.get("note") for e in old.get("links", []) if e.get("note")}
    entries, used_ids = [], Counter()
    for url in sorted(found):
        rec = found[url]
        name = product_name(url, rec["names"])
        base = f"{rec['store']}-{slug(name)[:48]}"
        used_ids[base] += 1
        eid = base if used_ids[base] == 1 else f"{base}-{used_ids[base]}"
        # exact name match, US links only: products.json holds US (USD) prices, and near-matches confuse models
        price = prices.get(slug(name)) if rec["store"] == "com" else None
        entry = {"id": eid, "name": name, "country": rec["store"] and ("ca" if rec["store"] == "ca" else "us"),
                 "url": url, "kind": "product" if asin_of(url) else "search", "asin": asin_of(url),
                 "price": price, "used_in": sorted(rec["pages"])}
        if url in notes:
            entry["note"] = notes[url]
        entries.append(entry)
    entries.sort(key=lambda e: (e["country"], e["id"]))
    return {"tags": TAGS, "links": entries}


def check(found, occurrences, reg):
    by_url = {e["url"]: e for e in reg.get("links", [])}
    for url, rec in found.items():
        e = by_url.get(url)
        if not e:
            problems.append(f"not in registry: {url} (used on {', '.join(sorted(rec['pages']))[:80]}), run amazon_registry.py --update")
            continue
        missing = rec["pages"] - set(e["used_in"])
        if missing:
            problems.append(f"registry entry {e['id']} does not list page(s): {', '.join(sorted(missing))}")
    for e in reg.get("links", []):
        if e["url"] not in found:
            problems.append(f"registry entry {e['id']} is not used on any page (remove it with --update)")
        else:
            extra = set(e["used_in"]) - found[e["url"]]["pages"]
            if extra:
                problems.append(f"registry entry {e['id']} lists page(s) that no longer use it: {', '.join(sorted(extra))}")
    for rel, url, store, tag in occurrences:
        want = expected_tag(rel, store)
        if tag != want:
            problems.append(f"{rel}: {url} has tag {tag!r}, expected {want!r}")
        if store != page_country(rel) and not (store == "com" and page_country(rel) == "us"):
            if not (store == "ca" and page_country(rel) == "ca"):
                problems.append(f"{rel}: links to amazon.{store} but the page is {'Canada' if page_country(rel) == 'ca' else 'US/neutral'}")


def main():
    found, occurrences = collect()
    if "--update" in sys.argv:
        old = json.loads(read(REGISTRY)) if REGISTRY.exists() else {}
        new = build(found, old)
        REGISTRY.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        n_price = sum(1 for e in new["links"] if e["price"])
        print(f"registry written: {len(new['links'])} links ({sum(1 for e in new['links'] if e['kind'] == 'product')} product pages, "
              f"{sum(1 for e in new['links'] if e['kind'] == 'search')} searches), {n_price} with a tracked price")
        check_after = True
    else:
        check_after = True
    reg = json.loads(read(REGISTRY)) if REGISTRY.exists() else {"links": []}
    if check_after:
        check(found, occurrences, reg)
    if problems:
        print("\n".join(f"x {p}" for p in problems[:40]))
        if len(problems) > 40:
            print(f"... and {len(problems) - 40} more")
        sys.exit(1)
    if "--update" not in sys.argv:
        print(f"amazon registry OK: {len(reg['links'])} links, {len(occurrences)} occurrences")


if __name__ == "__main__":
    main()
