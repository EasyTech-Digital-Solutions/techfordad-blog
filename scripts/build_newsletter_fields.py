"""Write three hidden fields into the newsletter signup form on every page, so Mailchimp knows where each subscriber signed up.

Mailchimp audience fields (Audience > Settings > Audience fields and merge tags), all type Text, created by the owner on 2026-10-07:
    SOURCE   the page the form was on, e.g. "blog/best-tablets-for-seniors" ("home" for the home page)
    TOPIC    a short topic family for that page, e.g. "tablets", "medical-alert", "hearing" (families below)
    COUNTRY  "US" or "CA" for a country-specific review; left out on pages that are not tied to one country
The values are fixed per page at build time, so nothing depends on JavaScript. They sit between <!-- nl-fields --> markers, written by
build_nav.py; never hand-edit them. With them the owner can segment the monthly newsletter ("signed up from a medical alert page", "Canada readers").
If a Mailchimp field named SOURCE, TOPIC or COUNTRY does not exist, Mailchimp ignores the extra input: nothing breaks.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_related as R  # noqa: E402

FORM_RE = re.compile(r'(<form class="email-form"[^>]*list-manage[^>]*>)')
BLOCK_RE = re.compile(r"\s*<!-- nl-fields -->.*?<!-- /nl-fields -->", re.S)

# build_related.TOPICS key -> the broader topic the owner segments by
FAMILY = {
    "medical-alert": "medical-alert", "no-fee": "medical-alert", "life-alert-vs": "medical-alert",
    "hearing": "hearing", "hearing-guide": "hearing",
    "gps": "gps", "gps-guide": "gps",
    "cell-phones": "phones", "jitterbug": "phones", "cordless": "phones", "plans": "phones",
    "tablets": "tablets", "ipad-guide": "tablets", "e-readers": "tablets",
    "alexa": "smart-home", "smart-home": "smart-home", "doorbells": "smart-home", "home-security": "smart-home", "tv-remotes": "smart-home",
    "bp": "health", "pills": "health", "sleep": "health", "smartwatches": "health",
    "fall": "safety", "safety-checklist": "safety", "checklist": "safety",
    "caregiver": "caregiving",
}

# pages that build_related.TOPICS does not list (parked, noindex): their topic family
EXTRA = {
    "blog/best-laptops-for-seniors.html": "tablets",
    "blog/best-large-button-keyboards-for-seniors.html": "tablets",
    "blog/best-video-doorbells-for-seniors.html": "smart-home",
}


def fields_for(rel, html):
    """The (name, value) pairs for a page, in order."""
    source = "home" if rel == "index.html" else re.sub(r"\.html$", "", rel)
    if rel.startswith("gift-guides/"):
        topic = "gifts"
    elif rel == "index.html":
        topic = "home"
    else:
        key = R.topic_of(rel)
        topic = FAMILY.get(key, "other") if key else EXTRA.get(rel, "other")
    out = [("SOURCE", source), ("TOPIC", topic)]
    country = None
    if rel.startswith("blog/"):
        key = R.topic_of(rel)
        shared = key and R.TOPICS[key][0] == R.TOPICS[key][1]  # one page serves both countries
        if not shared:
            country = "CA" if 'lang="en-CA"' in html[:400] else "US"
    elif rel.startswith("gift-guides/"):
        country = "US"  # the gift guides carry US (amazon.com) links only
    if country:
        out.append(("COUNTRY", country))
    return out


def block(rel, html):
    inputs = "\n".join(f'      <input type="hidden" name="{n}" value="{v}"/>' for n, v in fields_for(rel, html))
    return f"\n      <!-- nl-fields -->\n{inputs}\n      <!-- /nl-fields -->"


def pages():
    for pattern in ("*.html", "blog/*.html", "guides/*.html", "gift-guides/*.html"):
        for path in sorted(ROOT.glob(pattern)):
            yield path.relative_to(ROOT).as_posix(), path


def main():
    written = 0
    for rel, path in pages():
        text = path.read_text(encoding="utf-8")
        if not FORM_RE.search(text):
            continue
        clean = BLOCK_RE.sub("", text)
        new = FORM_RE.sub(lambda m: m.group(1) + block(rel, clean), clean, count=1)
        if new != text:
            path.write_text(new, encoding="utf-8")
            written += 1
    print(f"newsletter fields: {written} pages written")


if __name__ == "__main__":
    main()
