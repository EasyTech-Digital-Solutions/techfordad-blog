# TechForDad

Static HTML affiliate blog reviewing tech products for seniors and their caregivers (US + Canada variants). No build step — pages are hand-authored HTML, deployed as static files via GitHub Pages (see `CNAME`).

## New article checklist

Every new `blog/*.html` article (weekly automated posts included) must ship with all of the following — not just the article body:

1. **The article HTML** in `blog/`, following the structure of a recent comparable article (head block with title/meta/canonical/og/twitter tags + `Article` JSON-LD, `.article-hero` section, comparison content, FAQ).
2. **Title ≤ 60 chars, meta description ≤ 160 chars.** Google truncates past this in search results — check actual character count, not a guess.
3. **A hero image.** See "Hero images" below — this step has been skipped on past articles and left them with a text-only hero and a broken/fallback `og:image`. Don't skip it.
4. **A card in `blog/index.html`** linking to the new article (match the existing `.card` markup; add `data-country="ca"` for Canada variants).
5. **A `sitemap.xml` entry** for the new URL.

## Hero images

Every article hero should have a real photo, not just text on the navy background. Process (established in commits `c49f0f6`, `95d5905`):

1. Source a **copyright-free photo from Unsplash** (Unsplash License — free for commercial use, no attribution required) that matches the article's specific topic — not a generic tech stock photo.
2. Save it to `images/heroes/hero-<topic>.jpg`. Target ~900px wide, re-encoded as a progressive JPEG at quality ~82 (see commit `8326325`) — keep file sizes small, this is a full-bleed background image, not a print asset.
3. Wire it into the page in two places:
   - `<meta property="og:image" content="https://www.techfordad.com/images/heroes/hero-<topic>.jpg"/>` in the `<head>`.
   - `<img src="../images/heroes/hero-<topic>.jpg" alt="..." width="860" height="480" loading="lazy">` as the **first child** of `<div class="article-hero">`, before `.article-hero-inner`. (The CSS absolutely-positions it as a `background: cover`, so exact source dimensions don't matter — the `width`/`height` attributes are just layout-reservation hints and don't need to match the file's real pixel size.)
4. If no suitable photo exists yet, it's fine to ship the article with a text-only hero (many pages already work this way), but **come back and add one** — don't leave `og:image` pointing at a file that was never actually saved. If in doubt, point `og:image` at `images/og-default.svg` (the site's real fallback) rather than a hero filename that doesn't exist yet.

## Content conventions

- US and Canada variants are separate files (`best-x-for-seniors.html` / `best-x-for-seniors-canada.html`), Canada pages use `lang="en-CA"` and CAD pricing.
- **Amazon affiliate tags:** US pages (amazon.com) use `tag=techfordad0b-20`; Canada pages (amazon.ca) use `tag=abhikar91-20`. These are the only two registered Associates tags. Never invent another (`techfordad-ca-20` was made up by past weekly runs and earns nothing). Before finishing, grep the new article for `tag=` and confirm every link uses the right one.
- **Amazon disclosure:** Amazon requires the exact sentence "As an Amazon Associate I earn from qualifying purchases." It lives in the `footer-affiliate` paragraph in the site footer. Copy the footer unchanged from an existing page and confirm the sentence is present on every new article.
- Product prices are tracked in `scripts/products.json` and auto-updated weekly by `scripts/auto_price_update.py` (GitHub Action `auto-price-update.yml`) — if an article's price claims should stay current, add its products to that file.
