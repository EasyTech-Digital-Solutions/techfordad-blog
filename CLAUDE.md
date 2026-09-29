# TechForDad

Static HTML affiliate blog reviewing tech products for seniors and their caregivers (US + Canada variants). No build step — pages are hand-authored HTML, deployed as static files via GitHub Pages (see `CNAME`).

## New article checklist

Every new `blog/*.html` article (weekly automated posts included) must ship with all of the following — not just the article body:

1. **The article HTML** in `blog/`, following the structure of a recent comparable article (head block with title/meta/canonical/og/twitter tags + `Article` JSON-LD, `.article-hero` section, comparison content, FAQ).
2. **Title ≤ 60 chars, meta description ≤ 160 chars.** Google truncates past this in search results — check actual character count, not a guess.
3. **A hero image.** See "Hero images" below — this step has been skipped on past articles and left them with a text-only hero and a broken/fallback `og:image`. Don't skip it.
4. **A card in `blog/index.html`** linking to the new article (match the existing `.card` markup; add `data-country="ca"` for Canada variants).
5. **A `sitemap.xml` entry** for the new URL.
6. **Run `python3 scripts/build_nav.py`.** The header's "All Reviews" dropdown is generated from `blog/*.html` (files ending `-canada.html` go under Canada, `noindex` pages are left out) and copied into every page. Re-run it after adding or removing an article so the menu and the cache-busting `?v=` on `style.css`/`main.js` stay in sync.

## Hero images

Every article hero should have a real photo, not just text on the navy background. Process (established in commits `c49f0f6`, `95d5905`):

1. Source a **copyright-free photo from Unsplash** (Unsplash License — free for commercial use, no attribution required) that matches the article's specific topic — not a generic tech stock photo.
2. Save it to `images/heroes/hero-<topic>.jpg`. Target ~900px wide, re-encoded as a progressive JPEG at quality ~82 (see commit `8326325`) — keep file sizes small, this is a full-bleed background image, not a print asset.
3. Wire it into the page in two places:
   - `<meta property="og:image" content="https://www.techfordad.com/images/heroes/hero-<topic>.jpg"/>` in the `<head>`.
   - `<img src="../images/heroes/hero-<topic>.jpg" alt="..." width="860" height="480" fetchpriority="high">` as the **first child** of `<div class="article-hero">`, before `.article-hero-inner`. (The CSS absolutely-positions it as a `background: cover`, so exact source dimensions don't matter — the `width`/`height` attributes are just layout-reservation hints and don't need to match the file's real pixel size. Use `fetchpriority="high"`, not `loading="lazy"`: the hero is the first thing visitors see, and lazy-loading it delays the page.)
4. If no suitable photo exists yet, it's fine to ship the article with a text-only hero (many pages already work this way), but **come back and add one** — don't leave `og:image` pointing at a file that was never actually saved. If in doubt, point `og:image` at `images/og-default.svg` (the site's real fallback) rather than a hero filename that doesn't exist yet.

## Content conventions

- US and Canada variants are separate files (`best-x-for-seniors.html` / `best-x-for-seniors-canada.html`), Canada pages use `lang="en-CA"` and CAD pricing.
- **Amazon affiliate tags:** US pages (amazon.com) use `tag=techfordad0b-20`; Canada pages (amazon.ca) use `tag=abhikar91-20`. Links inside the Gift Guides section (`gift-guides/`) use `tag=techfordad-gifts-20` instead of `techfordad0b-20`, so that section reports separately in Associates; never mix the two on one page. These are the only three registered tags. Never invent another (`techfordad-ca-20` was made up by past weekly runs and earns nothing). Before finishing, grep the new article for `tag=` and confirm every link uses the right one.
- **Amazon disclosure:** Amazon requires the exact sentence "As an Amazon Associate I earn from qualifying purchases." It lives in the `footer-affiliate` paragraph in the site footer. Copy the footer unchanged from an existing page and confirm the sentence is present on every new article.
- Product prices are tracked in `scripts/products.json` and auto-updated weekly by `scripts/auto_price_update.py` (GitHub Action `auto-price-update.yml`) — if an article's price claims should stay current, add its products to that file.

## Gift Guides, seasonal themes and site chrome

- **Gift Guides** live in `gift-guides/`. Their content is defined in `scripts/build_gift_guides.py` (products, ASINs, prices, FAQs). Edit that file and run `python3 scripts/build_gift_guides.py`; it rewrites the six pages, the "See more gift ideas" boxes on the review pages, and the sitemap entries, then runs `build_nav.py`. Do not hand-edit `gift-guides/*.html`.
- Gift Guides links use `tag=techfordad-gifts-20` only (see the affiliate tags rule above). Write prices as "about $X (source, checked date)" and never as a live price.
- Before publishing or refreshing a guide, run `python3 scripts/check_amazon_listings.py out.json ASIN ...` to confirm each listing is live, buyable and well rated. Amazon rate-limits after roughly 100 rapid requests; wait a while if it reports `blocked`.
- **Seasonal themes:** `js/season.js` sets `data-season` (Halloween Sep 29 - Oct 31, Christmas Nov 1 - Dec 31) and `data-gifts` (big gift banner Sep 1 - Dec 31, May 1-14, Jun 1-21). Colours are variables in `css/style.css`; outside the windows the default look is used. Preview with `?season=halloween|christmas|none` and `?gifts=peak|off`.
- **Header menus** (All Reviews, Gift Guides, Guides, About) are generated into every page by `scripts/build_nav.py`. Re-run it after adding or removing any article, guide or gift guide. Redirect stubs (pages with `http-equiv="refresh"`) and `noindex` pages are left out of the menus.
- `guides/best-senior-gifts.html` is a redirect stub to the Gift Guides hub. Do not recreate a competing gifts page.
- Hero images use `fetchpriority="high"`, never `loading="lazy"`.
- The monthly price audit (`scripts/audit_inventory.py`) covers `blog/`, `guides/` and `gift-guides/`.
- **Dates and counts that must not go stale:** the gift guides take every date from one setting in `scripts/build_gift_guides.py`; after re-checking prices, run `python3 scripts/build_gift_guides.py --checked YYYY-MM-DD` (this updates "Updated ...", the price notes and the structured-data date together). Do not run it unless prices were actually re-checked. Run `python3 scripts/update_site_stats.py` to refresh the homepage "N+ Products Compared" claim. Never change an "Updated" date without changing the content.
- **Gift announcement bar** (`<!-- gift-bar -->`, injected on every page except `gift-guides/` by `build_nav.py`) shows only while `data-gifts="peak"`. Visitors can dismiss it (remembered 14 days in `localStorage`); preview with `?giftbar=show`. The homepage picture tiles are generated by `build_gift_guides.py` from the same guide data, with price chips in its `CHIPS` table; update those chips when the lowest verified price in a guide changes.
