"""Write the "Table of Contents" box on every guide (guides/*.html), so guides follow the same layout as the reviews.

The box lists every <h2> section of the guide (not "Related ...", "Keep Reading" or the newsletter) and sits at the top of
`.about-body`, between <!-- guide-toc --> markers, so the script is idempotent. Sections without an id get one made from
their heading. Run by build_nav.py; never hand-edit the block.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK_RE = re.compile(r"[ \t]*<!-- guide-toc -->.*?<!-- /guide-toc -->[ \t]*\n\n?", re.S)
SKIP = ("Related Guides", "Related Articles", "Keep Reading", "Free Caregiver Tech Checklist")


def slug(text, used):
    s = re.sub(r"[^a-z0-9]+", "-", html.unescape(re.sub(r"<[^>]+>", "", text)).lower()).strip("-")[:48].strip("-") or "section"
    base, n = s, 2
    while s in used:
        s, n = f"{base}-{n}", n + 1
    used.add(s)
    return s


def build(text):
    text = BLOCK_RE.sub("", text)
    start = text.find('<div class="about-body">')
    if start == -1:
        return None
    end = text.find("</main>")
    body = text[start:end]
    used = set(re.findall(r'id="([^"]+)"', text))
    entries = []

    def fix(m):
        attrs, inner = m.group(1), m.group(2)
        label = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        if label in SKIP or label.startswith("Related"):
            return m.group(0)
        idm = re.search(r'id="([^"]+)"', attrs)
        if label.startswith("Sources and Where to Check"):  # the generated sources box carries the id on its <section>
            entries.append(("sources", inner.strip()))
            return m.group(0)
        if idm:
            sid = idm.group(1)
        else:
            sid = slug(inner, used)
            attrs = attrs + f' id="{sid}"'
        entries.append((sid, inner.strip()))
        return f"<h2{attrs}>{inner}</h2>"

    body = re.sub(r"<h2([^>]*)>(.*?)</h2>", fix, body, flags=re.S)
    if len(entries) < 3:
        return text
    lis = "\n".join(f'    <li><a href="#{sid}">{label}</a></li>' for sid, label in entries)
    box = ('<!-- guide-toc -->\n<div class="toc">\n  <p class="toc-title">Table of Contents</p>\n  <ol class="toc-plain">\n'
           + lis + "\n  </ol>\n</div>\n<!-- /guide-toc -->\n\n")
    head = '<div class="about-body">'
    return text[:start] + head + "\n\n" + box + body[len(head):].lstrip("\n") + text[end:]


def main():
    written = 0
    for path in sorted((ROOT / "guides").glob("*.html")):
        text = path.read_text(encoding="utf-8")
        if "http-equiv=\"refresh\"" in text or path.name == "index.html":
            continue
        new = build(text)
        if new is not None and new != text:
            path.write_text(new, encoding="utf-8")
            written += 1
    print(f"guide contents: {written} pages written")


if __name__ == "__main__":
    main()
