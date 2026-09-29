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

1. **Tracking ID: `techfordad-gifts-20`** (created by the user on 2026-09-29 inside the existing `techfordad0b-20` account). Use it only on links inside `gift-guides/`. Link format: `https://www.amazon.com/dp/ASIN?tag=techfordad-gifts-20` with `rel="sponsored noopener"`. Rules require confirming the ID is active in Associates Central before the first guide is published; one test click and a look at the Tracking ID report the next day is enough.
2. **Show prices carefully.** Amazon's Associates rules restrict quoting prices unless they are current or clearly dated. The existing articles use "approximate, checked on [date]" wording. The guides should do the same, or show price bands such as "under $50" instead of exact figures. Please confirm which you prefer.
3. **Amazon changed prices once already in 2026.** Expect more movement before Christmas. Re-run the checker the week each guide publishes.
4. **Sunbeam throws**: no current recall found for these models, but the CPSC page should be checked on publish day.
5. **Hub URL:** the architecture note says "techfordad.com/gift guides". A space is not valid in a URL. Proposed: `/gift-guides/` with the hub at `gift-guides/index.html`.
6. **Timing:** the rules ask for guides to be indexed a few weeks before the season. Publishing by mid-October fits.

## Open decisions for you

* Price display: exact "about $X, checked [date]" or price bands only.
* Whether to include Canada versions later. Canada links must use `abhikar91-20` (or its own Canada tracking ID), not the US ID.
* Keep the two duplicate-risk items (Aura, Ember) in Guide 3 only, and Skylight in Guide 2 only.

## What people actually search for (added 2026-09-29)

**Method and limits.** I read the live autocomplete lists on Google and Amazon for about 60 gift phrases, then expanded four core phrases across the alphabet (about 780 suggestions). Autocomplete is ordered by popularity, so it shows what people type most, but it gives no search-volume numbers. Google Trends and Keyword Planner were not available to me. Treat this as a ranking of demand, and confirm with Search Console once pages are live.

**1. Wording matters. "Elderly" beats "seniors".**
* "Gifts for seniors" is polluted by high-school seniors ("in high school", "farewell", "basketball night"). Many suggestions are not about older adults.
* "Gifts for elderly ...", "older adults" and "elderly parents" are clean. Use them in titles and H1s, with "seniors" in the body.

**2. Audience phrases, strongest first** (they appear across almost every seed):
* who **women / men / mom / dad / parents / mother / father**: "gifts for elderly women", "elderly men", "elderly mom", "elderly dad", "elderly parents"
* **"who have everything"** and "who want nothing" (shows up under seniors, grandparents, elderly parents, mom, dad, men and women)
* **age**: over 80, over 90, and exact ages (70, 75, 80, 85, 90, 100 year old woman/man/mom/dad)
* **birthday** (evergreen, all year) and **Christmas** (seasonal)
* **nursing home / assisted living / care home / hospital**
* **dementia** ("gifts for elderly with dementia", "best gifts for elderly woman with dementia")
* **mobility, wheelchair, bedridden, arthritis, live alone, lonely**
* **grandma / grandpa / grandparents**, but see the warning below

**3. Warnings from the data.**
* "Gifts for grandparents" is mostly people buying for *new* grandparents or kids making crafts (baby announcement, DIY, from toddler, Grandparents Day). Only "who have everything" and "elderly grandparents" match our audience.
* "Nursing home" searches are heavily "bulk" (activity directors buying for many residents). Not our reader.
* "Under $50 / $25 / $20 for seniors" gets little senior-specific autocomplete; generic "gifts under $50" is a crowded topic. Price tiers work better inside a guide than as the headline.

**4. Products people search for on Amazon** (from "___ for elderly" suggestions):
* Safety and daily living: slippers to prevent falls, motion night lights, pill organizers (AM/PM, easy open), lap and TV trays, reachers and grabbers, walker bags, non-slip shoes, bed and door alarms
* Comfort: heated blankets ("safe heated blanket for elderly"), robes, pajamas, heated socks, gentle massagers, cushions
* Communication and TV: phones (easy to use, hard of hearing, with photos), tablets with large fonts, **TV speakers and headphones**, simple remotes, digital picture frames
* Dementia-related: fidget blankets, **day and date clocks**, large-piece puzzles, one-touch music players, GPS jewelry and trackers
* Small helpers: magnifiers, spill-proof mugs, large-print books and calendars

**5. How this compares to the current plan.**

