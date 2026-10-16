#!/usr/bin/env python3
"""Build what the "Ask TechForDad" chat answers from: the site's own articles, cut into short chunks.

    python3 scripts/build_chat_index.py            write js/chat-index.json (run by build_nav.py)
    python3 scripts/build_chat_index.py --check    exit 1 if js/chat-index.json is out of date
    python3 scripts/build_chat_index.py --upload   also sync the chunks to Cloudflare Vectorize (GitHub Action)

js/chat-index.json is a small page list (title, URL, country, description, section headings) that the chat
searches in the browser when the AI is unavailable (daily free allowance used up, or the Worker is down).

--upload needs CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN and CHAT_VECTORIZE_INDEX in the environment. It embeds
only chunks whose text changed (each vector stores a hash of its text) and deletes vectors for text that is gone,
so a normal push costs a few neurons, not a full re-embed of the site.
"""
import glob
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "js", "chat-index.json")
FOLDERS = ("blog", "guides", "gift-guides")
EMBED_MODEL = "@cf/baai/bge-small-en-v1.5"
MAX_WORDS = 220

# Generated or off-topic blocks that would only add noise to answers (ads, newsletter, related links, sources list).
DROP_BLOCKS = re.compile(
    r"<!-- (ad:[a-z_]+|related|sources|gift-links|nl-fields|hreflang|product-schema) -->.*?<!-- /(ad|related|sources|gift-links|nl-fields|hreflang|product-schema) -->",
    re.S)
DROP_TAGS = re.compile(r"<(script|style|noscript|svg|button|form|nav)\b.*?</\1>", re.S | re.I)
DROP_ASIDES = re.compile(r"<aside\b.*?</aside>", re.S | re.I)
# Page furniture inside the article: breadcrumb, hero tag line and byline, affiliate disclosure box, contents lists.
SKIP_CLASSES = {"breadcrumb", "card-tag", "article-meta", "article-disclaimer", "toc-box", "toc-plain"}
AMAZON = re.compile(r"https://www\.amazon\.(com|ca)/")
BLOCK_TAGS = {"p", "li", "h3", "h4", "tr", "div", "section", "table", "ul", "ol", "dd", "dt", "br", "blockquote"}


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def pages():
    for folder in FOLDERS:
        for path in sorted(glob.glob(os.path.join(ROOT, folder, "*.html"))):
            if os.path.basename(path) == "index.html":
                continue
            text = read(path)
            if 'http-equiv="refresh"' in text or re.search(r'<meta[^>]+name="robots"[^>]+noindex', text, re.I):
                continue
            yield os.path.relpath(path, ROOT).replace(os.sep, "/"), text


def country(rel, text):
    if re.search(r'<html[^>]+lang="en-CA"', text):
        return "CA"
    if rel.startswith(("blog/", "gift-guides/")):
        return "US"
    return ""


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def untagged(url):
    """The Amazon URL without its affiliate tag: the Worker adds the right tag for the page the chat is open on."""
    parts = urlsplit(url)
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if k != "tag"])
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


