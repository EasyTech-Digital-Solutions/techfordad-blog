#!/usr/bin/env python3
"""Add a "Which One Should You Buy?" decision section and a top-pick Amazon button after the comparison table.

    python3 scripts/build_buying_summary.py          # write / refresh
    python3 scripts/build_buying_summary.py --check  # verify only, exit 1 on problems

Everything is read from the page's own product sections (nothing is invented): each pick's label
(badge or the heading tagline), price, first "pro" and first "con". Every name links to its review section.
  * US pages: the existing "Quick Picks" list at the top is replaced by the decision section (id="top-picks" kept).
  * Canada pages: the section is added straight after the "Top Picks at a Glance" table.
  * A "Check Price on Amazon" button for the #1 pick follows the comparison table (skipped when the #1 pick is not
    sold on Amazon, e.g. monitored medical alert services, which link to the provider instead).
Blocks sit between <!-- buy-summary --> / <!-- table-cta --> markers, so the script is idempotent.
To cover another page, add it to PAGES with its product-section ids in ranking order.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# page -> ("us"|"ca", [section ids in ranking order])
PAGES = {
    "blog/best-tablets-for-seniors.html": ("us", ["ipad", "fire-hd10", "ipad-mini", "samsung", "fire-8"]),
    "blog/best-tablets-for-seniors-canada.html": ("ca", ["ipad", "ipad-air", "samsung-tab-a9-plus", "fire-hd-10", "lenovo-tab"]),
    "blog/best-cell-phones-for-seniors.html": ("us", ["jitterbug", "iphone-se", "jitterbug-smart", "doro", "galaxy"]),
    "blog/best-cell-phones-for-seniors-canada.html": ("ca", ["iphone16", "samsung-a36", "samsung-a16", "doro", "artfone"]),
    "blog/best-medical-alert-systems.html": ("us", ["best-overall", "best-value", "best-mobile", "best-apple", "best-budget"]),
    "blog/best-medical-alert-systems-canada.html": ("ca", ["medicalert", "telus", "lifeline", "apple-watch"]),
    "blog/best-e-readers-for-seniors.html": ("us", ["best-overall", "best-arthritis", "best-large-screen", "best-budget", "best-library"]),
    "blog/best-e-readers-for-seniors-canada.html": ("ca", ["kobo-clara-bw", "kobo-libra-colour", "kindle-paperwhite", "kobo-clara-colour"]),
}
HEADING = "Which One Should You Buy?"
BUY_RE = re.compile(r"\n?[ \t]*<!-- buy-summary -->.*?<!-- /buy-summary -->[ \t]*\n?", re.S)
CTA_RE = re.compile(r"[ \t]*<!-- table-cta -->.*?<!-- /table-cta -->[ \t]*\n?", re.S)
problems = []


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def write(p, t):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


def plain(s):
    """Strip tags, keep entities (so the result can go straight back into HTML)."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def sentence(s):
    return s.rstrip(" .;:")


def section(text, sid):
    m = re.search(rf'<h2 id="{re.escape(sid)}"[^>]*>(.*?)</h2>(.*?)(?=<h2 |\Z)', text, re.S)
    return (m.group(1), m.group(2)) if m else (None, None)


def pick(text, sid):
    h2, body = section(text, sid)
    if h2 is None:
        problems.append(f"section #{sid} not found")
        return None
    name = plain(re.search(r"<h3[^>]*>(.*?)</h3>", body, re.S).group(1)) if "<h3" in body else plain(h2)
    name = re.split(r":", re.sub(r"^\d+\.\s*", "", name))[0].strip()
    badge = re.search(r'class="product-badge-small"[^>]*>(.*?)</span>', body, re.S)
    tagline = re.split(r"[:,]", re.sub(r"^\d+\.\s*", "", plain(h2)), maxsplit=1)
    if badge:
        label = re.sub(r"\s+20\d\d$", "", plain(badge.group(1)))
    elif len(tagline) > 1:
        label = tagline[1].strip()
    else:
        label = plain(re.search(r'class="product-badge"[^>]*>(.*?)</div>', body, re.S).group(1)) if 'class="product-badge"' in body else name
    price = None
    m = re.search(r'<span class="spec-label">(?:Price|Monthly Cost|Cost)</span><span class="spec-val">(.*?)</span>', body, re.S)
    if m:
        price = plain(m.group(1))
    else:
        m = re.search(r'class="product-price"[^>]*>(.*?)</div>', body, re.S)
        if m:
            pm = re.match(r"(.*?\d[\d,\.]*\s*CAD)", plain(m.group(1)))
            price = pm.group(1) if pm else None
    if price and "(" in price:
        price = re.sub(r"\s*\(.*$", "", price).strip() or price  # drop notes like "(64GB model)"
    pro = re.search(r'class="pros".*?<li>(.*?)</li>', body, re.S)
    con = re.search(r'class="cons".*?<li>(.*?)</li>', body, re.S)
    link = re.search(r'<a [^>]*href="(https?://(?:www\.)?amazon\.(?:com|ca)[^"]*)"[^>]*class="btn-check-price"', body) or \
        re.search(r'<a [^>]*class="btn-check-price"[^>]*href="(https?://(?:www\.)?amazon\.(?:com|ca)[^"]*)"', body)
    return dict(id=sid, name=name, label=label, price=price, pro=plain(pro.group(1)) if pro else None,
                con=plain(con.group(1)) if con else None, url=link.group(1) if link else None)


