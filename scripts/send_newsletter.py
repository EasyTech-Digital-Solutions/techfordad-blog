#!/usr/bin/env python3
"""Render a monthly newsletter and create it in Mailchimp as a DRAFT campaign.

    python3 scripts/send_newsletter.py docs/newsletters/2026-10.json            # render preview only
    python3 scripts/send_newsletter.py docs/newsletters/2026-10.json --draft    # create the draft in Mailchimp
    python3 scripts/send_newsletter.py docs/newsletters/2026-10.json --draft --test-to you@example.com

This script never sends to subscribers. You review the draft in Mailchimp and press Send yourself.
The API key is read from the MAILCHIMP_API_KEY environment variable and must never be written into
the repo (it is public). The server prefix (e.g. us2) is the part of the key after the last dash.
"""
import argparse
import base64
import html
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "scripts" / "newsletter_template.html"
AUDIENCE_ID = "8cf3d53e8d"  # the audience behind the site's signup form
FROM_NAME = "TechForDad"
FROM_EMAIL = "hello@techfordad.com"
# The logo is served from the live site, so the file must be committed and published first.
LOGO_PATH = "images/logo/techfordad-logo-email.png"
LOGO_URL = "https://www.techfordad.com/" + LOGO_PATH
TEMPLATE_LOGO_SRC = "../" + LOGO_PATH  # what the template shows when opened on its own; replaced when rendering

E = html.escape
# Colours and fonts mirror css/style.css (navy #1B3A6B, amber #E8A020, Playfair Display headings).
P = 'style="margin:0 0 16px;"'
H2 = "style=\"margin:0 0 10px;font-family:'Playfair Display',Georgia,'Times New Roman',serif;font-size:24px;line-height:1.3;font-weight:800;color:#1B3A6B;\""
LINK = 'style="color:#1B3A6B;font-weight:600;"'


def para(text):
    return f"    <p {P}>{E(text)}</p>"


def button(btn):
    return (
        '    <table role="presentation" cellpadding="0" cellspacing="0"><tr><td bgcolor="#E8A020" style="background:#E8A020;border-radius:8px;">\n'
        f'      <a href="{E(btn["url"])}" style="display:inline-block;padding:14px 28px;color:#1B3A6B;'
        f'font-size:18px;font-weight:bold;text-decoration:none;">{E(btn["text"])}</a>\n'
        "    </td></tr></table>"
    )


def render_block(block, first):
    parts = []
    if not first:
        parts.append('  <tr><td style="padding:16px 24px 0;"><hr style="border:0;border-top:1px solid #E5E7EB;"></td></tr>')
    inner = [f"    <h2 {H2}>{E(block['heading'])}</h2>"]
    inner += [para(t) for t in block.get("paragraphs", [])]
    if block.get("bullets"):
        items = "\n".join(
            f'      <li style="margin-bottom:10px;"><a href="{E(b["url"])}" {LINK}>{E(b["link_text"])}</a>: {E(b["desc"])}</li>'
            for b in block["bullets"]
        )
        inner.append(f'    <ul style="margin:0 0 8px;padding-left:22px;">\n{items}\n    </ul>')
    if block.get("button"):
        inner.append(button(block["button"]))
    for a in block.get("after", []):
        inner.append(
            f'    <p style="margin:16px 0 0;">{E(a.get("text", ""))}<a href="{E(a["url"])}" {LINK}>{E(a["link_text"])}</a>{E(a.get("tail", ""))}</p>'
        )
    parts.append('  <tr><td style="padding:8px 24px;">\n' + "\n".join(inner) + "\n  </td></tr>")
    return "\n\n".join(parts)


