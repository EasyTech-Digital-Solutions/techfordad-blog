# TechForDad admin panel (run locally)

The admin panel is **not published** on techfordad.com any more (see `_config.yml`). Run it on your
own computer instead:

1. Open a terminal in this `admin/` folder.
2. Start a local server: `python3 -m http.server 8765`
3. Open http://localhost:8765 in your browser.

It talks to the GitHub API and reads the live site from your browser, and the live site allows that,
so everything works the same as before. Because it now runs on `localhost`, the GitHub token and the
Anthropic key you enter are stored in the browser for `localhost` only, not on the website's own
origin where the ad and analytics scripts run.

**Product Tracker** (`product-tracker.html`, linked from the top bar) is a searchable, sortable table
of every product the site prices or links to, with status (Current / Unverifiable / Needs 2nd source /
Check model), last-verified date, and a source link per item. It reads `product-tracker-data.json`,
a flat export of the `products` collection from the "Product Tracker" artifact on claude.ai — ask
Claude to re-export that data into this file after a price-verification pass to refresh it.

Good practice:
- Use a **fine-grained GitHub token limited to this one repository** (Contents: read/write).
- Give the Anthropic key used here a **monthly spend limit** in the Anthropic console.
- Use "Logout" when you are done on a shared computer.
- If you used the old online panel at techfordad.com/admin, delete the saved session once:
  open techfordad.com, press F12, Application, Local storage, delete `tfd_v2_session`.
