"""A small HTML reader for the static (no-browser) tests."""
from __future__ import annotations

import functools
from html.parser import HTMLParser

import pages as P

VOID = {"meta", "link", "img", "br", "hr", "input", "source", "area", "base", "col", "embed", "wbr", "track", "param"}


class Doc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.lang = ""
        self.metas: list[dict] = []
        self.links: list[dict] = []   # <link>
        self.anchors: list[dict] = []  # <a>
        self.images: list[dict] = []
        self.scripts: list[dict] = []
        self.iframes: list[dict] = []
        self.forms: list[dict] = []
        self.h1 = 0
        self.ids: list[str] = []
        self.elements_with_inline_handlers: list[str] = []
        self.inline_scripts: list[str] = []
        self._script_buf: list[str] | None = None
        self._stack: list[tuple[str, int]] = []
        self.errors: list[str] = []
        self.base_resources: list[tuple[str, str, str]] = []  # (tag, attr, url)

    def handle_starttag(self, tag, attrs):
        a = {k: (v if v is not None else "") for k, v in attrs}
        line = self.getpos()[0]
        if "id" in a:
            self.ids.append(a["id"])
        for k in a:
            if k.startswith("on") and len(k) > 2:
                self.elements_with_inline_handlers.append(f"<{tag} {k}> line {line}")
        if tag == "html":
            self.lang = a.get("lang", "")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            self.metas.append(a)
        elif tag == "link":
            self.links.append(a)
        elif tag == "a":
            self.anchors.append(dict(a, _line=line))
        elif tag == "img":
            self.images.append(a)
        elif tag == "script":
            self.scripts.append(a)
            self._script_buf = []
        elif tag == "iframe":
            self.iframes.append(a)
        elif tag == "form":
            self.forms.append(a)
        elif tag == "h1":
            self.h1 += 1
        for attr in ("src", "href", "action", "data-src", "poster"):
            if attr in a and tag not in ("a",):
                self.base_resources.append((tag, attr, a[attr]))
        if tag not in VOID:
            self._stack.append((tag, line))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._script_buf is not None:
            body = "".join(self._script_buf).strip()
            if body:
                self.inline_scripts.append(body)
            self._script_buf = None
        if tag in VOID:
            return
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                if i != len(self._stack) - 1:
                    inner = self._stack[i + 1][0]
                    self.errors.append(f"<{inner}> (line {self._stack[i + 1][1]}) not closed before </{tag}> (line {self.getpos()[0]})")
                del self._stack[i:]
                return
        self.errors.append(f"stray </{tag}> at line {self.getpos()[0]}")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._script_buf is not None:
            self._script_buf.append(data)

    def close(self):
        super().close()
        for tag, line in self._stack:
            if tag not in ("html", "body", "head"):
                self.errors.append(f"<{tag}> (line {line}) never closed")

    def meta(self, key: str, value: str, attr: str = "name") -> str | None:
        for m in self.metas:
            if m.get(attr, "").lower() == key.lower():
                return m.get(value, m.get("content"))
        return None

    def canonical(self) -> str | None:
        for link in self.links:
            if link.get("rel", "").lower() == "canonical":
                return link.get("href")
        return None


@functools.lru_cache(maxsize=None)
def parse(rel: str) -> Doc:
    doc = Doc()
    doc.feed(P.read(rel))
    doc.close()
    return doc


@functools.lru_cache(maxsize=None)
def jsonld(rel: str) -> tuple:
    """Every JSON-LD block on a page, parsed. A block that does not parse raises, which fails the test that asked."""
    import json
    import re

    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', P.read(rel), re.S):
        data = json.loads(m.group(1))
        out.extend(data if isinstance(data, list) else [data])
    return tuple(out)
