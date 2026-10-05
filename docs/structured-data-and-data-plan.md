# What data can be added without risking indexing or the Amazon account (research, 2026-10-05)

Sources opened: Google Search Central (structured data policies, review snippet, product snippet, Article), schema.org (citation, publishingPrinciples,
correctionsPolicy, ownershipFundingInfo, mentions), Amazon Associates program policies.

## Rules that decide what is safe

**Google**
- Markup must match visible content, represent the page honestly, and never misrepresent "your ownership, affiliation, or primary purpose".
- Review and rating markup must reflect genuine reviews or ratings. Fake or undisclosed-incentive reviews risk a manual action (loses rich results).
- Product snippets are for review/aggregator pages and need `review`, `aggregateRating` or `offers`. Merchant listings are for pages where shoppers can buy.
  TechForDad is neither a seller nor a tester, so Product markup has no honest version today (see docs/seo-sweep-2026-10-05.md).
- Article: `author` (Person or Organization) should carry a `url` that identifies the author.

**Amazon Associates (policies page, read 2026-10-05)**
- "your Site may only show prices and availability if: (a) we serve the link in which that price and availability data are displayed, or (b) you obtain Product pricing and availability data via Creators API or PA API."
- Cached prices must be refreshed within 24 hours; a date/time stamp and the "prices ... are accurate as of the date/time indicated and are subject to change" notice are required.
- Star ratings and customer reviews may only be shown if obtained through the API. Product images may not be stored or cached (links only).
- PA API / Creators API access requires recent qualifying sales (reported: 3 within 180 days to start; 10 in the trailing 30 days to keep access). Check Associates Central for the current rule.

## Finding to decide on (money at stake)
Review pages show hand-entered prices next to "Check Price on Amazon" buttons ("From $449", "~$599"). Amazon's policy says a site may not show Amazon prices
unless Amazon serves them or the API supplies them. The prices on the site come from the maker's pages (scripts/price-sources.json, 139 records with source URL
and verified date), which helps, but a reader sees the number beside an Amazon button. Options, safest first:
1. Label every price as "maker's list price, checked <date>" with the source link, state that Amazon's price may differ, and keep the prices away from the Amazon button text.
2. Show price ranges or "see current price on Amazon" instead of numbers.
3. Get API access and show live, time-stamped prices (this also makes accurate `Offer` markup defensible).

## Structured data that is truthful and useful
- `Article.citation`: the sources a page cites (from scripts/sources.json), as CreativeWork/URL values. schema.org: "A citation or reference to another creative work".
- `Article.about` (primary subject, e.g. "Hearing aids") and `mentions` (named products, as plain `Thing`s with a name; no Offer, no Product snippet).
- `Article.author.url` pointing to about.html (Google recommends a URL that identifies the author).
- Organization: `publishingPrinciples` -> how-we-review.html, `correctionsPolicy` -> about.html#corrections, `ownershipFundingInfo` -> affiliate-disclosure.html.
  All three are valid on Organization per schema.org and describe real pages.
- Organization `logo` once a raster file is supplied.
- Do NOT add: Product/Offer (no merchant role), Review/AggregateRating (no testing), MedicalWebPage `reviewedBy` (no medical reviewer), prices or InStock.

## Real data (content, not markup) the site can publish honestly
- A visible "What we checked and when" box per page: price/terms register rows with source link and verified date (the data already exists).
- Derived cost tables with the arithmetic and inputs shown (for example 3-year cost of a medical alert = equipment + monthly fee x 36), each input linked to its source.
- Terms-we-read tables (contracts, cancellation, activation) linked to the company policy page, as done for Medical Guardian.
- Canada province-by-province funding tables with official links (hearing aids, blood pressure monitors).
- Dated change notes per page (what changed, why, source).
- Original data a competitor cannot copy: a public price/terms history from the monthly audit (history.json keeps 12 runs; start publishing a trend once it has data).