class Sections(HTMLParser):
    """Splits the article into [h2 id, h2 text, body text, products] sections, keeping paragraph and table-row breaks.
    Products are the section's own "Check Price on Amazon" buttons, so a chat answer can offer the same button."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = [["", "", [], []]]
        self.in_h2 = False
        self.h2_id = ""
        self.h2_text = []
        self.in_h1 = False
        self.h1 = []
        self.in_cta = False
        self.skip = None  # [tag, depth] while inside a SKIP_CLASSES element

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.skip:
            if tag == self.skip[0]:
                self.skip[1] += 1
            return
        if SKIP_CLASSES & set((a.get("class") or "").split()):
            self.skip = [tag, 1]
            return
        if tag == "a" and "btn-check-price" in (a.get("class") or "") and a.get("data-product") \
                and AMAZON.match(a.get("href") or ""):
            self.in_cta = True
            products = self.sections[-1][3]
            if all(p["name"] != a["data-product"] for p in products):
                products.append({"name": a["data-product"], "url": untagged(a["href"])})
        elif tag == "h2":
            self.in_h2, self.h2_id, self.h2_text = True, a.get("id") or "", []
        elif tag == "h1":
            self.in_h1 = True
        elif tag in ("td", "th"):
            self.sections[-1][2].append(" | ")
        elif tag in BLOCK_TAGS:
            self.sections[-1][2].append("\n")

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip[0]:
                self.skip[1] -= 1
                if not self.skip[1]:
                    self.skip = None
            return
        if tag == "h2" and self.in_h2:
            self.in_h2 = False
            self.sections.append([self.h2_id, clean("".join(self.h2_text)), [], []])
        elif tag == "h1":
            self.in_h1 = False
        elif tag == "a":
            self.in_cta = False
        elif tag in BLOCK_TAGS:
            self.sections[-1][2].append("\n")

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_h2:
            self.h2_text.append(data)
        elif self.in_h1:
            self.h1.append(data)
        elif not self.in_cta:
            self.sections[-1][2].append(data)


def parse(rel, text):
    desc = re.search(r'<meta name="description" content="([^"]*)"', text)
    main = re.search(r'<main id="main">(.*?)</main>', text, re.S)
    body = main.group(1) if main else text
    body = body.split('<section class="newsletter"')[0]
    body = DROP_ASIDES.sub(" ", DROP_TAGS.sub(" ", DROP_BLOCKS.sub(" ", body)))
    p = Sections()
    p.feed(body)
    title = clean("".join(p.h1)) or rel
    sections = []
    for sid, heading, parts, products in p.sections:
        paras = [clean(x) for x in "".join(parts).split("\n")]
        paras = [x.strip(" |") for x in paras if len(x.strip(" |")) > 2]
        if paras:
            sections.append((sid, heading or "Introduction", paras, products))
    return {
        "url": "/" + rel,
        "title": title,
        "country": country(rel, text),
        "description": clean(html.unescape(desc.group(1))) if desc else "",
        "sections": sections,
    }


def chunks(page):
    """~220-word chunks that never cross a section, each prefixed with the page title and section for context."""
    out = []
    for sid, heading, paras, products in page["sections"]:
        buf, words = [], 0
        for para in paras:
            n = len(para.split())
            if buf and words + n > MAX_WORDS:
                out.append((sid, heading, "\n".join(buf), products))
                buf, words = [], 0
            buf.append(para)
            words += n
        if buf:
            out.append((sid, heading, "\n".join(buf), products))
    result = []
    for i, (sid, heading, body, products) in enumerate(out):
        if len(body.split()) > MAX_WORDS * 2:  # one huge paragraph or table: keep the first part
            body = " ".join(body.split()[:MAX_WORDS * 2])
        text = f"{page['title']} - {heading}\n{body}"
        url = page["url"] + (f"#{sid}" if sid else "")
        products_json = json.dumps(products, ensure_ascii=False)  # Vectorize metadata values must be flat
        result.append({
            "id": f"{page['url'].lstrip('/')}#{i}",
            "url": url,
            "title": page["title"],
            "section": heading,
            "country": page["country"],
            "text": text,
            "products": products_json,
            "hash": hashlib.sha1((text + products_json).encode("utf-8")).hexdigest()[:16],
        })
    return result


def build():
    site = [parse(rel, text) for rel, text in pages()]
    index = {
        "_readme": "Generated by scripts/build_chat_index.py (run by build_nav.py). Used by js/chat.js when the AI is unavailable.",
        "pages": [{
            "u": p["url"], "t": p["title"], "c": p["country"], "d": p["description"],
            "h": [[sid, heading] for sid, heading, _, _ in p["sections"] if sid],
        } for p in site],
    }
    all_chunks = [c for p in site for c in chunks(p)]
    return json.dumps(index, ensure_ascii=False, indent=0) + "\n", all_chunks


# ---------------------------------------------------------------- Cloudflare sync (--upload)

def api(method, path, body=None, content_type="application/json"):
    url = f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/{path}"
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}", "Content-Type": content_type})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())["result"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(2 ** attempt * 3)
                continue
            sys.exit(f"Cloudflare API {method} {path}: HTTP {e.code} {e.read()[:500]!r}")


def upload(all_chunks):
    index = os.environ["CHAT_VECTORIZE_INDEX"]
    base = f"vectorize/v2/indexes/{index}"
    existing, cursor = [], None
    while True:
        res = api("GET", f"{base}/list?count=1000" + (f"&cursor={cursor}" if cursor else ""))
        existing += [v["id"] for v in res.get("vectors", [])]
        cursor = res.get("nextCursor")
        if not res.get("isTruncated") or not cursor:
            break
    wanted = {c["id"]: c for c in all_chunks}
    stale = [i for i in existing if i not in wanted]
    have_hash = {}
    present = [i for i in existing if i in wanted]
    for i in range(0, len(present), 20):
        for v in api("POST", f"{base}/get_by_ids", {"ids": present[i:i + 20]}) or []:
            have_hash[v["id"]] = (v.get("metadata") or {}).get("hash")
    todo = [c for c in all_chunks if have_hash.get(c["id"]) != c["hash"]]
    print(f"chat index: {len(all_chunks)} chunks, {len(todo)} new or changed, {len(stale)} to delete")
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        vectors = api("POST", f"ai/run/{EMBED_MODEL}", {"text": [c["text"] for c in batch]})["data"]
        lines = [json.dumps({"id": c["id"], "values": v, "metadata": {
            k: c[k] for k in ("url", "title", "section", "country", "text", "products", "hash")}}) for c, v in zip(batch, vectors)]
        api("POST", f"{base}/upsert", "\n".join(lines), content_type="application/x-ndjson")
    for i in range(0, len(stale), 100):
        api("POST", f"{base}/delete_by_ids", {"ids": stale[i:i + 100]})


def main(argv=()):
    text, all_chunks = build()
    if "--check" in argv:
        current = read(OUT) if os.path.exists(OUT) else ""
        if current != text:
            print("js/chat-index.json is out of date: run python3 scripts/build_chat_index.py")
            return 1
        print(f"chat index OK ({len(all_chunks)} chunks)")
        return 0
    if not os.path.exists(OUT) or read(OUT) != text:
        with open(OUT, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    if "--upload" in argv:
        upload(all_chunks)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
