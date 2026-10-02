# TechForDad test suite

Automated checks for every page of the site: that it is correct, safe, readable on a phone, prints well, earns
commission, and has not broken since the last change. Written for a static HTML site with no build step.

```
tests/run.sh                 everything that works offline (loads every page in Chrome; about 17 minutes)
tests/run.sh --quick         one page of each kind (about 2 minutes): the fast check while you work
tests/run.sh tests/test_security.py tests/test_links.py     just some files (instant: no browser)
tests/run.sh --live          also check the PUBLISHED site (run after merging to main)
```

The first run creates `.venv/` and installs the dependencies (`tests/requirements.txt`). The browser tests drive the
Chrome that is already on your computer; CI installs its own. Nothing here is published on the website (`tests/` is in
the `exclude:` list in `_config.yml`, and a test checks that).

## What is checked

| File | Needs a browser? | What it protects |
|---|---|---|
| `test_inventory.py` | no | Every HTML file has a **kind** (`pages.py`); `sitemap.xml` matches the pages; old-URL redirects work |
| `test_template_parity.py` | no | USA and Canada articles do not differ: two columns, sidebar boxes (Our Top Picks matches the pick list, Related Guides, affiliate note), author box, newsletter, click-to-open FAQ, section order (summary, products, comparison table), and the inside of each part: product cards, comparison table, disclosure box, hero line, breadcrumb |
| `test_seo.py` | no | Well-formed HTML, no duplicate ids, one `h1`, title ≤ 60 and description ≤ 160, canonical URL, social tags, `lang` (`en-CA` for Canada), alt text, no missing local files |
| `test_links.py` | no | **Affiliate rules (the part that gets paid):** right tracking ID per page type, right Amazon store, `rel="sponsored"`, no shortened links, disclosure present, bounty links match the verified list exactly, discontinued offers gone, `#anchors` exist |
| `test_security.py` | no | Internal files are not published, no insecure `http://` resources, third-party scripts and forms are allowlisted, no inline handlers beyond the known two, no `eval`/`innerHTML`, no secrets in the repo, workflows pinned and least-privilege, `security.txt` not expired |
| `test_generated.py` | no | The repo's own scripts: `check_site.py --all`, `check_internal_links.py`, `build_nav.py --check` (nav, related, sources, buying summary, asset versions) |
| `test_ui_pages.py` | yes | Every page, desktop and phone: no JS or console errors, no failed requests, no sideways scrolling, no broken images, header/footer, mobile menu, 44px touch targets, readable text, toolbar position, table button, offers |
| `test_ui_interactions.py` | yes | FAQ, menus, **Copy link**, **Share**, every **print button**, and the scroll-position-after-printing regression |
| `test_ui_print.py` | yes | What prints: page chrome removed, FAQ answers open, page address and date added |
| `test_ui_a11y.py` | yes | Accessibility scan (axe-core) on every page against a **baseline** of known issues |
| `test_ui_registry.py` | no | Every CSS section is mapped to the tests that cover it (the "keep the tests current" guard) |
| `test_live_site.py` | `--live` | Every sitemap URL is up, redirects, real 404s, certificate expiry, security headers, internal files not public, deploy matches the repo |
| `check_the_tests.py` | (script) | Breaks a copy of the site in 43 ways and confirms the right test notices each one |

`.github/workflows/tests.yml` runs the whole suite on every pull request and every push to `main`.
`.github/workflows/live-site-check.yml` runs the live checks every Monday.

## When you change the UI (do this in the same pull request)

Adding or changing something visitors see means the tests must change too. The suite is built so that forgetting fails:

| You did this | The suite fails until you... |
|---|---|
| Added a **new kind of page** (a new folder, a new template) | add a rule in `tests/pages.py` (`test_every_html_file_has_a_kind`) and decide which checks apply |
| Added a **section to `css/style.css`** (a `/* ===== NAME ===== */` banner) | add it to `tests/data/ui_components.json` with the test(s) that cover it, **and write a test if none do** (`test_ui_registry.py`) |
| Added a **button, menu, form or behavior** | add a test in `test_ui_interactions.py` (click it, check the result). Copy a neighbouring test. |
| Changed **print styles** | extend `test_ui_print.py` |
| Added or changed an **Amazon link or offer** | generate it with SiteStripe, check the tag survives the redirect, add it to `tests/data/approved_amazon_links.json`, run `python3 scripts/amazon_registry.py --update` |
| Added a **third-party script, form or embed** | add its host to `tests/data/third_party_hosts.json`. That is a privacy and security decision: make it on purpose. |
| Added a **new top-level file or folder** | either list it in `exclude:` in `_config.yml` (internal) or in `tests/data/public_top_level.json` (public) |
| Changed `css/style.css` or `js/main.js` | bump `ASSET_VERSION` in `scripts/build_nav.py` and run it (`build_nav.py --check` fails otherwise) |

A good test for a UI change answers three questions: does it appear where it should (and *only* there), does it work when
clicked or tapped, and does it still fit on a phone? Copy the closest existing test and change the selector.

## Known-issue baselines (they only shrink)

Two files record problems that exist today, so they do not block work but can never get worse:

* `tests/data/known_issues.json`: inline `onclick`/`onmouseover` handlers on two pages.
* `tests/data/a11y_known_issues.json`: accessibility findings per page (rule → number of elements).

A **new** problem fails the suite. **Fixing** one also fails it, with a message telling you to remove the line (so the
file stays honest). To re-record the accessibility baseline after fixing things:
`tests/run.sh --update-baseline tests/test_ui_a11y.py`, then **read the git diff**: it should only have lines removed.
Never grow a baseline to make a failing test pass; fix the page, or ask first.

## Checking the tests themselves

```
./.venv/bin/python tests/check_the_tests.py            # all 43 deliberate breakages (about 6 minutes)
./.venv/bin/python tests/check_the_tests.py affiliate  # only those with "affiliate" in the name
```

It breaks a temporary copy of the site (a wrong affiliate tag, a leaked secret, a JavaScript error, the print scroll bug...)
and reports any breakage the suite fails to notice. Run it after changing the tests. Add a line to `MUTATIONS` for every
new kind of check you write.

## How the browser tests work

* The repo is served on a local port, as GitHub Pages would serve it. Requests to other sites (Google, Amazon) get empty
  answers, so tests run offline and never send analytics hits.
* Each page is loaded once per screen size (desktop 1280px, phone 390px) and measured by `tests/measure.js`; many tests
  read that one report, which keeps a full run to about 17 minutes.
* Print is tested by emulating print media, and by replacing `window.print` with a stand-in that behaves like Chrome after
  a cancelled print (fires `beforeprint`, jumps to the top, fires `afterprint`).
* The checks use fixtures in `conftest.py`; `pages.py` is the page inventory; `htmlutil.py` reads HTML for the static tests.

## Not covered (be honest about the edges)

* Real phones, Safari and Firefox: the browser tests use Chrome (a phone-sized window and phone user agent, not a device).
* The actual print dialog and the native share sheet: they are stood in for, not opened.
* Whether Amazon credits a bounty: only the links are verified; check Associates Central's Bounty Events report.
* Content quality (is a recommendation right, is a price current): the monthly audit and `check_site.py` cover prices.
* Accessibility checks catch about a third of real problems; they do not replace trying the site with a screen reader.
