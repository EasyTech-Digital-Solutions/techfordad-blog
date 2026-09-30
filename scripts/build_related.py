#!/usr/bin/env python3
"""Generate the "Keep Reading" related-links block on every indexable article and guide.

    python3 scripts/build_related.py          # write / refresh the blocks
    python3 scripts/build_related.py --check  # verify only, exit 1 on problems

The link graph lives in RELATED below (topic clusters: safety, communication, health tech,
caregiver/how-to). Each topic has a US page, a Canada page, or a country-neutral page; a US page
only links to US or neutral pages, a Canada page only to Canada or neutral pages. Targets that are
noindex or missing are skipped. Blocks are wrapped in <!-- related --> markers, so the script is
idempotent. build_nav.py runs it. To add an article: add a TOPICS entry and list it in RELATED.
"""
import glob
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# key: (US path, Canada path, title US, title Canada, blurb). None = no page for that country;
# the same path in both slots = country-neutral page.
N = "neutral"
TOPICS = {
    "medical-alert": ("blog/best-medical-alert-systems.html", "blog/best-medical-alert-systems-canada.html", "Best Medical Alert Systems", "Best Medical Alert Systems in Canada", "Monitored help buttons, fall detection and what they cost"),
    "no-fee": ("blog/medical-alert-no-monthly-fee.html", None, "Medical Alert With No Monthly Fee", None, "Options that skip the monthly bill, and their trade-offs"),
    "life-alert-vs": ("blog/life-alert-vs-medical-guardian.html", None, "Life Alert vs Medical Guardian", None, "A head-to-head look at two well-known services"),
    "gps": ("blog/best-gps-trackers-for-seniors.html", "blog/best-gps-trackers-for-seniors-canada.html", "Best GPS Trackers for Seniors", "Best GPS Trackers for Seniors in Canada", "Location tracking for a parent who wanders or drives"),
    "gps-guide": ("guides/gps-trackers.html", "guides/gps-trackers.html", "GPS Tracker Guide for Seniors with Dementia", "GPS Tracker Guide for Seniors with Dementia", "How to choose and introduce a tracker"),
    "home-security": ("blog/best-home-security-for-seniors.html", "blog/best-home-security-for-seniors-canada.html", "Best Home Security for Seniors", "Best Home Security for Seniors in Canada", "Easy-to-use alarms and cameras for a parent living alone"),
    "doorbells": (None, "blog/best-video-doorbells-for-seniors-canada.html", None, "Best Video Doorbells for Seniors in Canada", "See who is at the door without getting up"),
    "smart-home": ("blog/best-smart-home-devices-for-seniors.html", None, "Best Smart Home Devices for Seniors", None, "Lights, plugs and sensors that make a home easier"),
    "alexa": ("blog/best-alexa-devices-for-seniors.html", None, "Best Alexa Devices for Seniors", None, "Voice control, reminders and easy video calls"),
    "fall": ("guides/fall-prevention-tech.html", "guides/fall-prevention-tech.html", "Fall Prevention Technology for Seniors", "Fall Prevention Technology for Seniors", "What technology can and cannot do about falls"),
    "safety-checklist": ("guides/home-safety-checklist.html", "guides/home-safety-checklist.html", "Home Safety Checklist for Seniors", "Home Safety Checklist for Seniors", "Room-by-room checks before you buy anything"),
    "cell-phones": ("blog/best-cell-phones-for-seniors.html", "blog/best-cell-phones-for-seniors-canada.html", "Best Cell Phones for Seniors", "Best Cell Phones for Seniors in Canada", "Simple phones and smartphones with big text and loud audio"),
    "plans": (None, "blog/best-cell-phone-plans-for-seniors-canada.html", None, "Best Senior Cell Phone Plans in Canada", "Low-cost plans and senior discounts from Canadian carriers"),
    "jitterbug": ("blog/jitterbug-vs-iphone-for-seniors.html", None, "Jitterbug vs iPhone for Seniors", None, "Which one suits a parent who is new to smartphones"),
    "cordless": ("blog/best-cordless-phones-for-seniors.html", "blog/best-cordless-phones-for-seniors-canada.html", "Best Cordless Phones for Seniors", "Best Cordless Phones for Seniors in Canada", "Home phones with loud, clear sound and big buttons"),
    "tablets": ("blog/best-tablets-for-seniors.html", "blog/best-tablets-for-seniors-canada.html", "Best Tablets for Seniors", "Best Tablets for Seniors in Canada", "The easiest screens for video calls, photos and reading"),
    "e-readers": ("blog/best-e-readers-for-seniors.html", "blog/best-e-readers-for-seniors-canada.html", "Best E-Readers for Seniors", "Best E-Readers for Seniors in Canada", "Large print and glare-free screens for reading"),
    "ipad-guide": ("blog/how-to-set-up-ipad-for-elderly-parent.html", "blog/how-to-set-up-ipad-for-elderly-parent.html", "How to Set Up an iPad for an Elderly Parent", "How to Set Up an iPad for an Elderly Parent", "Step-by-step settings that make an iPad easier to use"),
    "tv-remotes": ("blog/best-tv-remotes-for-seniors.html", None, "Best TV Remotes for Seniors", None, "Big-button remotes that make the TV simple again"),
    "bp": ("blog/best-blood-pressure-monitors-for-seniors.html", "blog/best-blood-pressure-monitors-canada.html", "Best Blood Pressure Monitors for Seniors", "Best Blood Pressure Monitors in Canada", "Home monitors that are easy to read and use"),
    "hearing": ("blog/best-hearing-aids-for-seniors.html", "blog/best-hearing-aids-canada.html", "Best Hearing Aids for Seniors", "Best Hearing Aids in Canada", "Over-the-counter and prescription options compared"),
    "hearing-guide": ("guides/hearing-aids.html", "guides/hearing-aids.html", "Hearing Aid Buying Guide for Seniors", "Hearing Aid Buying Guide for Seniors", "What to check before buying hearing aids"),
    "smartwatches": ("blog/best-smartwatches-for-seniors.html", "blog/best-smartwatches-for-seniors-canada.html", "Best Smartwatches for Seniors", "Best Smartwatches for Seniors in Canada", "Fall detection, heart rate and emergency calling on the wrist"),
    "sleep": ("blog/best-sleep-trackers-for-seniors.html", None, "Best Sleep Trackers for Seniors", None, "Simple ways to track sleep without a wearable"),
    "pills": ("blog/best-pill-organizers-for-seniors.html", None, "Best Pill Organizers for Seniors", None, "Organizers and reminders that help medication get taken"),
    "caregiver": ("guides/caregiver-resources.html", "guides/caregiver-resources.html", "Caregiver Resources & Support Tools", "Caregiver Resources & Support Tools", "Tools and support for the family doing the caring"),
    "checklist": ("guides/7-tech-essentials-checklist.html", "guides/7-tech-essentials-checklist.html", "7 Tech Essentials for a Senior Home", "7 Tech Essentials for a Senior Home", "A short list to start with"),
}

