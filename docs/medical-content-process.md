# Medical content: how we research, source and update (AI-assisted, transparent)

Applies first to: medical alerts, hearing aids, blood pressure monitors, fall prevention, GPS trackers for dementia,
pill organizers, sleep trackers, smartwatches (health features). Google treats these as "your money or your life" topics,
so they need the most care.

## Principles (what keeps the site fair, transparent and legal)

1. **AI helps research and draft; it is never the source.** Every health fact needs a named source a reader can open.
   If no source can be opened, the sentence is softened to what is verified, or removed.
2. **No invented experience.** We do not claim hands-on testing, medical review, credentials or quotes we do not have.
   The site already says this (About, How We Review). Keep it true on every page.
3. **Say how the page was made.** The About and How We Review pages disclose that AI helps gather specs and draft guides.
   Google's guidance asks for this ("who, how, why"); it does not ban AI content, it penalises unhelpful, unsourced content.
4. **Affiliate honesty.** Keep the Amazon Associates sentence and the disclosure box; never let a commission change a ranking.
5. **Not medical advice.** Health pages point readers to their doctor or pharmacist for decisions.
6. **Canada and USA stay in step.** A health fact fixed on one page is checked on its twin (Health Canada, Hypertension Canada
   and CRTC wording differ from the US ones).

## Per-page procedure (one medical page at a time)

1. List every health claim: numbers, thresholds, regulatory statements, "recommended by", "validated", risk multipliers.
2. For each claim, open a primary source (government, professional body, maker documentation, peer-reviewed or
   independent lab test). Prefer: CDC, NIH/NHLBI/NIDCD, FDA, Health Canada, Hypertension Canada, AHA/AMA/AARP, maker pages.
3. Classify each claim: **confirmed** (wording matches source), **soften** (source says less than we do), **remove**
   (no source), or **unverifiable** (source blocks automated reads; do not cite what you could not open).
4. Edit the sentence to match the source and link it inline (`target="_blank" rel="noopener"`).
5. Add the same source to `scripts/sources.json` with `used_for` worded as exactly what the page covers, then run
   `python3 scripts/build_sources.py --verify` and `python3 scripts/build_nav.py`.
6. Only if the content really changed, move `dateModified`. Never change a date without a content change.
7. Log it below.

## Tools that block automated reads (record, do not bypass)

heart.org, mayoclinic.org and validatebp.org return 403 to scripted fetches; open them in a browser and cite only what a person
has read. The AHA "Eastern States" affiliate and CDC/NHLBI pages were readable.

## Log

| Date | Page | Result |
|------|------|--------|
| 2026-10-05 | best-blood-pressure-monitors-for-seniors | Confirmed: upper-arm and validated monitors, 5 min rest, 2 readings 1 min apart, 180/120 emergency threshold, AFib fivefold stroke risk (AHA). Softened: "leading risk factor" to CDC wording ("increases the risk"); removed unsourced "5 mmHg" and "10 to 15 mmHg" figures. Added CDC and AHA sources. |
| 2026-10-05 | best-hearing-aids-for-seniors, hearing-aids guide | Confirmed FDA OTC rule (adults 18+, perceived mild to moderate, Oct 17 2022), Medicare (no coverage for hearing aids or fitting exams), NIDCD prevalence (1 in 3 ages 65-74). Removed unsourced: "third most common chronic condition", "7 year wait", "$4,600 average", Medicare Advantage dollar range, FSA/HSA "eligible: yes" (IRS 502 only confirms hearing aids are medical expenses). |
| 2026-10-05 | best-hearing-aids-canada | Corrected: Ontario ADP is 75% up to $500 per side (no "every five years" or "age 19" confirmed); Manitoba seniors program is up to $2,000 for 65+ with household net income under $80,000 (the 80% figure is the children's program); Alberta AADL is 25% cost share up to $500 per family per year; BC funding is up to $2,000 per aid for people on income/disability assistance; StatCan 78% (ages 60-79); DTC and METC wording from CRA. Removed unverified Ontario OTC consultation claim; AirPods hearing feature status cited to Apple's own statement (July 2025). |
| 2026-10-05 | best-medical-alert-systems (+Canada), life-alert-vs-medical-guardian, medical-alert-no-monthly-fee | CDC: falls are the leading cause of injury death for 65+ (43,000+ deaths in 2024). NCOA: Original Medicare does not pay for medical alert systems; most Medicaid does not. Ontario ADP does not fund medical alert systems ("life-alert systems" are listed as not covered). Life Alert vs Medical Guardian rewritten with attributed figures (NCOA, company pages); removed unsourced response-time rankings and absolute claims. Conflict noted: Medical Guardian's page says cancellation fees may apply; NCOA says none. |
| 2026-10-05 | best-blood-pressure-monitors-canada | StatCan 2023 (19.9% adults, 45.0% of 65+, self-reported); Hypertension Canada list confirms 4 of 5 monitors and its wrist-monitor stance; Medical Devices Regulations s.23(3) for bilingual labelling. Removed unverified Heart and Stroke 1-in-4 and 10-20 mmHg wrist figures. |
| 2026-10-05 | best-smartwatches (US, Canada), best-gps-trackers (US), gps-trackers guide, pill organizers, sleep trackers, fall-prevention and home-safety guides | CDC fall figures; Alzheimer's Association (6 in 10 wander; call 911 if not found in 15 minutes); Alzheimer Society of Canada (ethics, no device guarantees). Removed the "CDC 125,000 deaths" non-adherence claim (its origin is not CDC); corrected 65+ sleep guidance to CDC's 7 to 8 hours; softened unsourced absolutes ("most falls happen in the bathroom", etc.). |

## Open items for a human

- Medical Guardian: the monthly price and cancellation terms differ between its own page ($34.95, fees may apply) and NCOA ($38.95, no cancellation fees). Run the monthly price audit on the Medical Guardian lines in the US medical alerts article.
- guides/hearing-aids.html still lists older products (Sony CRE-E10, Lexie B2, Jabra Enhance Plus) that its own newer section and the US article say are discontinued or replaced.
- Quebec/RAMQ hearing aid wording, Costco Canada pricing and several maker-sourced product claims were not re-verified in this pass.
- Open in a browser (they block scripted reads): heart.org, mayoclinic.org, validatebp.org, canada.ca pages, cdc.gov pages.

## Next in line

Hearing aids (US, then Canada), medical alerts (US, Canada), fall prevention guide, GPS tracker/dementia guide, pill organizers.
