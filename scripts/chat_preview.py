#!/usr/bin/env python3
"""Preview the "Ask TechForDad" chat on your own computer.

    python3 scripts/chat_preview.py            then open http://localhost:8000/
    python3 scripts/chat_preview.py 8080       another port

Serves the site like GitHub Pages and stands in for the Cloudflare Worker at /api/chat. There is no AI here: each
answer is the best-matching passage from the articles (labelled "Local preview"), with that section's real Check Price
buttons tagged the way the Worker tags them. Use it to check the panel, buttons, links and layout, not answer quality
(for that, run scripts/chat_eval.py against the deployed Worker).
"""
import functools
import http.server
import json
import os
import re
import socketserver
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_chat_index  # noqa: E402

ROOT = build_chat_index.ROOT
STOP = set("a an and are best can do does for from good how i in is it me my of on or the to what which who with you your "
           "mom dad parent parents senior seniors elderly".split())


def words(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 1]


def store_for(page, country):
    """Same choice as storeFor() in worker/src/index.js."""
    if page.startswith("/gift-guides/"):
        return "www.amazon.com", "techfordad-gifts-20"
    if country == "CA":
        return "www.amazon.ca", "abhikar91-20"
    return "www.amazon.com", "techfordad0b-20"


def answer(chunks, question, page, country):
    q = set(words(question))

    def score(c):
        head = set(words(c["title"] + " " + c["section"]))
        s = sum(2 for w in q if w in head) + sum(1 for w in q if w in c["text"].lower())
        if country and c["country"]:
            s *= 1.2 if c["country"] == country else 0.7
        return s

    ranked = sorted(chunks, key=score, reverse=True)
    if not q or score(ranked[0]) < 2:
        return {"id": "preview", "mode": "no_match", "sources": [],
                "answer": "I couldn't find that on TechForDad. I can help with technology for seniors."}
    top = ranked[0]
    body = top["text"].split("\n", 1)[-1].split()
    host, tag = store_for(page, country)
    products = [{"name": p["name"], "url": p["url"] + ("&" if "?" in p["url"] else "?") + "tag=" + tag}
                for p in json.loads(top["products"]) if f"//{host}/" in p["url"]][:3]
    seen, sources = set(), []
    for c in ranked[:5]:
        page_url = c["url"].split("#")[0]
        if page_url not in seen and len(sources) < 3:
            seen.add(page_url)
            sources.append({"title": c["title"], "url": c["url"]})
    excerpt = " ".join(body[:90]) + ("..." if len(body) > 90 else "")
    return {"id": "preview", "mode": "ai", "sources": sources, "products": products,
            "answer": "[Local preview - no AI on this computer. Best-matching passage:]\n" + excerpt}


def main(argv):
    port = int(argv[0]) if argv else 8000
    _, chunks = build_chat_index.build()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=ROOT, **k)

        def log_message(self, *a):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
            out = {"ok": True}
            if self.path == "/api/chat":
                out = answer(chunks, str(body.get("question", "")), str(body.get("page", "")), str(body.get("country", "")))
            data = json.dumps(out).encode("utf-8")
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), Handler) as server:
        print(f"Chat preview: http://localhost:{port}/  (Ctrl+C to stop)", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main(sys.argv[1:])
