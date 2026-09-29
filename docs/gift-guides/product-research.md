# Gift Guides: product research (checked 2026-09-29)

Research for the three launch guides in the PRD. Nothing here is published on the site yet.

## How this was checked

* **Candidates** came from independent gift and tech guides: NCOA (June 2026), AARP (Dec 2024), NBC Select (Dec 2025), CNN Underscored, Aging at Ease (2026), plus what the site already reviews.
* **Every Amazon listing** was opened on 2026-09-29 (US storefront, USD). Recorded: ASIN, title, star rating, rating count, and whether the listing is buyable (has an Add to Cart button). All 48 listings checked are live and buyable, including every product recommended below.
* **Prices** come from Amazon's buy box when Amazon shows one, otherwise from the manufacturer or a named news source. Amazon hides the price on many variation pages, so about half the prices below are from other sources. Those are marked.
* **Amazon raised device prices on 2026-08-21** (memory-chip costs). Older figures for Echo, Kindle and Fire TV are wrong now. Only post-increase figures are used here.
* Re-run `python3 scripts/check_amazon_listings.py out.json ASIN ...` before publishing to re-check listings and prices.

Confidence: **High** = price and listing both confirmed today. **Medium** = listing confirmed, price from another source or a range. **Low** = listing confirmed, price not yet found.

## Guide 1: Gifts under $50 for seniors

Rule: the buy price must be $50 or less. Bombas slippers ($55, NCOA) and the Sunbeam Royal Ultra throw ($69.99) were dropped for this reason.

| # | Product | ASIN | Price | Rating (count) | Why it fits | Watch out for | Conf. |
|---|---|---|---|---|---|---|---|
| 1 | Apple AirTag (2nd gen), 1 pack | B0GJTFXNRX | $29 (Apple) | 4.6 (11,326) | Finds keys, wallet, glasses case | iPhone or iPad only; Android users need the Chipolo below | High |
| 2 | Chipolo ONE Point (Android) | B0C4W2VGTX | $28 (Chipolo, via search) | 3.9 (613) | Same idea for Android phones | Lowest rating in the set; optional | Medium |
| 3 | MagicMakers shiatsu neck massager with heat | B07FNGP1SV | $39.99 (Amazon) | 4.4 (11,870) | Wide seller, easy corded use | Heat and deep kneading are not for everyone (numbness, pacemakers); say "check with a doctor" | High |
| 4 | Lyridz 6-pack motion-sensor night lights | B08HGXV837 | $26.99 (Amazon) | 4.6 (8,317) | Hallway, bathroom and kitchen lighting for night trips | None found | High |
| 5 | Nazano lighted magnifier | B08PP4RJ5J | $14.89 (Amazon) | 4.5 (21,443) | Pill labels, menus, small print | Needs AA batteries | High |
| 6 | Sukuos extra-large weekly pill organizer | B07V1QCJGF | $6.99 (Amazon) | 4.7 (25,509) | Big compartments, easy to open | Not a substitute for a reminder system | High |
| 7 | Joywell armchair caddy | B07GDBWNXW | $9.98 (Amazon) | 4.5 (11,899) | Remote, phone and glasses stay within reach | None found | High |
| 8 | Bicycle jumbo-index playing cards, 2 pack | B000BUUTJ6 | $5.63 (Amazon) | 4.8 (12,536) | Large print, made in the USA | None found | High |
| 9 | Ravensburger 1,000-piece puzzle (Great New York) | B01NH0USHR | Not read; NCOA priced a puzzle at $28 | 4.7 (1,391) | Popular quiet hobby | Price to confirm | Low |
| 10 | YETI Rambler 20 oz tumbler | B073WJMKHN | $35.00 (Amazon) | 4.8 (147,919) | Keeps coffee hot | MagSlider lid is not leak-proof | High |
| 11 | Fire TV Stick HD | B0DJGDC3BD | about $40 (Amazon lineup, Aug 2026) | 4.1 (5,707) | Alexa voice remote | Someone must set it up; only for TVs with a free HDMI port | Medium |

Not included: a Sunbeam throw under $50. Sunbeam flannel throw B0D87RLDT7 (4.4, 8,383 ratings) is live but its price was not readable. If it is $50 or less it can be added as #12.

## Guide 2: Tech gifts seniors actually use

Rule: only devices with a clear, low-effort daily use, and only after setup by the giver.

| # | Product | ASIN | Price | Rating (count) | Why it fits | Watch out for | Conf. |
|---|---|---|---|---|---|---|---|
| 1 | Skylight Frame 10" | B01N7ENHO6 | about $139 to $160 (Walmart, Michaels) | 4.7 (27,558) | Family emails photos to the frame; nothing for the grandparent to learn | Skylight Plus is $39/yr and is needed for the app and cloud features; emailing photos stays free | Medium |
| 2 | Amazon Echo Show 8 | B0DC8ZMR1P (Glacier White: B0DC93K4NW) | $199.99 (press, Aug 2026) | 4.3 (8,008) | Voice-started video calls to family | Alexa+ is free with Prime, otherwise $19.99/month; basic video calling works without it | High |
| 3 | Apple Watch SE 3 (GPS, 40mm) | B0HJB1CGR3 | $249 (Apple) | 4.7 (4,551) | Fall Detection turns on by default at age 55+; can call emergency services if the wearer is still | Needs an iPhone; the GPS model needs the phone or Wi-Fi for calls | High |
| 4 | iPad (A16, 11-inch, Wi-Fi, 128GB) | B0DZ75TN5F | $449 (Apple) | 4.7 (29,015) | Video calls, photos, reading | Priciest item here; set up text size and Accessibility first | High |
| 5 | Kindle Paperwhite (16GB) | B0CFPJYX7P | $199.99 (press, Aug 2026) | 4.6 (23,214) | Adjustable text size, glare-free screen | Up $40 in August | High |
| 6 | Omron Bronze upper-arm blood pressure monitor | B07S2H3XB9 | Not read; Omron lists similar models at $60 to $91 | 4.6 (37,395) | Trusted brand, one-button use | Confirm the exact model and price; not a substitute for medical advice | Low |
| 7 | Amazon Fire HD 10 | B0BL5XPDR6 | $154.99 (one news source) | 4.5 (44,471) | Cheaper tablet | Price rests on a single source | Medium |

