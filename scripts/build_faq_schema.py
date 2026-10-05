"""Keep each page's FAQPage JSON-LD identical to the FAQ a visitor can open on the page.

Google wants FAQ structured data to match visible content. The schema used to be hand-written next to the visible
`div.faq-item` blocks and drifted (different questions, shorter answers). This reads the visible FAQ and rewrites
the existing FAQPage block in <head> from it, so the two can never disagree. Pages with no FAQPage block are left
alone (adding an FAQ is a content decision), and gift-guides/ are skipped because build_gift_guides.py owns those.

Usage: python3 build_faq_schema.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted((ROOT / "blog").glob("*.html")) + sorted((ROOT / "guides").glob("*.html"))

LD_RE = re.compile(r'([ \t]*)<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', re.S)
ITEM_RE = re.compile(r'<div class="faq-q"[^>]*>(.*?)</div>\s*<div class="faq-a"[^>]*>(.*?)</div>', re.S)


def plain(s):
    s = re.sub(r"</(p|li)>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def main():
    changed = 0
    for path in PAGES:
        text = path.read_text(encoding="utf-8")
        items = [(plain(q), plain(a)) for q, a in ITEM_RE.findall(text)]
        if not items:
            continue
        for m in LD_RE.finditer(text):
            try:
                data = json.loads(m.group(2))
            except ValueError:
                # a hand edit broke the block's JSON: rebuild it from the visible FAQ rather than leave it invalid
                if '"@type": "FAQPage"' not in m.group(2):
                    continue
                data = {"@context": "https://schema.org", "@type": "FAQPage"}
            if data.get("@type") != "FAQPage":
                continue
            head = json.dumps({k: v for k, v in data.items() if k != "mainEntity"}, ensure_ascii=False, indent=2)
            qs = ",\n".join(
                '      {\n        "@type": "Question",\n        "name": %s,\n        "acceptedAnswer": {"@type": "Answer", "text": %s}\n      }'
                % (json.dumps(q, ensure_ascii=False), json.dumps(a, ensure_ascii=False)) for q, a in items)
            body = head[:-2].replace("\n", "\n  ") + ',\n    "mainEntity": [\n' + qs + "\n    ]\n  }"
            new = f'{m.group(1)}<script type="application/ld+json">\n  {body}\n  </script>'
            if new != m.group(0):
                text = text.replace(m.group(0), new, 1)
                path.write_text(text, encoding="utf-8")
                changed += 1
            break
    print(f"FAQ schema: {changed} pages updated")


if __name__ == "__main__":
    main()