# topic -> related topics, most useful first. Missing targets for a country are skipped.
RELATED = {
    "medical-alert": ["no-fee", "life-alert-vs", "gps", "fall", "smartwatches"],
    "no-fee": ["medical-alert", "life-alert-vs", "smartwatches", "fall"],
    "life-alert-vs": ["medical-alert", "no-fee", "gps", "safety-checklist"],
    "gps": ["medical-alert", "gps-guide", "smartwatches", "fall", "caregiver"],
    "gps-guide": ["gps", "medical-alert", "caregiver", "fall"],
    "home-security": ["doorbells", "safety-checklist", "smart-home", "medical-alert", "fall"],
    "doorbells": ["home-security", "safety-checklist", "medical-alert", "alexa"],
    "smart-home": ["alexa", "home-security", "tablets", "medical-alert"],
    "alexa": ["smart-home", "tablets", "home-security", "ipad-guide"],
    "fall": ["medical-alert", "smartwatches", "safety-checklist", "no-fee", "home-security"],
    "safety-checklist": ["home-security", "fall", "medical-alert", "checklist", "pills"],
    "cell-phones": ["plans", "jitterbug", "cordless", "tablets", "ipad-guide", "hearing"],
    "plans": ["cell-phones", "tablets", "cordless", "smartwatches"],
    "jitterbug": ["cell-phones", "tablets", "ipad-guide", "medical-alert"],
    "cordless": ["cell-phones", "hearing", "medical-alert", "tv-remotes"],
    "tablets": ["ipad-guide", "e-readers", "cell-phones", "alexa", "plans", "jitterbug"],
    "e-readers": ["tablets", "ipad-guide", "cell-phones", "hearing"],
    "ipad-guide": ["tablets", "cell-phones", "e-readers", "caregiver", "checklist"],
    "tv-remotes": ["smart-home", "alexa", "hearing", "tablets"],
    "bp": ["smartwatches", "sleep", "pills", "medical-alert"],
    "hearing": ["hearing-guide", "cordless", "cell-phones", "tv-remotes"],
    "hearing-guide": ["hearing", "cordless", "tv-remotes", "caregiver"],
    "smartwatches": ["bp", "sleep", "medical-alert", "gps", "fall"],
    "sleep": ["smartwatches", "bp", "pills", "fall"],
    "pills": ["bp", "sleep", "smartwatches", "caregiver"],
    "caregiver": ["ipad-guide", "medical-alert", "gps-guide", "pills", "checklist"],
    "checklist": ["medical-alert", "cell-phones", "tablets", "home-security", "gps", "pills"],
}
MAX_LINKS = 5
BLOCK_RE = re.compile(r"[ \t]*<!-- related -->.*?<!-- /related -->[ \t]*\n?", re.S)
problems = []


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def write(p, text):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def noindex(path):
    return bool(re.search(r'<meta name="robots"[^>]*noindex', read(ROOT / path)))


