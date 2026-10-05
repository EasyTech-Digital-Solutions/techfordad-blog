"""Put a short "health information" notice on every page that gives health-related advice.

These topics are "your money or your life" for Google and matter to readers: the notice says the page is general
information (not medical advice), that health facts are linked to their sources, and that AI helps draft the guides.
It is written into a `<!-- health-note -->` block right under the affiliate disclosure, so never hand-edit the block.
To add a page, put it in MEDICAL_PAGES and run `python3 scripts/build_nav.py`.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MEDICAL_PAGES = [
    "blog/best-hearing-aids-for-seniors.html", "blog/best-hearing-aids-canada.html",
    "blog/best-medical-alert-systems.html", "blog/best-medical-alert-systems-canada.html",
    "blog/best-blood-pressure-monitors-for-seniors.html", "blog/best-blood-pressure-monitors-canada.html",
    "blog/best-gps-trackers-for-seniors.html", "blog/best-gps-trackers-for-seniors-canada.html",
    "blog/best-pill-organizers-for-seniors.html", "blog/best-sleep-trackers-for-seniors.html",
    "blog/best-smartwatches-for-seniors.html", "blog/best-smartwatches-for-seniors-canada.html",
    "blog/medical-alert-no-monthly-fee.html", "blog/life-alert-vs-medical-guardian.html",
    "guides/hearing-aids.html", "guides/fall-prevention-tech.html", "guides/gps-trackers.html",
    "guides/home-safety-checklist.html",
]

TEXT = ('<strong>Health information:</strong> general information, not medical advice; it does not replace your parent\'s doctor, '
        'audiologist or pharmacist. Health facts link to their sources, and AI helps draft our guides '
        '(<a href="../how-we-review.html" style="text-decoration:underline">how we review products</a>).')

# The note lives INSIDE the affiliate disclosure box (one box, not two): a second line before the box's closing </div>.
OLD_BLOCK_RE = re.compile(r'[ \t]*<!-- health-note -->.*?<!-- /health-note -->[ \t]*\r?\n\r?\n?', re.S)
INLINE_RE = re.compile(r'<br>\s*<!-- health-note -->.*?<!-- /health-note -->', re.S)
ARTICLE_ANCHOR = re.compile(r'(<div class="article-disclaimer">\s*<strong>Affiliate Disclosure:</strong>.*?)(\s*</div>)', re.S)
GUIDE_ANCHOR = re.compile(r'(<div class="article-disclaimer">.*?)(\s*</div>)', re.S)


def main():
    written, problems = 0, []
    for rel in MEDICAL_PAGES:
        path = ROOT / rel
        original = path.read_text(encoding="utf-8")
        text = OLD_BLOCK_RE.sub("", INLINE_RE.sub("", original))
        anchor = (GUIDE_ANCHOR if rel.startswith("guides/") else ARTICLE_ANCHOR).search(text)
        if not anchor:
            problems.append(rel)
            continue
        inner = anchor.group(1).rstrip()
        new = text[:anchor.start()] + inner + "<br>\n      <!-- health-note -->" + TEXT + "<!-- /health-note -->" + anchor.group(2) + text[anchor.end():]
        if new != original:
            path.write_text(new, encoding="utf-8")
            written += 1
    print(f"health note: {written} pages written" + (f" (no anchor found: {problems})" if problems else ""))


if __name__ == "__main__":
    main()
