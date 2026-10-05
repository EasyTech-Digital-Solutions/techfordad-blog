#!/usr/bin/env python3
"""Write the "Sources and Where to Check the Details" block at the bottom of a guide.

    python3 scripts/build_sources.py            # write / refresh the blocks
    python3 scripts/build_sources.py --check    # verify only, exit 1 on problems (no network)
    python3 scripts/build_sources.py --verify   # open every source URL and report its status (network)

The sources live in scripts/sources.json (page -> list of sources). Each page block sits just before the
"Keep Reading" box, between <!-- sources --> markers, so the script is idempotent. Rules:
  * only add a link you have opened and that really covers the topic; "used_for" says what the page covers, never more;
  * https only, no Amazon links (those belong on Check Price buttons, with the affiliate tag);
  * "checked" in sources.json is the date the links were last verified: move it forward only after --verify.
"""
import concurrent.futures as cf
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "scripts" / "sources.json"
KINDS = [("maker", "From the makers and providers"), ("authority", "Health and medical organizations"), ("independent", "Independent reviews and testing"), ("official", "Government sources and programs")]
BLOCK_RE = re.compile(r"[ \t]*<!-- sources -->.*?<!-- /sources -->[ \t]*\n?", re.S)
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
problems = []


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def write(p, t):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


def esc(s):
    return html.escape(s, quote=True)


def pretty_date(iso):
    y, m, d = iso.split("-")
    return f"{MONTHS[int(m) - 1]} {int(d)}, {y}"


def render(rel, entry, checked):
    root = "../" if rel.count("/") else ""
    lines = ["<!-- sources -->", '<section class="sources" id="sources">', "  <h2>Sources and Where to Check the Details</h2>",
             f'  <p>Prices, plans and features change, so the maker or provider\'s own page is the final word. These are the pages behind this guide, plus independent reviews you can compare with ours. Links last checked {pretty_date(checked)}. See <a href="{root}how-we-review.html">how we review products</a>.</p>']
    for kind, heading in KINDS:
        items = [s for s in entry["sources"] if s["kind"] == kind]
        if not items:
            continue
        lines.append(f"  <h3>{heading}</h3>")
        lines.append("  <ul>")
        for s in items:
            lines.append(f'    <li><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a> <span>{esc(s["used_for"])}</span></li>')
        lines.append("  </ul>")
    if entry.get("note"):
        lines.append(f'  <p class="sources-note">{esc(entry["note"])}</p>')
    lines += ["</section>", "<!-- /sources -->"]
    return "\n".join(lines) + "\n"


def insert(text, block):
    text = BLOCK_RE.sub("", text)
    i = text.find("<!-- gift-links -->")  # order at the foot of a review: FAQ, How We Chose, Sources, gift ideas, Keep Reading
    if i == -1:
        i = text.find("<!-- related -->")
    if i == -1:
        return None
    i = text.rfind("\n", 0, i) + 1
    return text[:i] + block + text[i:]


def validate(data):
    seen_kinds = {k for k, _ in KINDS}
    for rel, entry in data["pages"].items():
        if not (ROOT / rel).exists():
            problems.append(f"{rel}: page does not exist")
        if len(entry["sources"]) < 3:
            problems.append(f"{rel}: fewer than 3 sources")
        urls = [s["url"] for s in entry["sources"]]
        for u in urls:
            if not u.startswith("https://"):
                problems.append(f"{rel}: {u} is not https")
            if re.search(r"://(?:www\.)?amazon\.", u):
                problems.append(f"{rel}: {u} is an Amazon link (use a Check Price button)")
        for u in {u for u in urls if urls.count(u) > 1}:
            problems.append(f"{rel}: duplicate source {u}")
        for s in entry["sources"]:
            if s["kind"] not in seen_kinds:
                problems.append(f"{rel}: unknown kind {s['kind']!r}")
            if not s.get("title") or not s.get("used_for"):
                problems.append(f"{rel}: source without title or used_for: {s.get('url')}")
    if not re.match(r"\d{4}-\d{2}-\d{2}$", data["checked"]):
        problems.append("sources.json: 'checked' must be YYYY-MM-DD")


def verify(data):
    UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36", "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-US,en;q=0.9"}
    jobs = {(rel, s["url"]): s for rel, e in data["pages"].items() for s in e["sources"]}
    urls = sorted({u for _, u in jobs})

    def probe(u):
        try:
            return u, urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).status
        except urllib.error.HTTPError as e:
            return u, e.code
        except Exception as e:
            return u, type(e).__name__

    results = {}
    with cf.ThreadPoolExecutor(6) as ex:
        for u, st in ex.map(probe, urls):
            results[u] = st
    bad = 0
    skip_urls = {u for (rel, u), s in jobs.items() if s.get("skip_verify")}
    for u in urls:
        st = results[u]
        if st != 200:
            if u in skip_urls:
                print(f"  skipped (site blocks scripted checks: open it in a browser yourself): {st} {u}")
            else:
                bad += 1
                print(f"  FAIL {st} {u}")
    print(f"verified {len(urls)} distinct URLs: {len(urls) - bad - len([u for u in urls if results[u] != 200 and u in skip_urls])} OK, {bad} failing")
    return bad == 0


def main():
    data = json.loads(read(DATA))
    validate(data)
    if "--verify" in sys.argv:
        ok = verify(data)
        sys.exit(0 if ok and not problems else 1)
    check = "--check" in sys.argv
    for rel, entry in data["pages"].items():
        path = ROOT / rel
        if not path.exists():
            continue
        text = read(path)
        new = insert(text, render(rel, entry, data["checked"]))
        if new is None:
            problems.append(f"{rel}: no Keep Reading block to sit before (run build_related.py first)")
            continue
        if check:
            if new != text:
                problems.append(f"{rel}: sources block missing or out of date (run build_sources.py)")
        elif new != text:
            write(path, new)
    if problems:
        print("\n".join(f"x {p}" for p in problems))
        sys.exit(1)
    print(f"sources: {len(data['pages'])} pages {'OK' if check else 'written'}")


if __name__ == "__main__":
    main()
