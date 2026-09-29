# Production audit (2026-09-29)

Scope: all 56 current pages plus the new Gift Guides, seasonal themes, header menus and the scripts behind them. Checks were run against a local copy in a real Edge browser (mouse, keyboard, five screen widths) and with static scans of the HTML. Nothing was run against the live site.

## Result

Nothing blocks publishing. Everything found during the audit was fixed or is listed under "Open items" below.

## What was checked, and the result

| Area | Check | Result |
|---|---|---|
| Structure | Balanced tags, duplicate ids, missing assets, broken internal links (about 2,900 menu links plus page links) | Clean |
| SEO | Title 60 or fewer, description 160 or fewer, canonical, Open Graph, `og:image` files exist, JSON-LD parses, FAQ schema matches visible questions, sitemap vs. real pages | Clean (see note on the home-security description) |
| Sitemap | Every indexable page listed; no `noindex` page or redirect stub listed | 51 entries, correct |
| Affiliate compliance | Every Amazon link has `rel="sponsored"`, correct tag per area (US `techfordad0b-20`, Canada `abhikar91-20`, gifts `techfordad-gifts-20`), Associates disclosure sentence on every page with Amazon links | Fixed 33 links missing `sponsored`; now clean |
| Security | Secrets scan, `target="_blank"` without `noopener`, http links, form endpoints, workflow permissions | Clean |
| Console and network | Console errors, uncaught exceptions, failed requests, broken images on all 56 pages | Zero |
| Layout | Horizontal overflow at 1873, 1280, 1024, 768 and 390 px | One 3px overflow (see open items) |
| Menus | Real mouse: click one, hover another, click away, Escape | Only one menu open at a time |
| Keyboard | Enter opens, Tab enters menu, Escape closes and returns focus, `aria-expanded` updates, focus outline | Pass |
| Contrast | 69 text and button checks across default, Halloween and Christmas themes | "Free Guide" button was 2.2:1 (white on amber); fixed to 5.3:1 |
| Theme dates | 26 date and URL-override cases at every boundary (Sep 28-30, Oct 31 / Nov 1, Dec 31 / Jan 1, gift windows) | Pass |
| Performance | Hero images were lazy-loaded on 46 pages | Switched to `fetchpriority="high"` |
| Scripts | `check_site.py`, `build_nav.py` (idempotent), `build_gift_guides.py`, `audit_inventory.py` | Work; inventory now covers gift guides |

## Fixed during the audit

1. 33 Amazon buttons on 7 review pages lacked `rel="sponsored"`.
2. Gift pages were regenerated with a plain header after the menu script had run. The generator now runs the menu script itself.
3. My first attempt at removing the old gifts page from the sitemap deleted 22 other entries. Restored from git and redone one entry at a time; the sitemap now has exactly the intended changes.
4. Guide pages: author box had no vertical padding (inline style override); checklist showed a bullet and a box on every item; no spacing after lists; 12 places where text ran into a bold word; outdated product names (Galaxy Watch 6, Apple Watch Series 9, Lively Mobile Plus).
5. Old `guides/best-senior-gifts.html` overlapped the new Gift Guides. It is now a redirect stub; about 90 links, the legacy Father's Day redirect, the sitemap and the Guides menu were updated.
6. "Free Guide" button contrast (2.2:1 to 5.3:1).
7. Hero images no longer lazy-load.
8. Gift banner now starts Sep 1 (was Oct 1), since it is already gift season.
9. The blue "prices change" bar now follows the seasonal theme.
10. `.gitignore` now ignores Python cache files.
11. The monthly price audit now includes `gift-guides/`.

## Open items (none blocks publishing)

**Before the Gift Guides go live**
- ~~Verify the LifeStation Mobile listing~~ Done 2026-09-29: live and buyable, 4.0 stars from 270 ratings. (Its fall-detection add-on and the model AARP tested still need the reader to confirm, and the guide says so.)
- Aura and Birdbuddy Pro listings are live and buyable (Aura 4.7 stars from 13,894 ratings; Birdbuddy 4.3 from 212). Amazon does not show their prices to my checker, so the guide shows no price and says "check the current price on Amazon". That is acceptable to publish; add a price only after reading it from the listing.
- Omron and the Ravensburger puzzle are not in any built guide (they were dropped when the five tech-led guides were built), so there is nothing to verify for them.
- After publishing, click one gift link and confirm the click appears in the `techfordad-gifts-20` tracking ID report the next day.
- Re-run `check_amazon_listings.py` the week you publish; Amazon raised device prices in August.

**Worth doing soon**
- Home page and reviews index load heavy card images (the reviews index transfers about 1.3 MB). Making 400px thumbnails for cards would cut that by roughly two thirds.
- Heading order: 24 older review pages jump from `h1` to `h4` because "Table of Contents" is an `h4`. Low severity for readers; screen-reader outline is slightly off.
- `blog/best-cordless-phones-for-seniors.html` overflows by 3px at a 1024px window (sidebar).
- Mobile menu tap targets are 41px tall; 44px is the usual target.
- Hero and guide pages carry "Updated June/July 2026" badges from earlier; refresh them when their prices are next verified.
- The Weekly Articles routine on claude.ai is still paused. When you turn it back on, its first Canada article should be checked for the `abhikar91-20` tag, and both articles for the new footer disclosure line and `fetchpriority="high"` hero.

**Notes**
- The home-security meta description counts as 162 characters in the raw HTML because of the `&amp;` entity; rendered it is 158, so it is within the 160 limit.
- The three `noindex` pages (laptops, large-button keyboards, US video doorbells) stay out of the sitemap and out of all menus.

## Added after the audit

- **Gift-season announcement bar** on every page except the gift guides, dismissible for 14 days, only shown in gift season.
- **Picture tiles with price chips** in the homepage gift banner (five tiles; two columns on phones), and a red dot on the "Gift Guides" menu item during the season.
- Re-ran the whole suite after these changes: static scan, 26 date cases, real-mouse menu test, runtime (zero console errors, zero failed requests), layout at five widths. Same result as before; the only overflow remains the 3px on the cordless-phones page at 1024px.
- Mobile menu: the "Gift Guides" label was centred once the red dot was added; fixed so it lines up with the other items.
- **Left-edge strip reported in screenshots:** measured with a real browser at 757px and 1873px; page content starts at x=0 and no element paints in that strip, so it is not produced by the site. Most likely browser zoom, a browser side panel or an extension. Not reproduced.