| Plan item | Demand match |
|---|---|
| Night lights, pill organizer, magnifier, armchair caddy, heated throw, massager | Strong match |
| Digital frames (Skylight, Aura), tablets | Strong match |
| Slippers (Bombas) | Match, but people want "to prevent falls"; add a fall-focused option |
| Phones (Jitterbug rejected) | Big demand; the site's existing phone reviews should be linked instead |
| TV headphones and speakers | **Big demand, and we rejected the only product (Sennheiser, 3.8 stars); needs a better pick** |
| Day and date clocks, large-piece puzzles, fidget blankets, simple music players | **Big demand, not in the plan yet** |
| Bird feeder, Ember mug, Click & Grow | Nice ideas, but no evidence of search demand; fine for "who have everything" only |
| Apple Watch SE, iPad, Kindle | Lower demand than the rest; keep as premium picks |

**6. Suggested changes to the guide lineup** (for your decision):
1. **Gifts for Elderly Parents Who Have Everything** (merge planned Guide 3 with the "elderly parents" cluster; strongest phrase across the data)
2. **Tech Gifts for Elderly Parents and Seniors** (matches "tech gifts for seniors / elderly / elderly parents")
3. **Inexpensive Gifts for Elderly Parents (under $50)** (planned Guide 1, with the price tier inside)
4. **Gifts for Someone With Dementia** (new; a large, sensitive cluster; needs careful wording and safety notes)
5. **Gifts for Elderly in a Nursing Home or Assisted Living** (new; Christmas-heavy)
Also weave "birthday" into each guide, since birthday intent is evergreen.

**7. Competition (quick check).** The Google results for "gifts for elderly woman who has everything" and "christmas gifts for elderly parents" are mostly small blogs, Etsy, Pinterest and home-care companies, not big publishers. Dementia results are led by alz.org, the Alzheimer Society of Canada and care providers, so that one needs cited sources. No obvious giant dominates the "elderly parents" cluster, which is the opening.

**8. Next research needed** for the new items: TV listening device, dementia day clock, large-piece puzzle, fall-prevention slippers, fidget blanket, simple music player, lap tray.

## Tech-first research update (added 2026-09-29)

Direction agreed: guides stay **tech-led (about 80%)** with **2 to 3 non-tech "comfort and safety add-ons"** per guide, placed last. More non-tech is allowed only in the dementia guide, backed by Alzheimer's organization advice. Existing site reviews are linked from each guide (GPS trackers, TV remotes, pill dispensers, medical alerts, phones, doorbells, hearing).

**Authority source found:** the Alzheimer's Association gift guide (alz.org) recommends a large-type digital clock with date and time, GPS trackers, a photo-enabled "memory" phone, framed photos with names, dry-erase calendars, no-spill cups and label makers. This backs the tech-led dementia guide.

### New tech candidates (listings opened 2026-09-29 unless noted)