def is_stub(path):
    return 'http-equiv="refresh"' in read(ROOT / path)


def country_of(path):
    return "ca" if path.endswith("-canada.html") or path == "blog/best-hearing-aids-canada.html" else "us"


def topic_of(path):
    """Topic key for a page, using whichever slot (US or Canada) holds it."""
    for key, (us, ca, *_rest) in TOPICS.items():
        if path in (us, ca):
            return key
    return None


def rel(from_path, to_path):
    a, b = from_path.split("/")[0], to_path.split("/")[0]
    return to_path.split("/")[-1] if a == b else f"../{to_path}"


def entries(path):
    topic = topic_of(path)
    if topic is None or topic not in RELATED:
        return []
    ca = country_of(path)  # neutral pages (guides, iPad setup) count as US and show the US set
    out = []
    for key in RELATED[topic]:
        us_p, ca_p, us_t, ca_t, blurb = TOPICS[key]
        target, title = (ca_p, ca_t) if ca == "ca" else (us_p, us_t)
        if not target or target == path or (ROOT / target).exists() is False:
            continue
        if noindex(target) or is_stub(target):
            continue
        out.append((target, title, blurb))
    return out[:MAX_LINKS]


def render(path, items):
    lines = ["<!-- related -->", '<section class="related-guides">', "  <h2>Keep Reading</h2>", "  <ul>"]
    for target, title, blurb in items:
        lines.append(f'    <li><a href="{rel(path, target)}"><strong>{title}</strong></a> <span>{blurb}</span></li>')
    lines += ["  </ul>", "</section>", "<!-- /related -->"]
    return "\n".join(lines) + "\n"


def insert(path, text, block):
    text = BLOCK_RE.sub("", text)
    if "</article>" in text:  # US articles: inside the article column, after the FAQ
        i = text.rindex("</article>")
        i = text.rfind("\n", 0, i) + 1
        return text[:i] + block + text[i:]
    m = re.search(r'\n(</div>\n)\n<div class="author-box', text)  # guides: end of .about-body
    if m:
        i = m.start(1)
        return text[:i] + block + text[i:]
    m = re.search(r"\n(  </div>\n</div>\n)\n<footer>", text)  # Canada pages: end of .article-body
    if m:
        i = m.start(1)
        return text[:i] + block + text[i:]
    problems.append(f"{path}: no insertion point found")
    return text


def main():
    check = "--check" in sys.argv
    paths = sorted(p.relative_to(ROOT).as_posix() for p in [*ROOT.glob("blog/*.html"), *ROOT.glob("guides/*.html")] if p.name != "index.html")
    inbound = {}
    done = 0
    for path in paths:
        if noindex(path) or is_stub(path) or topic_of(path) is None:
            continue
        items = entries(path)
        if not items:
            problems.append(f"{path}: no related links resolved")
            continue
        for target, _t, _b in items:
            inbound[target] = inbound.get(target, 0) + 1
        text = read(ROOT / path)
        new = insert(path, text, render(path, items))
        if check:
            if new != text:
                problems.append(f"{path}: related block missing or out of date (run build_related.py)")
        elif new != text:
            write(ROOT / path, new)
        done += 1
    for path in paths:
        if noindex(path) or is_stub(path) or topic_of(path) is None:
            continue
        need = 1 if country_of(path) == "ca" else 2  # Canada has fewer pages to link from
        if inbound.get(path, 0) < need:
            problems.append(f"{path}: only {inbound.get(path, 0)} related-block link(s) point here")
    if problems:
        print("\n".join(f"x {p}" for p in problems))
        sys.exit(1)
    print(f"related: {done} pages {'OK' if check else 'written'}")


if __name__ == "__main__":
    main()