def render(content, logo_url=LOGO_URL):
    blocks = "\n\n".join(render_block(b, i == 0) for i, b in enumerate(content["blocks"]))
    out = TEMPLATE.read_text(encoding="utf-8")
    for key, val in {
        TEMPLATE_LOGO_SRC: E(logo_url),
        "{{title}}": E(content["title"]),
        "{{preview}}": E(content["preview"]),
        "{{intro}}": "\n".join(para(t) for t in content["intro"]),
        "{{blocks}}": blocks,
    }.items():
        out = out.replace(key, val)
    return out


def render_fragment(content):
    """Body content only (no header, footer or page wrapper), for pasting into a text block's
    source-code view, e.g. the Mailchimp form-builder welcome email, which supplies its own logo and footer."""
    blocks = "\n\n".join(render_block(b, i == 0) for i, b in enumerate(content["blocks"]))
    intro = "\n".join(para(t) for t in content["intro"])
    wrap = "font-family:'Inter',Arial,Helvetica,sans-serif;color:#1A1A2E;font-size:18px;line-height:1.6;"
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="{wrap}">\n'
        f'  <tr><td style="padding:8px 0;">\n{intro}\n  </td></tr>\n\n{blocks}\n</table>\n'
        '<p style="margin:16px 0 0;font-size:14px;color:#52606d;text-align:center;">*|LIST:ADDRESSLINE|*</p>\n'
    )


def api(method, path, key, body=None):
    server = key.rsplit("-", 1)[-1]
    req = urllib.request.Request(
        f"https://{server}.api.mailchimp.com/3.0{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={
            "Authorization": "Basic " + base64.b64encode(f"anystring:{key}".encode()).decode(),
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as err:
        sys.exit(f"Mailchimp {method} {path} failed: HTTP {err.code}: {err.read().decode()[:500]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("content", help="newsletter JSON, e.g. docs/newsletters/2026-10.json")
    ap.add_argument("--draft", action="store_true", help="create the draft campaign in Mailchimp")
    ap.add_argument("--test-to", metavar="EMAIL", help="also send a test copy of the draft to this address")
    args = ap.parse_args()

    content_path = Path(args.content)
    content = json.loads(content_path.read_text(encoding="utf-8"))
    rendered = render(content)  # logo from the live site: this is what Mailchimp receives and what you paste
    email_file = content_path.with_suffix(".email.html")
    email_file.write_text(rendered, encoding="utf-8")
    # Browser preview uses the local logo file so it shows before the logo is published.
    preview = content_path.with_suffix(".preview.html")
    preview.write_text(render(content, Path(os.path.relpath(ROOT / LOGO_PATH, preview.parent)).as_posix()), encoding="utf-8")
    print(f"Rendered preview: {preview}")
    print(f"HTML to paste into Mailchimp: {email_file}")
    fragment = content_path.with_suffix(".fragment.html")
    fragment.write_text(render_fragment(content), encoding="utf-8")
    print(f"Body only, for a text block's source view: {fragment}")

    if not args.draft:
        print("Preview only. Add --draft to create the campaign in Mailchimp (it will not be sent).")
        return

    key = os.environ.get("MAILCHIMP_API_KEY", "").strip()
    if "-" not in key:
        sys.exit("MAILCHIMP_API_KEY is not set (expected a key like abc123...-us2).")

    camp = api("POST", "/campaigns", key, {
        "type": "regular",
        "recipients": {"list_id": AUDIENCE_ID},
        "settings": {
            "subject_line": content["subject"],
            "preview_text": content["preview"],
            "title": content["title"],
            "from_name": FROM_NAME,
            "reply_to": FROM_EMAIL,
        },
    })
    cid = camp["id"]
    api("PUT", f"/campaigns/{cid}/content", key, {"html": rendered})
    print(f"Draft created: {content['title']} (id {cid}). Review and send it in Mailchimp: Campaigns > Drafts.")

    if args.test_to:
        api("POST", f"/campaigns/{cid}/actions/test", key, {"test_emails": [args.test_to], "send_type": "html"})
        print(f"Test email sent to {args.test_to}.")


if __name__ == "__main__":
    main()