def render_summary(picks, country):
    lines = ["<!-- buy-summary -->"]
    if country == "ca":
        lines.append(f'<h2 id="which-one">{HEADING}</h2>')
    else:
        lines.append(f'<h2 id="top-picks">{HEADING}</h2>')
    lines.append("<p>Short on time? Here is who each pick suits best, with its main reason to buy and the one thing to watch for. Each name links to the full review below.</p>")
    lines.append('<ul class="buy-decision">')
    for p in picks:
        head = f'<strong>{p["label"]}:</strong> <a href="#{p["id"]}">{p["name"]}</a>'
        if p["price"]:
            head += f' ({p["price"]})'
        bits = []
        if p["pro"]:
            bits.append(f'Why: {sentence(p["pro"])}.')
        if p["con"]:
            bits.append(f'Watch out: {sentence(p["con"])}.')
        tail = f' <span class="buy-why">{" ".join(bits)}</span>' if bits else ""
        lines.append(f"  <li>{head}{tail}</li>")
    lines.append("</ul>")
    if "overall" in picks[0]["label"].lower():
        lines.append(f'<p class="buy-note">Not sure? Start with the <a href="#{picks[0]["id"]}">{picks[0]["name"]}</a>. It is our overall pick.</p>')
    lines.append("<!-- /buy-summary -->")
    return "\n".join(lines) + "\n"


def render_cta(top, country):
    store = "Amazon.ca" if country == "ca" else "Amazon"
    label = f"Check Price on {store} →"
    aria = html.escape(f"Check Price on {store}: {html.unescape(top['name'])}", quote=True)
    prod = html.escape(html.unescape(top["name"]), quote=True)
    return ("<!-- table-cta -->\n"
            '<p class="table-cta">'
            f'<a href="{top["url"]}" target="_blank" rel="sponsored noopener" class="btn-check-price" '
            f'data-cta="comparison_table" data-product="{prod}" aria-label="{aria}">{label}</a> '
            f'<span>Our top pick: <a href="#{top["id"]}">{top["name"]}</a></span></p>\n'
            "<!-- /table-cta -->\n")


def process(rel, check):
    country, ids = PAGES[rel]
    path = ROOT / rel
    text = read(path)
    base = CTA_RE.sub("", BUY_RE.sub("", text))
    picks = [pick(base, i) for i in ids]
    if any(p is None for p in picks):
        return
    # 1. decision section
    summary = render_summary(picks, country)
    if country == "us":
        if BUY_RE.search(text):  # already generated: refresh in place
            new = BUY_RE.sub(lambda _m: ("\n" if _m.group(0).startswith("\n") else "") + summary, text, count=1)
        else:  # first run: replace the hand-written Quick Picks list
            new, n = re.subn(r'<h2 id="top-picks"[^>]*>[^<]*</h2>\s*<ul>.*?</ul>\n', lambda _m: summary, text, count=1, flags=re.S)
            if not n:
                problems.append(f"{rel}: Quick Picks list not found")
                return
    else:
        new = CTA_RE.sub("", BUY_RE.sub("", text))
        m = re.search(r'<div class="comparison-table-wrap">.*?</table>\s*</div>\n', new, re.S)
        if not m:
            problems.append(f"{rel}: comparison table not found")
            return
        new = new[:m.end()] + "\n" + summary + new[m.end():]
    # 2. CTA after the comparison table
    top = picks[0]
    new = CTA_RE.sub("", new)
    if top["url"]:
        if country == "us":
            i = new.find('<h2 id="comparison"')
            j = new.find("</table>", i) if i != -1 else -1
            if j == -1:
                problems.append(f"{rel}: comparison table not found for the button")
            else:
                k = j + len("</table>")
                wrap = re.match(r"\s*</div>\n", new[k:])
                k = k + wrap.end() if wrap else k
                new = new[:k] + ("" if new[k - 1] == "\n" else "\n") + render_cta(top, country) + new[k:]
        else:
            m = re.search(r"<!-- /buy-summary -->", new)
            i = new.find('<div class="comparison-table-wrap">')
            k = new.find("</table>", i)
            wrap = re.match(r"\s*</div>\n", new[k + 8:])
            k = k + 8 + (wrap.end() if wrap else 0)
            new = new[:k] + render_cta(top, country) + new[k:]
    # 3. TOC label (US pages)
    new = re.sub(r'(<a href="#top-picks">)[^<]*(</a>)', rf"\g<1>{HEADING}\g<2>", new)
    if check:
        if new != text:
            problems.append(f"{rel}: buying summary missing or out of date (run build_buying_summary.py)")
    elif new != text:
        write(path, new)
    return top["url"] is not None


def main():
    check = "--check" in sys.argv
    no_cta = []
    for rel in PAGES:
        if process(rel, check) is False:
            no_cta.append(rel.split("/")[-1])
    if problems:
        print("\n".join(f"x {p}" for p in problems))
        sys.exit(1)
    print(f"buying summary: {len(PAGES)} pages {'OK' if check else 'written'}" + (f" (no Amazon button, #1 pick not on Amazon: {', '.join(no_cta)})" if no_cta else ""))


if __name__ == "__main__":
    main()