## Guide 3: Gifts for grandparents who have everything

| # | Product | ASIN | Price | Rating (count) | Why it fits | Watch out for | Conf. |
|---|---|---|---|---|---|---|---|
| 1 | Aura Carver Mat digital frame (10") | B0BG3F79LF | Not read; a Costco listing of the Carver was $99.99 | 4.7 (13,894) | Free unlimited photo storage, family can add photos; Aura says Wirecutter and Wired recommend it, and a 2026 roundup ranked it first (not checked at the source) | Price to confirm; the Mason model is being replaced | Low |
| 2 | Ember Mug 2 (10 oz) | B07NQPYGYD | $89.99 (Amazon) | 4.7 (20,891) | Keeps coffee at a set temperature | Hand wash only; about 90 minutes off the coaster; Ember's own site now sells Mug 3 at $149.95 | High |
| 3 | Sunbeam Royal Ultra Fleece heated throw | B008BF2MFM | $69.99 (Amazon) | 4.4 (10,444) | Comfort for daily use | See the recall note below | High |
| 4 | Click & Grow Smart Garden 3 | B01MRVMKQH | $101.60 (Amazon) | 4.6 (2,377) | Fresh herbs indoors, no green thumb needed | Pods are a recurring purchase | High |
| 5 | Birdbuddy Pro smart bird feeder | B0DHY6CQBC | Not read | 4.3 (212) | Watch birds and get photos on a phone | Needs a 2.4 GHz Wi-Fi network; premium membership is optional at $39/yr; pole not included; few reviews | Low |
| 6 | Bombas Gripper slippers (women's) | B0GQLQL62V | about $55 (NCOA) | 4.4 (26,054) | Grip soles for safer steps | Men's version has only 683 ratings | Medium |
| 7 | Ravensburger Cabinet of Curiosities 1,000-piece puzzle | B0CPM917RM | $31.20 (Amazon) | 4.9 (54) | Giftable hobby | Few reviews | High |

Non-Amazon ideas that experts recommend (Storyworth about $89 to $99, Remento $99, Wonderbly $90, MasterClass) fit the "has everything" theme but are out of scope, because the PRD is Amazon-only for this phase. They could be mentioned without links.

## Considered and rejected

| Product | Why |
|---|---|
| Sennheiser RS 120-W TV headphones ($159.95) | 3.8 stars across 3,662 ratings |
| Jitterbug Flip2 (B08HVVCBHL) | 4.0 stars; needs a Lively plan from $34.99/month; Lively's newer Flip3 exists; ConsumerAffairs reviews complain the keys and screen are small |
| Jitterbug Smart4 | 3.9 stars |
| Echo Dot | Now $79.99 after the August increase |
| Echo Pop | Listing fine (4.7, 103,752) but no current price found |
| Fire TV Stick 4K Select and Plus | $50 and $70 after the increase; the HD stick is enough for most |
| Ring Battery Doorbell | Needs installation and a plan for saved video |
| Sunbeam queen heated blanket | CPSC recall March 2023 (model 32810027); throws are different models, but check CPSC before publishing |

## Flags before writing

1. **Tracking ID does not exist yet.** You need to create the Gift Guides tracking ID in Amazon Associates Central (Account, Manage Tracking IDs). It is created inside the existing `techfordad0b-20` account, not a new account. I will not invent a tag: a made-up tag earned nothing on the Canada pages. Until you give me the ID, links use the placeholder `TAGPENDING`.
2. **Show prices carefully.** Amazon's Associates rules restrict quoting prices unless they are current or clearly dated. The existing articles use "approximate, checked on [date]" wording. The guides should do the same, or show price bands such as "under $50" instead of exact figures. Please confirm which you prefer.
3. **Amazon changed prices once already in 2026.** Expect more movement before Christmas. Re-run the checker the week each guide publishes.
4. **Sunbeam throws**: no current recall found for these models, but the CPSC page should be checked on publish day.
5. **Hub URL:** the architecture note says "techfordad.com/gift guides". A space is not valid in a URL. Proposed: `/gift-guides/` with the hub at `gift-guides/index.html`.
6. **Timing:** the rules ask for guides to be indexed a few weeks before the season. Publishing by mid-October fits.

## Open decisions for you

* Price display: exact "about $X, checked [date]" or price bands only.
* Whether to include Canada versions later. Canada links must use `abhikar91-20` (or its own Canada tracking ID), not the US ID.
* Keep the two duplicate-risk items (Aura, Ember) in Guide 3 only, and Skylight in Guide 2 only.