| Category | Product | ASIN | Price (source) | Rating (count) | Notes |
|---|---|---|---|---|---|
| TV listening | **Avantree Ensemble** (dock, works by optical, AUX or Bluetooth) | B08629PFFQ | $109.99 (Amazon) | 4.3 (15,352) | Best-reviewed pick; replaces the rejected Sennheiser (3.8) |
| TV listening | Avantree Opera (passes audio through to a soundbar) | B08D6GHYD7 | $139.99 (Amazon) | 4.3 (4,566) | For homes with a soundbar |
| TV listening | SIMOLIO 2.4G TV headphones, spare battery | B07HP1N2RC | $109.99 (Amazon) | 4.1 (2,002) | Cheaper: B08DHQ7J57 at $89.99, 4.3 (500). Maker warns RF headsets are not for pacemaker users or severe hearing loss |
| Day clock | **American Lifetime dementia clock** | B019G79V1Q | $59.95 (Amazon) | 4.6 (23,798) | Best-reviewed; custom alarms |
| Day clock | AINFTIME day and date clock (7") | B0BKV7TVNL | $29.99 (Amazon) | 4.5 (1,351) | Under-$50 pick; SSYA (B0DM5TNSPZ, $54.99, 4.6, 7,462) is the premium alternative |
| Easy TV remote | Flipper big-button remote (TV and cable only, no streaming apps) | B0CR5S1BCN | $39.95 (Amazon) | 4.2 (1,401) | Already ranked #1 in the site's remote review; cannot navigate streaming apps |
| Camera | WYZE Cam v4 | B0CJ9Z22L5 | $44.98 (Wyze) | 4.3 (11,348) | microSD recording without a subscription; card sold separately |
| Camera | Blink Mini 2 | B0BWWZXWPL | about $40 (Security.org) | 4.5 (11,906) | Easiest with Alexa ("show me the living room"); Blink cloud plans start at $3.99/month, live view is limited without one |
| Camera | eufy Indoor Cam S350 (4K) | B0CD7F1M9R | $129.99 MSRP (PCWorld, Tom's Guide) | 4.4 (2,385) | No subscription; local storage; privacy mode |
| Fidget blanket (dementia add-on, non-tech) | 18-in-1 fidget blanket | B09JBJ7C8W | $39.81 (Amazon) | 4.5 (317) | Cheaper: B08R6DG3Q1 at $17.99, 4.1 (500); check the care team first and avoid small loose parts |

**Camera note for the guide:** cameras in a parent's home need the parent's consent, should stay out of bedrooms and bathrooms, and should be described as check-ins, not surveillance.

### Not recommended yet
* **Simple music players (Amazon brands such as VigorKeeper, ClaspVital, Healvaluefit):** $115 to $140 each, but only 33 to 89 ratings and scores between 3.6 and 4.6. The only older, better-known one, SMPL (B01B9THLUW, 4.4 from 420 ratings), had no readable price. Wait until a better-reviewed product is found.
* **Fall-prevention slippers:** none with strong reviews. Silverts 3.9 (1,553), shower shoes 4.1 (1,204). No slipper guarantees fall prevention, so Bombas stays a comfort add-on with a careful caption.

### Not yet verified (Amazon rate-limited the checker mid-run)
GE BigEZ remote 84666 (B0FWL14KM6), UltraPro BigEZ 85053 (B0F6SVQLBQ), Flipper universal remote (B002GR1YZ0), GE 4-device remote 71262 (B0C62L1FPT). Re-run `scripts/check_amazon_listings.py` after waiting several minutes. The script now reports `status: blocked` when Amazon serves its robot-check page.

### Proposed tech-led lineup (draft, for your approval)

1. **Tech Gifts for Elderly Parents:** Skylight Frame, Echo Show 8, iPad or Fire HD 10, Kindle Paperwhite, Avantree Ensemble TV headphones, Flipper remote. *Add-ons:* armchair caddy, lighted magnifier.
2. **Safety Tech for Elderly Parents Who Live Alone:** Apple Watch SE 3, AirTag (keys), Blink Mini 2, WYZE Cam v4 or eufy S350, Ring doorbell, Lyridz night lights. Links to the site's GPS tracker, medical alert, doorbell and pill dispenser reviews. *Add-on:* extra-large pill organizer.
3. **Tech Gifts for Someone With Dementia:** American Lifetime clock, Flipper remote, AirTag, photo frame, Echo Show 8 for early stages, links to the site's GPS tracker and phone reviews. *Add-ons (cited to alz.org):* fidget blanket, soft cushion, no-spill cup.
4. **Tech Gifts for Seniors Under $50:** AirTag $29, AINFTIME clock $29.99, Flipper remote $39.95, Fire TV Stick HD about $40, Blink Mini 2 about $40, WYZE Cam v4 $44.98, Lyridz night lights $26.99, Nazano magnifier $14.89. *Add-ons:* armchair caddy $9.98, pill organizer $6.99.
5. **Gifts for Elderly Parents Who Have Everything:** Aura Carver Mat, Ember Mug 2, Click & Grow, Birdbuddy Pro. *Add-ons:* Sunbeam throw, Bombas slippers.

### Prices still unconfirmed
Aura, Birdbuddy Pro, Omron, Ravensburger puzzle, Blink Mini 2 (third-party source only), Fire TV Stick HD (press-based), and the four unverified remotes. All get re-checked the week each guide publishes.

## Fall detection gadgets (added 2026-09-29, replaces the slipper idea)

Clarified direction: "fall detection" means **tech gadgets**, not footwear. The fall-prevention slipper item is dropped from the plan. Bombas stays only as an optional comfort add-on in Guide 5, with no fall-prevention claims.

### What testing says (use this wording in the guide)
* AARP tested 16 devices with 12 controlled lab falls each (chair, standing, sideways, backward). LifeStation (Pearl and Sidekick) and IRIS Ally caught **all 12**. Bay Alarm SOS Home and the LifeFone devices caught **9 of 12**.
* AARP's own caveat: **"No fall detection is 100 percent accurate."** In its user survey about 72% said their device works as intended, 14% said it sometimes works, 1% said it failed.
* A published smartwatch study found 77% of falls detected, with 16% missed. Independent write-ups put smartwatch detection at roughly 60% to 80% for fast falls and lower for slow ones, like sliding out of a chair.
* **A University of Illinois study found the Apple Watch detected only 14 of 300 falls by wheelchair users (about 5%).** The guide must say wheelchair users should not rely on it.
* Fall detection is an **add-on cost** on most monitored devices: about $8 to $10 a month on top of the base plan. Base monitoring runs about $25 to $45 a month.
* The gadget should be described as a backup, not a replacement for pressing the help button or for checking in.

### Fall detection gadgets that are sold on Amazon

| Device | ASIN | Cost (source) | Notes | Listing check |
|---|---|---|---|---|
| Apple Watch SE 3 (GPS, 40mm) | B0HJB1CGR3 | $249; plan $0 to about $25/mo (Apple, SeniorList) | Fall Detection on by default at 55+; needs an iPhone; 4.7 stars from 4,551 ratings | Verified |
| Samsung Galaxy Watch9 (40mm Bluetooth) | B0H9BPZXZC | about $379.99 (site's price file, Sep 2026) | Android option; the Amazon listing is a bundle with a $50 gift card, so check the exact variant | Pending |
| Lively Mobile2 | B0CV83V94H | $119.99 device; plans from $24.99/mo; fall detection +$9.99/mo (site price file) | Must be activated with Lively; SafeHome notes the pendant battery lasts about a day and a half | Pending |
| Bay Alarm Medical SOS Mobile GPS | B0C4QTKR83 | device price to confirm; fall detection about $10/mo extra (AARP, SafeHome) | 4G GPS; AARP's Bay Alarm SOS Home caught 9 of 12 falls; "call to activate" | Pending |
| Bay Alarm Medical SOS Micro | B0DJ1YW9JZ | to confirm | Under 1.2 oz; optional fall detection | Pending |
| Medical Guardian MGMobile / MGMini | B0BYTJK59D / B0CHGXYM2X | to confirm; subscription required | Monitoring plan needed before it works | Pending |
| LifeStation Mobile (On-the-Go) | B07G9MTFX8 (6-month version: B07G9LX816) | plans about $35 to $51/mo; fall detection $8 to $16 extra (SeniorList, NCOA) | Caught all 12 falls in AARP's test (Pearl and Sidekick models; confirm the exact model listed) | Not yet checked |

"Pending" means the listing was found on Amazon but Amazon blocked my verification requests after about 130 checks today. A slow background check is queued and will fill this column in.

### Avoid
Generic "no monthly fee, automatic fall detection" pendants on Amazon (for example B01H2DNBSA, B0CNL3QVVZ, B0C5Y5534H) are unbranded or little-known, with no independent test results. They are not recommended until they have been checked. LogicMark Guardian Alert 911 Plus is a known brand but was not verified.

### Where it goes in the lineup
* **Guide 2, Safety Tech for Elderly Parents Who Live Alone:** lead with Apple Watch SE 3 (iPhone families), Galaxy Watch9 (Android families) and one monitored mobile pendant (Lively Mobile2 or Bay Alarm SOS Mobile GPS). Include the accuracy section and the running cost table. Link to the site's medical alert and smartwatch reviews.
* **Guide 3, Dementia:** GPS tracker and AirTag stay; add a caution that fall detection depends on the person keeping the device on.
* **Guide 4, Under $50:** none of these fit; they are all over $100 or subscription-based.

## Verification update (2026-09-29, after Amazon's block cleared)

Listings opened and buyable, with ratings: Lively Mobile2 (4.1 stars, 247 ratings), Bay Alarm SOS Mobile GPS (4.0, 99), Samsung Galaxy Watch9 40mm (4.5, 357; **$379.99 on Amazon**), Medical Guardian MGMobile (3.2, 60 - weak, not recommended), Medical Guardian MGMini (3.9, 299), Lively Mobile Plus (4.3, 595), Flipper universal remote (4.4, 8,326), GE BigEZ 84666 ($12.25, 4.2, 73), UltraPro BigEZ 85053 ($16.49, 4.4, 99), GE 4-device remote 71262 (3.6, 102).

The generic "no monthly fee" fall-detection pendants confirm the earlier decision to avoid them: B01H2DNBSA 2.7 stars (18 ratings), B0CNL3QVVZ 3.3 (24), B0C5Y5534H 3.7 (197).

Still not verified: LifeStation Mobile (B07G9MTFX8), plus exact prices for Aura, Birdbuddy Pro, Omron and the Ravensburger puzzle. Verify these before publishing.
