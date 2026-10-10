#!/usr/bin/env python3
"""Build the Gift Guides section: gift-guides/index.html plus five guides.

    python3 scripts/build_gift_guides.py
    python3 scripts/build_nav.py        # adds the header dropdown, season script and cache versions

All content lives in this file. Amazon links use the dedicated Gift Guides tracking ID
(see CLAUDE.md); never use the site-wide tag inside gift-guides/. Prices are written as
"about $X" with a checked-on date because Amazon's rules restrict quoting stale prices.
Re-run scripts/check_amazon_listings.py and update PRICE_DATE before publishing.
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "gift-guides")
TAG = "techfordad-gifts-20"
PRICE_DATE = "September 30, 2026"   # date prices were last checked; change with --checked, never by hand
UPDATED_LABEL = "September 2026"    # shown as "Updated ..." on the pages; follows PRICE_DATE
PUBLISHED = "2026-09-29"            # first publish date (structured data)
MODIFIED = "2026-09-30"             # last modified date (structured data); follows PRICE_DATE
SITE = "https://www.techfordad.com"


SHORT_LABEL = "Sep 2026"            # short form used in price notes such as "(Amazon, checked Sep 2026)"


def stamp(s):
    """Any date written into the content below follows the single 'checked' date at the top of this file."""
    return s.replace("September 29, 2026", PRICE_DATE).replace("Sep 2026", SHORT_LABEL)


def e(s):
    return html.escape(stamp(s), quote=True)


def amazon(asin):
    return f"https://www.amazon.com/dp/{asin}?tag={TAG}"


# ---------------------------------------------------------------- content
GUIDES = [
    {
        "slug": "tech-gifts-for-elderly-parents",
        "title": "Tech Gifts for Elderly Parents (2026 Guide) | TechForDad",
        "h1": "Tech Gifts for Elderly Parents They Will Actually Use",
        "short": "Tech Gifts for Elderly Parents",
        "desc": "Tech gifts for elderly parents that are easy to use: a photo frame, video calls by voice, an e-reader, TV headphones and a big-button remote.",
        "card": "A photo frame, video calls by voice, an e-reader, TV headphones and a big-button remote.",
        "hero": "hero-ipad-setup.jpg",
        "hero_alt": "Hands using a tablet",
        "subtitle": "Devices with one clear, low-effort benefit: seeing family photos, calling by voice, reading larger type, hearing the TV. Set each one up before you give it.",
        "intro": [
            "The best tech gift for an elderly parent solves a daily annoyance without adding something new to learn. This guide sticks to devices with one clear benefit: seeing family photos, calling someone by voice, reading in bigger type, hearing the TV, or working the remote without squinting.",
            "Older adults do buy technology. AARP's 2026 technology research found that 71% of older adults bought a tech product in 2025. The gifts that get used are the ones you set up first, so plan an hour to do that before you hand anything over.",
        ],
        "products": [
            {"name": "Skylight Frame, 10-inch", "asin": "B01N7ENHO6", "badge": "Easiest for a parent who avoids apps",
             "price": "about $139 to $160 (retail listings, Sep 2026)",
             "why": "Family members email photos to the frame's own address and the pictures appear. Your parent does nothing except look at it.",
             "best": "Parents who do not use smartphones or apps",
             "watch": "Skylight says the mobile app and cloud features need Skylight Plus at $39 a year. Sending photos by email stays free."},
            {"name": "Amazon Echo Show 8", "asin": "B0DC8ZMR1P", "badge": "Video calls by voice",
             "price": "about $199.99 (Amazon's Aug 2026 price list)",
             "why": "Say \"Alexa, call Sarah\" and the call starts. There is no phone to hold and no small buttons.",
             "best": "Parents who can talk to a speaker but find touch screens fiddly",
             "watch": "Alexa+ is free with Prime, otherwise $19.99 a month. Basic video calling works without it. The screen has a camera, so ask before placing it in a bedroom."},
            {"name": "Apple iPad (A16, 11-inch, Wi-Fi)", "asin": "B0DZ75TN5F", "badge": "Most capable",
             "price": "$449 (Apple)",
             "why": "FaceTime, photos, reading and text that can be enlarged. It does the most of anything here.",
             "best": "Parents who already use an iPhone or are ready to learn",
             "watch": "The most expensive gift on this page. Turn on larger text and Accessibility settings before you wrap it. Our guide to setting up an iPad for an elderly parent walks through it."},
            {"name": "Amazon Fire HD 10", "asin": "B0BL5XPDR6", "badge": "Lower-cost tablet",
             "price": "about $155 (reported July 2026, one source)",
             "why": "A large screen for video calls, photos and streaming at a lower price than an iPad.",
             "best": "A first tablet on a budget",
             "watch": "Amazon sells versions with and without lock-screen ads, so check which one you are buying."},
            {"name": "Kindle Paperwhite (16GB)", "asin": "B0CFPJYX7P", "badge": "For readers",
             "price": "about $159.99 (Amazon, 16GB)",
             "why": "Text size can be enlarged, and the screen is glare-free in bright rooms.",
             "best": "Parents who read every day",
             "watch": "The 32GB Signature Edition costs more, about $199.99. Books need Wi-Fi to download."},
            {"name": "Avantree Ensemble TV headphones", "asin": "B08629PFFQ", "badge": "Hear the TV without turning it up",
             "price": "about $109.99 (Amazon, checked Sep 2026)",
             "why": "Wireless headphones on a charging dock, so one person can turn up the dialogue without blasting the room.",
             "best": "Parents who keep asking for the TV to be louder",
             "watch": "Check that your parent's TV has an optical or headphone output, or use Bluetooth on a compatible TV. It suits one listener at a time."},
            {"name": "Flipper big-button TV remote", "asin": "B0CR5S1BCN", "badge": "Simple TV control",
             "price": "about $39.95 (Amazon, checked Sep 2026)",
             "why": "Large color-coded buttons for power, volume and channels, with no menus to get lost in.",
             "best": "Parents who cannot work a modern remote",
             "watch": "It cannot navigate streaming apps like Netflix or Prime Video. It controls TV and cable only."},
        ],
        "addons_title": "Comfort add-ons that pair with tech",
        "addons": [
            {"name": "Joywell armchair caddy", "asin": "B07GDBWNXW", "price": "about $9.98",
             "why": "Keeps the remote, phone and glasses within reach of the favorite chair."},
            {"name": "Nazano lighted magnifier", "asin": "B08PP4RJ5J", "price": "about $14.89",
             "why": "Helps with pill labels, menus and small print. Uses AA batteries."},
        ],
        "sections": [
            ("How to make a tech gift work", [
                "Set it up yourself, then walk through it once together. Write the two or three steps your parent will actually use on a card and tape it nearby. Check the Wi-Fi works where the device will sit, and phone them two weeks later to see whether it is being used.",
            ]),
        ],
        "faq": [
            ("What is the easiest tech gift for an elderly parent?",
             "A photo frame that family fills by email, such as the Skylight Frame, needs nothing from your parent. A big-button remote is the easiest for TV. Both work best after you have set them up."),
            ("Do these gifts need Wi-Fi?",
             "The Skylight Frame, Echo Show, iPad, Fire tablet and Kindle all need Wi-Fi to receive photos, calls or books. The TV headphones and remote do not."),
            ("Are there monthly fees?",
             "Not required. Skylight Plus ($39 a year) and Alexa+ ($19.99 a month without Prime) are optional. Check each product before you buy."),
            ("What if my parent says they do not want technology?",
             "Start with something that removes a frustration, such as the TV headphones or the big-button remote, rather than something that adds a new device to manage."),
        ],
        "related": [("../blog/best-tablets-for-seniors.html", "Best tablets for seniors"),
                    ("../blog/how-to-set-up-ipad-for-elderly-parent.html", "How to set up an iPad for an elderly parent"),
                    ("../blog/best-alexa-devices-for-seniors.html", "Best Alexa devices for seniors"),
                    ("../blog/best-tv-remotes-for-seniors.html", "Best TV remotes for seniors"),
                    ("../blog/best-e-readers-for-seniors.html", "Best e-readers for seniors")],
        "sources": [("AARP, 2026 technology trends among older adults", "https://www.aarp.org/pri/topics/technology/"),
                    ("AARP, best tech gifts for older adults", "https://www.aarp.org/personal-technology/tech-gifts-older-adults/")],
    },
    {
        "slug": "safety-tech-for-elderly-parents-who-live-alone",
        "title": "Safety Tech for Elderly Parents Living Alone | TechForDad",
        "h1": "Safety Tech for Elderly Parents Who Live Alone",
        "short": "Safety Tech for Parents Who Live Alone",
        "desc": "Fall detection watches, medical alert pendants, indoor cameras and trackers for elderly parents who live alone, with honest accuracy and monthly costs.",
        "card": "Fall detection watches, alert pendants, indoor cameras and trackers, with honest accuracy and costs.",
        "hero": "hero-fall-prevention.jpg",
        "hero_alt": "A stairwell railing",
        "subtitle": "Fall detection watches and pendants, indoor cameras and trackers. What they cost each month, and how often fall detection actually works.",
        "intro": [
            "If a parent lives alone, the question behind most gift searches is simple: how will someone know if something goes wrong? This guide covers the devices that answer it, along with what they cost every month and where they fall short.",
            "One point comes first. Fall detection is a backup, not a guarantee. Use it alongside a help button and regular check-in calls.",
        ],
        "pre_sections": [
            ("How well does fall detection work?", [
                "AARP tested 16 medical alert devices using 12 controlled falls each (falling from a chair, dropping to the knees, sideways and backward). LifeStation and IRIS Ally detected all 12. Bay Alarm Medical's SOS Home and the LifeFone devices detected 9 of 12. AARP's conclusion: no fall detection is 100 percent accurate.",
                "Smartwatches vary more. A published study of a smartwatch app found 77% of induced falls were detected and about 16% were missed. Independent reviews put smartwatch detection at roughly 60% to 80% for fast falls and lower for slow ones, like sliding out of a chair. UnaliWear's review of the research reports a University of Illinois study in which an Apple Watch detected 14 of 300 falls by wheelchair users. If your parent uses a wheelchair, do not rely on a watch for fall detection.",
            ]),
        ],
        "products": [
            {"name": "Apple Watch SE 3 (GPS, 40mm)", "asin": "B0HJB1CGR3", "badge": "Best for iPhone families",
             "price": "$249 (Apple)",
             "why": "Apple says Fall Detection turns on automatically for anyone 55 or older who entered their age. If the watch senses a hard fall and the wearer does not respond, it can call emergency services after a countdown.",
             "best": "Parents who already use an iPhone and will wear a watch",
             "watch": "It needs an iPhone. The GPS model relies on the phone or Wi-Fi for calls; cellular models add a monthly plan. It must be worn and charged daily."},
            {"name": "Samsung Galaxy Watch9 (40mm Bluetooth)", "asin": "B0H9BPZXZC", "badge": "For Android families",
             "price": "$379.99 (Amazon, Sep 2026)",
             "why": "The Android counterpart. Samsung's watches include fall detection for people who use an Android phone.",
             "best": "Parents on Android phones",
             "watch": "The Amazon listing is a bundle that includes a gift card, so check the exact variant before you buy. Confirm fall detection is switched on in the watch settings."},
            {"name": "Lively Mobile2 medical alert device", "asin": "B0CV83V94H", "badge": "No smartphone needed",
             "price": "device about $119.99; plans from $24.99 a month; fall detection about $9.99 a month more (Lively)",
             "why": "A wearable help button that connects to a monitoring center. It works without a smartphone.",
             "best": "Parents without a smartphone who want a person on the other end",
             "watch": "It must be activated with Lively and needs a plan. SafeHome's testers found the pendant battery lasts about a day and a half."},
            {"name": "Bay Alarm Medical SOS Mobile GPS", "asin": "B0C4QTKR83", "badge": "Monitored mobile pendant",
             "price": "device price varies; fall detection about $10 a month extra (AARP, SafeHome)",
             "why": "A 4G GPS pendant with a 24/7 monitoring center. AARP's tests of Bay Alarm's SOS Home detected 9 of 12 falls.",
             "best": "Parents who leave the house and want GPS location too",
             "watch": "The listing says \"call to activate,\" and fall detection is an optional add-on. Confirm the exact model when you order."},
            {"name": "LifeStation Mobile medical alert system", "asin": "B07G9MTFX8", "badge": "Worth comparing",
             "price": "plans about $35 to $51 a month; fall detection $8 to $16 extra (SeniorList, NCOA)",
             "why": "LifeStation devices detected all 12 falls in AARP's tests. The Amazon listing includes one free month of monitoring.",
             "best": "Households comparing monitored options",
             "watch": "AARP tested LifeStation's Pearl and Sidekick models, not necessarily this Mobile pendant. Fall detection is an add-on, so confirm it is included."},
            {"name": "Apple AirTag (2nd generation), 1 pack", "asin": "B0GJTFXNRX", "badge": "Finds keys, not people",
             "price": "$29 (Apple)",
             "why": "Attach it to keys, a wallet or a bag and find it in the Find My app.",
             "best": "iPhone owners who misplace things",
             "watch": "It is for items. For a person who wanders, use a purpose-built GPS tracker (see our GPS tracker review)."},
            {"name": "Blink Mini 2 indoor camera", "asin": "B0BWWZXWPL", "badge": "Easiest camera with Alexa",
             "price": "about $40 (Security.org, Sep 2026)",
             "why": "A plug-in camera with two-way audio. With an Echo Show it can show the living room on request.",
             "best": "Families who want a quick check-in view",
             "watch": "Blink cloud plans start at $3.99 a month. Check what live view and recording need before you buy."},
            {"name": "WYZE Cam v4", "asin": "B0CJ9Z22L5", "badge": "Lower cost, no subscription",
             "price": "$44.98 (Wyze)",
             "why": "Records to a microSD card in the camera, so there is no required subscription.",
             "best": "Families who want video without a monthly fee",
             "watch": "The microSD card is sold separately."},
            {"name": "eufy Indoor Cam S350 (4K)", "asin": "B0CD7F1M9R", "badge": "Sharpest picture, no subscription",
             "price": "about $129.99 list (PCWorld, Tom's Guide)",
             "why": "Two lenses with zoom, local storage and a physical privacy mode, with no subscription.",
             "best": "A clear view of a room, with privacy controls",
             "watch": "It costs more than the others. Storage needs a microSD card."},
        ],
        "addons_title": "Simple add-ons",
        "addons": [
            {"name": "EZVALO 6-pack rechargeable motion-sensor night lights", "asin": "B0GHQHXV12", "price": "about $55.99",
             "why": "Lights the way to the bathroom at night, no wiring or batteries to replace."},
            {"name": "Sukuos extra-large weekly pill organizer", "asin": "B07V1QCJGF", "price": "about $6.99",
             "why": "Big compartments that are easy to open. For automatic reminders, see our pill dispenser review."},
        ],
        "sections": [
            ("What each option costs every month", [
                "Most of the cost is ongoing, not the device. Rough monthly figures from the manufacturers and from AARP, SafeHome and SeniorList:",
                {"table": (["Option", "Monthly cost"], [
                    ["Apple Watch SE 3", "$0, or about $25 for a cellular plan if it must work without the phone"],
                    ["Lively Mobile2", "From $24.99, plus about $9.99 for fall detection"],
                    ["Bay Alarm Medical", "Base plan plus about $10 for fall detection"],
                    ["LifeStation", "Base plan plus $8 to $16 for fall detection"],
                    ["Blink Mini 2", "Optional cloud plans from $3.99"],
                    ["WYZE Cam v4 and eufy S350", "No required fee (microSD card sold separately)"],
                ])},
            ]),
            ("Before you install a camera", [
                "Talk to your parent first. A camera in a parent's home needs their agreement. Keep cameras out of bedrooms and bathrooms, tell visitors, and think of it as a way to check in, not to watch.",
            ]),
        ],
        "faq": [
            ("Does fall detection work every time?",
             "No. AARP's lab tests found devices detected between 9 and 12 of 12 test falls, and smartwatches detect roughly 60% to 80% of fast falls. Treat it as a backup and keep a help button and regular check-ins."),
            ("Does the Apple Watch turn on fall detection by itself?",
             "Apple says it turns on automatically if the wearer is 55 or older and entered their age when setting up the watch. It is available for people 18 and over, and can be switched on in the Watch app."),
            ("Which option has no monthly fee?",
             "The Apple Watch SE 3 can work with no plan if the iPhone is nearby. The WYZE and eufy cameras need no subscription. Monitored pendants, including Lively, Bay Alarm and LifeStation, all need a monthly plan."),
            ("Should I buy a cheap pendant with automatic fall detection from an unknown brand?",
             "We would not. Several unbranded Amazon pendants promise fall detection and no monthly fee, but none has independent test results that we could find. Choose a known monitoring company."),
        ],
        "related": [("../blog/best-medical-alert-systems.html", "Best medical alert systems"),
                    ("../blog/best-smartwatches-for-seniors.html", "Best smartwatches for seniors"),
                    ("../blog/best-gps-trackers-for-seniors.html", "Best GPS trackers for seniors"),
                    ("../blog/best-pill-organizers-for-seniors.html", "Best pill dispensers for seniors"),
                    ("../blog/medical-alert-no-monthly-fee.html", "Medical alerts with no monthly fee")],
        "sources": [("AARP, best medical alert systems with fall detection (tested)", "https://www.aarp.org/caregiving/home-care/best-medical-alert-systems-with-fall-detection/"),
                    ("Apple Support, Fall Detection on Apple Watch", "https://support.apple.com/en-us/108896"),
                    ("Study: smartwatch app detecting induced falls (PubMed)", "https://pubmed.ncbi.nlm.nih.gov/35311686/"),
                    ("UnaliWear, smartwatch fall detection accuracy", "https://www.unaliwear.com/senior-safety-101/smartwatch-fall-detection-sensor-accuracy/"),
                    ("SafeHome, best fall detection devices", "https://www.safehome.org/medical-alert-systems/best/fall-detection/")],
    },
    {
        "slug": "tech-gifts-for-someone-with-dementia",
        "title": "Tech Gifts for Someone With Dementia | TechForDad",
        "h1": "Tech Gifts for Someone With Dementia",
        "short": "Tech Gifts for Someone With Dementia",
        "desc": "Tech gifts for someone with dementia: a day and date clock, simple TV remote, photo frame and trackers, plus a few comfort items.",
        "card": "A day and date clock, simple remote, photo frame and trackers, plus a few comfort items.",
        "hero": "hero-caregiver-resources.jpg",
        "hero_alt": "A caregiver with residents doing an activity",
        "subtitle": "Simple, familiar devices that support routine and connection. Chosen with the Alzheimer's Association's own gift advice in mind.",
        "intro": [
            "A good gift for someone living with dementia is simple, familiar and easy to use. Avoid anything with many buttons, confusing instructions or fast-paced stimulation. The Alzheimer's Association advises starting with where the person is cognitively, so you choose something they can actually use and enjoy.",
            "The Association's holiday guide suggests a digital clock with large type showing the date and time, framed photographs with names on them, GPS trackers, and a simple phone that stores pictures and contacts. This guide follows that advice and adds a few devices we have checked.",
        ],
        "products": [
            {"name": "American Lifetime dementia clock", "asin": "B019G79V1Q", "badge": "Best-reviewed day clock",
             "price": "about $59.95 (Amazon, checked Sep 2026)",
             "why": "A large display that shows the full day, date and time of day, with custom alarms for reminders. Knowing the day can reduce confusion and repeated questions.",
             "best": "Any stage where routine helps",
             "watch": "Set the alarm labels for your parent's routine before you give it. It plugs in, so place it where it can stay."},
            {"name": "AINFTIME day and date clock", "asin": "B0BKV7TVNL", "badge": "Lower-cost clock",
             "price": "about $29.99 (Amazon, checked Sep 2026)",
             "why": "The same idea at half the price, with a large 7-inch display showing day and date.",
             "best": "A second clock for the kitchen or bedroom",
             "watch": "Fewer reviews than the American Lifetime clock."},
            {"name": "Flipper big-button TV remote", "asin": "B0CR5S1BCN", "badge": "One less thing to get wrong",
             "price": "about $39.95 (Amazon, checked Sep 2026)",
             "why": "Color-coded buttons for power, volume and channels. Our TV remote review ranks it first.",
             "best": "Someone who still enjoys television but cannot use a standard remote",
             "watch": "It works with the TV and cable box only, not streaming apps."},
            {"name": "Skylight Frame, 10-inch", "asin": "B01N7ENHO6", "badge": "Photos of family and friends",
             "price": "about $139 to $160 (retail listings, Sep 2026)",
             "why": "Family emails photos to the frame. Photographs are a gentle way to prompt memories and conversation.",
             "best": "Any stage; add names to the photo files if you can",
             "watch": "Skylight Plus ($39 a year) is optional and adds app and cloud features."},
            {"name": "Amazon Echo Show 8", "asin": "B0DC8ZMR1P", "badge": "Early stage: voice video calls",
             "price": "about $199.99 (Amazon's Aug 2026 price list)",
             "why": "Video calls started by voice can help a person keep in touch without handling a phone.",
             "best": "Early stages, when the person can still speak commands",
             "watch": "It may become confusing later on. It has a camera, so talk about where to place it."},
            {"name": "Apple AirTag (2nd generation), 1 pack", "asin": "B0GJTFXNRX", "badge": "For keys and wallets only",
             "price": "$29 (Apple)",
             "why": "Helps find misplaced keys, a wallet or a handbag.",
             "best": "Early stages, iPhone families",
             "watch": "It is not a safety tracker for a person who wanders. For that, see our GPS tracker review."},
        ],
        "addons_title": "Comfort items (not tech)",
        "addons": [
            {"name": "18-in-1 fidget blanket", "asin": "B09JBJ7C8W", "price": "about $39.81",
             "why": "A lap blanket with zippers, buttons and textures for restless hands. Check with the care team first, and avoid loose small parts."},
        ],
        "sections": [
            ("Trackers for someone who wanders", [
                "The Alzheimer's Association lists GPS trackers such as bracelets, watches and small trackers among its safety suggestions. Our GPS tracker review compares the options built for memory care, and explains how to help a resistant person accept one.",
            ]),
            ("Before you buy", [
                "Talk to the family or the care team. Something helpful in the early stage can be confusing later on, and the best gift is often your time: a regular visit, a walk or a shared lunch.",
            ]),
        ],
        "faq": [
            ("What is a dementia clock?",
             "It is a digital clock that spells out the full day of the week, the date and the time of day (morning, afternoon, evening, night) in large type. Many have custom alarms for medicines and routine."),
            ("Is an AirTag good for someone with dementia?",
             "Only for finding items such as keys or a wallet. It is not designed for tracking a person and depends on the person carrying it. Use a purpose-built GPS device for someone who wanders."),
            ("Should we buy a smart speaker for someone with dementia?",
             "It can help in the early stage, since video calls and reminders are voice-controlled. It may confuse later on, so check with the family or care team."),
            ("What about music players?",
             "Music can be a powerful comfort. We have not yet found a simple, one-touch player with strong independent reviews, so we are not recommending one."),
        ],
        "related": [("../blog/best-gps-trackers-for-seniors.html", "Best GPS trackers for seniors"),
                    ("../blog/best-tv-remotes-for-seniors.html", "Best TV remotes for seniors"),
                    ("../blog/best-cell-phones-for-seniors.html", "Best cell phones for seniors"),
                    ("../blog/best-medical-alert-systems.html", "Best medical alert systems")],
        "sources": [("Alzheimer's Association, gift guide for caregivers and people living with dementia", "https://www.alz.org/help-support/caregiving/holidays/gift-guide"),
                    ("Alzheimer Society of Canada, gift ideas for people with dementia", "https://alzheimer.ca/en/whats-happening/news/gift-ideas-people-dementia")],
    },
    {
        "slug": "tech-gifts-for-seniors-under-50",
        "title": "Tech Gifts for Seniors Under $50 (2026) | TechForDad",
        "h1": "Tech Gifts for Seniors Under $50",
        "short": "Tech Gifts Under $50",
        "desc": "Useful tech gifts for seniors under $50: a tracker, day clock, big-button remote, night lights, magnifier and a camera, with real prices.",
        "card": "A tracker, day clock, big-button remote, night lights, magnifier and an indoor camera, all under $50.",
        "hero": "hero-bluetooth-tracker.jpg",
        "hero_alt": "An AirTag floating above an open hand",
        "subtitle": "Every price here was $50 or less when we checked, and each one solves a real problem. Prices move, so check before you buy.",
        "intro": [
            "You do not need to spend much on a tech gift that gets used. The picks below were $50 or less when we checked, and each has a clear daily purpose.",
            "Prices below are what we saw on September 29, 2026 and will change. Amazon raised many device prices in August, so a few items sit close to the $50 line.",
        ],
        "products": [
            {"name": "Apple AirTag (2nd generation), 1 pack", "asin": "B0GJTFXNRX", "badge": "Finds keys and wallets",
             "price": "$29 (Apple)", "why": "Attach it to keys or a wallet and find it in the Find My app.",
             "best": "iPhone owners", "watch": "Works with iPhone and iPad only."},
            {"name": "Chipolo ONE Point (Android)", "asin": "B0C4W2VGTX", "badge": "Tracker for Android",
             "price": "about $28 (Chipolo)", "why": "The same idea for Android phones, using Google's Find My Device network.",
             "best": "Android owners", "watch": "Check which phones it works with before you buy; iPhone owners are usually better served by the AirTag."},
            {"name": "AINFTIME day and date clock", "asin": "B0BKV7TVNL", "badge": "Knows what day it is",
             "price": "about $29.99", "why": "A large display that spells out the day and date, useful for anyone who loses track of days.",
             "best": "A parent who often asks what day it is", "watch": "Plugs in."},
            {"name": "Flipper big-button TV remote", "asin": "B0CR5S1BCN", "badge": "Simple TV control",
             "price": "about $39.95", "why": "Large color-coded buttons for power, volume and channels.",
             "best": "A parent who struggles with a standard remote", "watch": "TV and cable only; no streaming apps."},
            {"name": "GE BigEZ OneTouch big-button remote", "asin": "B0FWL14KM6", "badge": "Lowest-cost big-button remote",
             "price": "about $12.25 (Amazon)", "why": "Large backlit buttons and one-touch setup for Samsung, LG, Vizio, Sony and Roku TVs. It also ranks second in our TV remote review.",
             "best": "A parent who needs bigger buttons on a budget", "watch": "It controls TVs with a slim set of buttons, so check it covers your parent's TV."},
            {"name": "Fire TV Stick HD", "asin": "B0DJGDC3BD", "badge": "Streaming with a voice remote",
             "price": "about $40 (Amazon's Aug 2026 price list)", "why": "Plugs into the TV and lets your parent say what they want to watch.",
             "best": "Parents with a TV that has a free HDMI port", "watch": "Someone needs to set it up first."},
            {"name": "Blink Mini 2 indoor camera", "asin": "B0BWWZXWPL", "badge": "Easy check-in camera",
             "price": "about $40", "why": "Plug-in camera with two-way audio; easy to use with Alexa.",
             "best": "Families who want a quick check-in", "watch": "Cloud plans start at $3.99 a month, and it works best with an agreed placement. Talk to your parent first."},
            {"name": "WYZE Cam v4", "asin": "B0CJ9Z22L5", "badge": "Camera without a subscription",
             "price": "$44.98 (Wyze)", "why": "Records to a microSD card, so no required fee.",
             "best": "A no-subscription camera", "watch": "The microSD card is sold separately."},
            {"name": "AMIR 6-pack motion-sensor stair lights", "asin": "B0B8MR5X6Y", "badge": "Safer night walks",
             "price": "about $15.99", "why": "Lights the hallway, bathroom and kitchen automatically, battery powered.",
             "best": "Any parent who gets up at night", "watch": "Batteries need replacing eventually."},
            {"name": "Nazano lighted magnifier", "asin": "B08PP4RJ5J", "badge": "Read small print",
             "price": "about $14.89", "why": "12 LEDs for reading labels, menus and small print.",
             "best": "Pill labels and recipes", "watch": "Uses AA batteries."},
        ],
        "addons_title": "Small extras (not tech)",
        "addons": [
            {"name": "Joywell armchair caddy", "asin": "B07GDBWNXW", "price": "about $9.98", "why": "Keeps remote, phone and glasses within reach."},
            {"name": "Sukuos extra-large weekly pill organizer", "asin": "B07V1QCJGF", "price": "about $6.99", "why": "Large compartments that are easy to open."},
            {"name": "Bicycle jumbo-index playing cards, 2 pack", "asin": "B000BUUTJ6", "price": "about $5.63", "why": "Large-print cards for a card game."},
        ],
        "sections": [],
        "faq": [
            ("What is the best tech gift for a senior under $50?",
             "For most families, a day and date clock or a big-button remote solves a daily problem for under $40. If your parent uses an iPhone and loses things, an AirTag at $29 is popular."),
            ("Are cameras a good gift?",
             "Only with your parent's agreement. Keep them out of bedrooms and bathrooms and treat them as a check-in, not surveillance."),
            ("Why are some prices close to $50?",
             "Amazon raised prices on many devices in August 2026, and prices change often. Check the current price on the page before you buy."),
            ("Do any of these need a subscription?",
             "None is required. Blink's cloud plans are optional, and the WYZE camera records to a microSD card at no fee."),
        ],
        "related": [("../blog/best-tv-remotes-for-seniors.html", "Best TV remotes for seniors"),
                    ("../blog/best-gps-trackers-for-seniors.html", "Best GPS trackers for seniors"),
                    ("../blog/best-pill-organizers-for-seniors.html", "Best pill dispensers for seniors")],
        "sources": [("NBC Select, best gifts under $50", "https://www.nbcnews.com/select/shopping/best-gifts-under-50-rcna242155")],
    },
    {
        "slug": "gifts-for-elderly-parents-who-have-everything",
        "title": "Gifts for Elderly Parents Who Have Everything | TechForDad",
        "h1": "Gifts for Elderly Parents Who Have Everything",
        "short": "Gifts for Parents Who Have Everything",
        "desc": "Gift ideas for elderly parents who have everything: a photo frame, smart mug, indoor garden, bird feeder camera and a cozy heated throw.",
        "card": "A photo frame, smart mug, indoor garden, bird feeder camera and a cozy heated throw.",
        "hero": "hero-senior-phone-plans.jpg",
        "hero_alt": "A senior couple looking at a smartphone together",
        "subtitle": "When a parent says they need nothing, the best gifts add comfort, connection or a small daily pleasure. Prices checked September 29, 2026.",
        "intro": [
            "\"Who has everything\" is one of the most common ways people search for gifts for older parents. The answer is usually not another gadget. It is something that keeps family close, adds a small daily pleasure, or makes a familiar routine nicer.",
            "The picks below are still tech-flavored, since that is what we know best, but each one earns its place by being used every day.",
        ],
        "products": [
            {"name": "Aura Carver Mat digital frame (10-inch)", "asin": "B0BG3F79LF", "badge": "Family photos, always fresh",
             "price": "about $179.99 (Aura, checked Oct 2026)",
             "why": "Family members send photos from a phone app and the frame updates itself. Amazon lists free unlimited cloud storage and no subscription.",
             "best": "Parents with lots of grandchildren far away",
             "watch": "Each family member adds photos by app, so it suits families who share photos already."},
            {"name": "Ember Mug 2 (10 oz)", "asin": "B07NQPYGYD", "badge": "Coffee that stays hot",
             "price": "about $89.99 (Amazon, checked Sep 2026)",
             "why": "Holds a chosen temperature, so the last sip is as warm as the first.",
             "best": "Slow coffee or tea drinkers",
             "watch": "Hand wash only, and about 90 minutes of heat off the coaster. Ember's own site now sells the newer Mug 3 at $149.95."},
            {"name": "Click & Grow indoor herb garden", "asin": "B01MRVMKQH", "badge": "Fresh herbs on the counter",
             "price": "about $101.60 (Amazon, checked Sep 2026)",
             "why": "Self-watering and lit by built-in LEDs, so there is no gardening skill required.",
             "best": "Cooks who like fresh basil or mint",
             "watch": "Plant pods are a recurring purchase."},
            {"name": "Birdbuddy Pro smart bird feeder", "asin": "B0DHY6CQBC", "badge": "Bird watching on a phone",
             "price": "about $279.99 (regular price; frequently discounted, checked Oct 2026)",
             "why": "A feeder with a camera that sends photos of visiting birds to a phone, with species identification.",
             "best": "Parents who watch birds from the window",
             "watch": "It needs a 2.4 GHz Wi-Fi network. A premium membership is optional, around $60 to $70 a year. The pole is not included, and the listing has fewer reviews than most items here."},
        ],
        "addons_title": "Comfort add-ons",
        "addons": [
            {"name": "Sunbeam Royal Ultra Fleece heated throw", "asin": "B008BF2MFM", "price": "about $69.99",
             "why": "Auto shut-off and four heat settings. Check the current CPSC recall list before you buy any heated blanket."},
            {"name": "Bombas Gripper slippers (women's)", "asin": "B0GQLQL62V", "price": "about $55",
             "why": "Grip soles for tile and hardwood floors. No slipper can guarantee against a fall."},
        ],
        "sections": [
            ("Gifts that are not in a box", [
                "For a parent who truly has everything, time can be the best gift: a standing weekly call, help sorting old photos, or an afternoon set aside to fix their phone and tablet.",
            ]),
        ],
        "faq": [
            ("What do you buy an elderly parent who has everything?",
             "Something that adds connection or a small daily pleasure: a photo frame that family keeps full, a mug that keeps coffee warm, or fresh herbs on the counter."),
            ("Are photo frames really used?",
             "They are used when family sends photos regularly. Choose a frame that lets several relatives add pictures, and set it up before you give it."),
            ("Do these gifts have subscriptions?",
             "The Aura frame lists no subscription. Birdbuddy's premium membership is optional at $39 a year."),
            ("Is a heated blanket safe for an older adult?",
             "Look for auto shut-off and check the Consumer Product Safety Commission recall list. Older adults with reduced feeling in their skin should ask their doctor first."),
        ],
        "related": [("../blog/best-smart-home-devices-for-seniors.html", "Best smart home devices for seniors"),
                    ("../blog/best-e-readers-for-seniors.html", "Best e-readers for seniors"),
                    ("../blog/best-tablets-for-seniors.html", "Best tablets for seniors")],
        "sources": [("NCOA, best gifts for seniors", "https://www.ncoa.org/product-resources/gift-guides/best-gifts-for-seniors/"),
                    ("CPSC recalls", "https://www.cpsc.gov/Recalls")],
    },
]

HUB_TITLE = "Gift Guides for Elderly Parents and Seniors | TechForDad"
HUB_DESC = "Gift guides for elderly parents and seniors: tech gifts, safety tech for parents who live alone, dementia-friendly gifts, gifts under $50 and more."

# ------------------------------------------------------------- templates
HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <link rel="icon" type="image/svg+xml" href="../favicon.svg"/>
  <link rel="icon" type="image/x-icon" href="../favicon.ico"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title}</title>
  <meta name="description" content="{desc}"/>
  <link rel="canonical" href="{url}"/>

  <meta property="og:type" content="article"/>
  <meta property="og:site_name" content="TechForDad"/>
  <meta property="og:title" content="{og_title}"/>
  <meta property="og:description" content="{desc}"/>
  <meta property="og:url" content="{url}"/>
  <meta property="og:image" content="{site}/images/heroes/{hero}"/>
  <meta name="twitter:card" content="summary_large_image"/>
  <meta name="twitter:title" content="{og_title}"/>
  <meta name="twitter:description" content="{desc}"/>
  <meta name="twitter:image" content="{site}/images/heroes/{hero}"/>
  <meta name="google-adsense-account" content="ca-pub-6309879983967574"/>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6309879983967574" crossorigin="anonymous"></script>

  <link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin/>
  <link rel="preload" href="/fonts/playfair-display.woff2" as="font" type="font/woff2" crossorigin/>
  <link rel="stylesheet" href="../css/style.css?v=20260930"/>

{jsonld}
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-YW35RMEFHV"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-YW35RMEFHV');</script>
</head>
<body>
<a class="skip-link" href="#main">Skip to main content</a>

<header>
  <div class="header-inner">
    <a href="../index.html" class="logo"><div class="logo-icon">★</div>TechForDad</a>
    <nav id="site-nav">
      <a href="../blog/best-medical-alert-systems.html">Alert Systems</a>
      <a href="../blog/best-cell-phones-for-seniors.html">Phones</a>
      <a href="../blog/index.html">All Reviews</a>
      <a href="../guides/index.html">Guides</a>
      <a href="../about.html">About</a>
      <a href="../index.html#newsletter" class="nav-cta">Free Guide</a>
    </nav>
    <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</header>

<main id="main">
"""

FOOT = """
<section class="newsletter" id="newsletter">
  <div class="newsletter-inner">
    <h2>Free Caregiver Tech Checklist</h2>
    <p>Get our free guide: <strong>"7 Tech Essentials Every Senior Home Should Have"</strong></p>
    <form class="email-form" action="https://us2.list-manage.com/subscribe/post?u=4d4642fb82dc99daa1b66f684&amp;id=8cf3d53e8d" method="post" target="_blank">
      <input type="email" name="EMAIL" placeholder="Enter your email address" required/>
      <button type="submit">Get Free Guide</button>
      <div style="position:absolute;left:-5000px;" aria-hidden="true">
        <input type="text" name="b_4d4642fb82dc99daa1b66f684_8cf3d53e8d" tabindex="-1" value=""/>
      </div>
    </form>
    <p class="email-note">No spam. Unsubscribe anytime.</p>
  </div>
</section>

<div class="author-box">
  <div class="author-box-avatar">★</div>
  <div class="author-box-content">
    <p class="author-box-name">Written by TechForDad: a project by EasyTechVancouver</p>
    <p class="author-box-bio">TechForDad is published by EasyTech Vancouver. Our guides are based on manufacturer specifications, published reviews and current prices, which we recheck every month. We do not hands-on test products, and no company pays for its ranking. See <a href="../how-we-review.html">how we review products</a>.</p>
  </div>
</div>

</main>

<footer>
  <div class="footer-inner">
    <div class="footer-grid">
      <div>
        <div class="footer-logo">★ TechForDad</div>
        <p class="footer-desc">Helping families choose the right technology for aging parents since 2024.</p>
        <p class="footer-affiliate">Affiliate Disclosure: We may earn a commission when you click links on this site. As an Amazon Associate I earn from qualifying purchases.</p>
      </div>
      <div class="footer-col">
        <h3>Gift Guides</h3>
        <ul>
{footer_links}
        </ul>
      </div>
      <div class="footer-col">
        <h3>Reviews</h3>
        <ul>
          <li><a href="../blog/best-medical-alert-systems.html">Medical Alert Systems</a></li>
          <li><a href="../blog/best-smartwatches-for-seniors.html">Smartwatches</a></li>
          <li><a href="../blog/best-gps-trackers-for-seniors.html">GPS Trackers</a></li>
          <li><a href="../blog/index.html">All Reviews</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h3>TechForDad</h3>
        <ul>
          <li><a href="../about.html">About</a></li>
          <li><a href="../guides/index.html">Guides</a></li>
          <li><a href="../contact.html">Contact</a></li>
          <li><a href="../privacy-policy.html">Privacy Policy</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span id="year">2026</span> TechForDad. All rights reserved.</span>
    </div>
  </div>
</footer>

<script src="../js/main.js" defer></script>
</body>
</html>
"""


def md(text):
    """Escape, then turn **bold** into <strong>."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e(text))


def jsonld(headline, desc, url, crumbs, faq, hero):
    article = {"@context": "https://schema.org", "@type": "Article", "headline": headline, "description": desc,
               "image": f"{SITE}/images/heroes/{hero}",
               "author": {"@type": "Organization", "name": "TechForDad"},
               "publisher": {"@type": "Organization", "name": "TechForDad", "url": SITE,
                             "parentOrganization": {"@type": "Organization", "name": "EasyTech Vancouver", "url": "https://easytechvancouver.ca/",
                                                    "sameAs": ["https://www.facebook.com/profile.php?id=61587106324816", "https://www.instagram.com/easytechvancouver", "https://www.linkedin.com/company/easytech-digital-solutions/", "https://www.google.com/maps/place/Easy+Tech/@49.1768374,-122.9222895"]}},
               "datePublished": PUBLISHED, "dateModified": MODIFIED}
    bread = {"@context": "https://schema.org", "@type": "BreadcrumbList",
             "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)]}
    blocks = [article, bread]
    if faq:
        blocks.append({"@context": "https://schema.org", "@type": "FAQPage",
                       "mainEntity": [{"@type": "Question", "name": q,
                                       "acceptedAnswer": {"@type": "Answer", "text": stamp(a)}} for q, a in faq]})
    return "\n".join('  <script type="application/ld+json">\n' + json.dumps(b, indent=2, ensure_ascii=False) + "\n  </script>\n" for b in blocks)


def product_card(n, p):
    top = " top-pick" if n == 1 else ""
    gold = " gold" if n == 1 else ""
    rows = [("Price", p["price"]), ("Best for", p["best"]), ("Watch out for", p["watch"])]
    specs = "\n".join(
        '          <div class="spec' + (" spec-wide" if l == "Watch out for" else "") + f'"><span class="spec-label">{l}</span><span class="spec-val">{e(v)}</span></div>'
        for l, v in rows)
    return f"""    <div class="product-card{top}">
      <div class="product-header">
        <div class="product-rank{gold}">{n}</div>
        <div class="product-title">
          <h3>{e(p['name'])}</h3>
          <span class="product-badge-small">{e(p['badge'])}</span>
        </div>
      </div>
      <div class="product-body">
        <p>{e(p['why'])}</p>
        <div class="product-specs">
{specs}
        </div>
        <a href="{amazon(p['asin'])}" target="_blank" rel="sponsored noopener" class="btn-check-price">Check Price on Amazon →</a>
      </div>
    </div>
"""


def guide_page(g):
    url = f"{SITE}/gift-guides/{g['slug']}.html"
    faq = g["faq"]
    others = [x for x in GUIDES if x is not g]
    toc = ['<li><a href="#picks">The picks</a></li>']
    for title, _ in g.get("pre_sections", []):
        toc.insert(0, f'<li><a href="#{re.sub(r"[^a-z]+", "-", title.lower()).strip("-")}">{e(title)}</a></li>')
    if g["addons"]:
        toc.append('<li><a href="#addons">' + e(g["addons_title"]) + "</a></li>")
    for title, _ in g["sections"]:
        toc.append(f'<li><a href="#{re.sub(r"[^a-z]+", "-", title.lower()).strip("-")}">{e(title)}</a></li>')
    toc += ['<li><a href="#faq">Frequently asked questions</a></li>', '<li><a href="#related">Related reviews</a></li>']

    def section(title, paras):
        sid = re.sub(r"[^a-z]+", "-", title.lower()).strip("-")
        chunks = []
        for p in paras:
            if isinstance(p, dict):
                heads, rows = p["table"]
                th = "".join(f"<th>{e(h)}</th>" for h in heads)
                tr = "\n".join("          <tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in rows)
                chunks.append('    <div class="comparison-table-wrap">\n      <table class="comparison-table">\n        <thead><tr>'
                              + th + "</tr></thead>\n        <tbody>\n" + tr + "\n        </tbody>\n      </table>\n    </div>")
            else:
                chunks.append(f"    <p>{md(p)}</p>")
        return f'    <h2 id="{sid}">{e(title)}</h2>\n\n' + "\n".join(chunks) + "\n"

    parts = [HEAD.format(title=e(g["title"]), desc=e(g["desc"]), url=url, og_title=e(g["h1"]), site=SITE, hero=g["hero"],
                         jsonld=jsonld(g["h1"], g["desc"], url,
                                       [("Home", SITE + "/"), ("Gift Guides", SITE + "/gift-guides/index.html"), (g["short"], url)], faq, g["hero"]))]
    parts.append(f"""
<div class="breadcrumb">
  <div class="breadcrumb-inner">
    <a href="../index.html">Home</a> <span>›</span>
    <a href="index.html">Gift Guides</a> <span>›</span>
    {e(g['short'])}
  </div>
</div>

<div class="article-hero">
  <img src="../images/heroes/{g['hero']}" alt="{e(g["hero_alt"])}" width="860" height="480" fetchpriority="high">
  <div class="article-hero-inner">
    <span class="card-tag">GIFT GUIDE · UPDATED {UPDATED_LABEL.upper()}</span>
    <h1>{e(g['h1'])}</h1>
    <p class="article-subtitle">{e(g['subtitle'])}</p>
    <div class="article-meta">
      <span>By TechForDad</span>
      <span>Updated {UPDATED_LABEL}</span>
      <span>Prices checked {PRICE_DATE}</span>
    </div>
  </div>
</div>

<div class="article-disclaimer">
<strong>Affiliate Disclosure:</strong> As an Amazon Associate I earn from qualifying purchases, at no extra cost to you. Links here use a tracking ID that shows us how this guide performs; our picks are never influenced by commission. Prices are approximate (checked {PRICE_DATE}); the price on Amazon when you buy is the price you pay. <a href="../affiliate-disclosure.html" style="text-decoration:underline">Full disclosure</a>.
</div>

<div class="article-body">
  <div class="article-inner">

    <div class="toc-box">
      <strong>Table of Contents</strong>
      <ul>
        {chr(10).join('        ' + t for t in toc).strip()}
      </ul>
    </div>
""")
    for para in g["intro"]:
        parts.append(f'    <p>{md(para)}</p>\n')
    for title, paras in g.get("pre_sections", []):
        parts.append(section(title, paras))
    parts.append('    <h2 id="picks">The picks</h2>\n')
    for i, p in enumerate(g["products"], 1):
        parts.append(product_card(i, p))
    if g["addons"]:
        parts.append(f'    <h2 id="addons">{e(g["addons_title"])}</h2>\n\n    <ul>\n')
        for a in g["addons"]:
            parts.append(f'      <li><strong>{e(a["name"])}</strong> ({e(a["price"])}): {e(a["why"])} <a href="{amazon(a["asin"])}" target="_blank" rel="sponsored noopener">Check price on Amazon →</a></li>\n')
        parts.append("    </ul>\n")
    for title, paras in g["sections"]:
        parts.append(section(title, paras))
    parts.append('    <h2 id="faq">Frequently asked questions</h2>\n\n')
    for q, a in faq:
        parts.append(f"    <h3>{e(q)}</h3>\n    <p>{e(a)}</p>\n\n")
    parts.append('    <h2 id="related">Related reviews</h2>\n\n    <ul>\n')
    for href, label in g["related"]:
        parts.append(f'      <li><a href="{href}">{e(label)}</a></li>\n')
    parts.append("    </ul>\n\n")
    parts.append('    <div class="gift-more">\n      <strong>More gift guides</strong>\n      <ul>\n')
    parts.append('        <li><a href="index.html">All gift guides</a></li>\n')
    for o in others:
        parts.append(f'        <li><a href="{o["slug"]}.html">{e(o["short"])}</a></li>\n')
    parts.append("      </ul>\n    </div>\n\n")
    if g["sources"]:
        parts.append('    <p class="gift-sources"><strong>Sources:</strong> ' + "; ".join(
            f'<a href="{u}" target="_blank" rel="noopener noreferrer">{e(l)}</a>' for l, u in g["sources"]) + ".</p>\n\n")
    parts.append("  </div>\n</div>\n")
    footer_links = "\n".join(f'          <li><a href="{x["slug"]}.html">{e(x["short"])}</a></li>' for x in GUIDES)
    parts.append(FOOT.format(footer_links=footer_links))
    return add_bounty_blocks(g["slug"], "".join(parts))


# The Amazon bounty / membership offers (Prime, Audible, Music Unlimited) live in scripts/gift_guide_bounty_blocks.json as exact
# HTML, because they are written by hand per guide (which memberships fit which gifts). They go in front of three headings.
# Without this step a regeneration silently deletes them (it did on 2026-10-05); tests/test_generated.py now fails if the
# generator's output differs from the committed pages.
BOUNTY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gift_guide_bounty_blocks.json")
BOUNTY_HEADINGS = {"before_picks": '<h2 id="picks">', "before_faq": '<h2 id="faq">', "before_related": '<h2 id="related">'}


def add_bounty_blocks(slug, text):
    import json
    with open(BOUNTY_FILE, encoding="utf-8") as f:
        blocks = json.load(f).get(slug, {})
    for key, heading in BOUNTY_HEADINGS.items():
        if key in blocks:
            marker = "    " + heading
            assert text.count(marker) == 1, f"{slug}: cannot place {key}: {marker!r} found {text.count(marker)} times"
            text = text.replace(marker, blocks[key] + heading, 1)
    for old, new in blocks.get("patches", []):
        assert text.count(old) == 1, f"{slug}: bounty patch does not apply: {old[:60]!r}"
        text = text.replace(old, new, 1)
    return text


def hub_page():
    url = f"{SITE}/gift-guides/index.html"
    crumbs = [("Home", SITE + "/"), ("Gift Guides", url)]
    cards = []
    for g in GUIDES:
        cards.append(f"""      <div class="card">
        <div class="card-img card-photo"><img src="../images/cards/{g['hero'].rsplit('.', 1)[0]}.webp" alt="" width="400" height="180" loading="lazy"></div>
        <div class="card-body">
          <span class="card-tag">Gift Guide</span>
          <h2>{e(g['h1'])}</h2>
          <p>{e(g['card'])}</p>
          <a href="{g['slug']}.html" class="card-link" aria-label="Read the guide: {e(g['h1'])}">Read the guide</a>
        </div>
      </div>
""")
    footer_links = "\n".join(f'          <li><a href="{x["slug"]}.html">{e(x["short"])}</a></li>' for x in GUIDES)
    page = HEAD.format(title=e(HUB_TITLE), desc=e(HUB_DESC), url=url, og_title="Gift Guides for Elderly Parents and Seniors",
                       site=SITE, hero="hero-senior-gifts.jpg", jsonld=jsonld("Gift Guides for Elderly Parents and Seniors", HUB_DESC, url, crumbs, [], "hero-senior-gifts.jpg"))
    page += f"""
<div class="article-hero">
  <img src="../images/heroes/hero-senior-gifts.jpg" alt="Wrapped gifts with gold ribbon on kraft paper" width="860" height="480" fetchpriority="high">
  <div class="article-hero-inner">
    <span class="card-tag">GIFT GUIDES</span>
    <h1>Gift Guides for Elderly Parents and Seniors</h1>
    <p class="article-subtitle">Tech gifts that get used, safety devices for parents who live alone, gifts for someone with dementia, and ideas under $50. Prices in these guides were checked on {PRICE_DATE}.</p>
    <div class="article-meta">
      <span>By TechForDad</span>
      <span>Updated {UPDATED_LABEL}</span>
    </div>
  </div>
</div>

<div class="article-disclaimer">
<strong>Affiliate Disclosure:</strong> As an Amazon Associate I earn from qualifying purchases, at no extra cost to you. Links in the gift guides use a tracking ID that shows us how each guide performs; our picks are never influenced by commission. Prices in our guides are approximate (checked {PRICE_DATE}). <a href="../affiliate-disclosure.html" style="text-decoration:underline">Full disclosure</a>.
</div>

<div class="article-body">
  <div class="article-inner" style="max-width:1140px">

    <p>Older parents are hard to shop for. They often have what they need, and a gift that adds a new device to manage can end up in a drawer. These guides focus on gifts that solve a real problem, and on setting them up so they get used.</p>

    <div class="cards-grid" style="margin:28px 0">
{''.join(cards)}    </div>

    <h2>How we choose</h2>

    <ul>
      <li>We favor devices with one clear daily benefit and a low learning curve.</li>
      <li>We look at each product's Amazon listing, and whether it is still on sale, before we recommend it.</li>
      <li>We explain monthly costs, subscriptions and limits, such as how often fall detection actually works.</li>
      <li>A few comfort items appear at the end of some guides, clearly marked as not tech.</li>
      <li>We do not rank products by commission.</li>
    </ul>

    <h2>Looking for a full review?</h2>

    <ul>
      <li><a href="../blog/best-medical-alert-systems.html">Best medical alert systems</a></li>
      <li><a href="../blog/best-smartwatches-for-seniors.html">Best smartwatches for seniors</a></li>
      <li><a href="../blog/best-gps-trackers-for-seniors.html">Best GPS trackers for seniors</a></li>
      <li><a href="../blog/best-tablets-for-seniors.html">Best tablets for seniors</a></li>
      <li><a href="../blog/index.html">All reviews</a></li>
    </ul>

  </div>
</div>
"""
    page += FOOT.format(footer_links=footer_links)
    return page


# Price chips on the homepage tiles. Each is the lowest price verified in that guide; update them
# with the guide's prices, or say something price-free.
CHIPS = {
    "tech-gifts-for-elderly-parents": "From about $40",
    "safety-tech-for-elderly-parents-who-live-alone": "From $29",
    "tech-gifts-for-someone-with-dementia": "From about $30",
    "tech-gifts-for-seniors-under-50": "All under $50",
    "gifts-for-elderly-parents-who-have-everything": "From about $70",
}
HOME_SECTION_RE = re.compile(r'<section class="gift-feature" id="gift-guides">.*?</section>', re.S)


def home_block():
    tiles = []
    for g in GUIDES:
        tiles.append(f"""          <li><a class="gift-tile" href="gift-guides/{g['slug']}.html">
            <span class="gift-tile-img"><img src="images/cards/{g['hero'].rsplit('.', 1)[0]}.webp" alt="" width="400" height="180" loading="lazy"></span>
            <span class="gift-tile-body"><span class="gift-tile-title">{e(g['short'])}</span><span class="gift-chip">{e(CHIPS[g['slug']])}</span></span>
          </a></li>""")
    return f"""<section class="gift-feature" id="gift-guides">
  <div class="section-inner">
    <div class="gift-feature-inner">
      <div class="gift-feature-text">
        <span class="gift-badge">Gift Guides</span>
        <h2>Tech gifts your parents will actually use</h2>
        <p class="gift-feature-lead">Five guides with prices checked on Amazon: everyday tech, safety devices for parents who live alone, gifts for someone with dementia, and ideas under $50.</p>
        <p class="gift-season-note">Gift season is here. Prices are checked monthly.</p>
      </div>
      <ul class="gift-tiles">
{chr(10).join(tiles)}
      </ul>
      <div class="gift-feature-actions">
        <a href="gift-guides/index.html" class="btn-primary">Browse all gift guides</a>
      </div>
    </div>
  </div>
</section>"""


def update_homepage():
    path = os.path.join(ROOT, "index.html")
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read().replace(chr(13) + chr(10), chr(10))  # Windows checkouts use CRLF
    new, n = HOME_SECTION_RE.subn(lambda _m: home_block(), text, count=1)
    if n and new != text:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    return bool(n)


GIFT_LINKS = {
    "best-tablets-for-seniors.html": "tech-gifts-for-elderly-parents",
    "how-to-set-up-ipad-for-elderly-parent.html": "tech-gifts-for-elderly-parents",
    "best-alexa-devices-for-seniors.html": "tech-gifts-for-elderly-parents",
    "best-smart-home-devices-for-seniors.html": "tech-gifts-for-elderly-parents",
    "best-cell-phones-for-seniors.html": "tech-gifts-for-elderly-parents",
    "jitterbug-vs-iphone-for-seniors.html": "tech-gifts-for-elderly-parents",
    "best-e-readers-for-seniors.html": "tech-gifts-for-elderly-parents",
    "best-smartwatches-for-seniors.html": "safety-tech-for-elderly-parents-who-live-alone",
    "best-medical-alert-systems.html": "safety-tech-for-elderly-parents-who-live-alone",
    "medical-alert-no-monthly-fee.html": "safety-tech-for-elderly-parents-who-live-alone",
    "life-alert-vs-medical-guardian.html": "safety-tech-for-elderly-parents-who-live-alone",
    "best-gps-trackers-for-seniors.html": "tech-gifts-for-someone-with-dementia",
    "best-tv-remotes-for-seniors.html": "tech-gifts-for-seniors-under-50",
    "best-pill-organizers-for-seniors.html": "tech-gifts-for-seniors-under-50",
}
LINK_RE = re.compile(r"[ \t]*<!-- gift-links -->.*?<!-- /gift-links -->\n?", re.S)
RELATED_RE = re.compile(r"[ \t]*<!-- related -->")  # the box sits in the article, just before "Keep Reading", not inside the author box


def add_review_links():
    by_slug = {g["slug"]: g for g in GUIDES}
    changed = 0
    for fname, slug in GIFT_LINKS.items():
        path = os.path.join(ROOT, "blog", fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read().replace(chr(13) + chr(10), chr(10))  # Windows checkouts use CRLF
        text = LINK_RE.sub("", text)
        g = by_slug[slug]
        block = (f'    <!-- gift-links -->\n    <div class="gift-more">\n      <strong>See more gift ideas</strong>\n'
                 f'      <p><a href="../gift-guides/{slug}.html">{e(g["h1"])}</a>, or browse <a href="../gift-guides/index.html">all gift guides</a>.</p>\n'
                 f'    </div>\n    <!-- /gift-links -->\n')
        new, n = RELATED_RE.subn(lambda m: block + m.group(0), text, count=1)
        if n and new != text:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new)
            changed += 1
    return changed


def add_sitemap():
    path = os.path.join(ROOT, "sitemap.xml")
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read().replace(chr(13) + chr(10), chr(10))  # Windows checkouts use CRLF
    urls = [f"{SITE}/gift-guides/index.html"] + [f"{SITE}/gift-guides/{g['slug']}.html" for g in GUIDES]
    added = 0
    for u in urls:
        if u in text:
            continue
        entry = f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{PUBLISHED}</lastmod>\n  </url>\n"
        text = text.replace("</urlset>", entry + "</urlset>")
        added += 1
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return added


def check_lengths():
    for t, d, name in [(HUB_TITLE, HUB_DESC, "hub")] + [(g["title"], g["desc"], g["slug"]) for g in GUIDES]:
        assert len(t) <= 60, f"{name}: title is {len(t)} chars"
        assert len(d) <= 160, f"{name}: description is {len(d)} chars"


def apply_checked_date(iso):
    """Set every date shown on the pages from one 'prices checked' date (YYYY-MM-DD)."""
    import datetime
    global PRICE_DATE, UPDATED_LABEL, MODIFIED, SHORT_LABEL
    d = datetime.date.fromisoformat(iso)
    SHORT_LABEL = d.strftime("%b %Y")
    PRICE_DATE = f"{d.strftime('%B')} {d.day}, {d.year}"
    UPDATED_LABEL = f"{d.strftime('%B')} {d.year}"
    MODIFIED = d.isoformat()


def check():
    """Dry run: regenerate in a temporary copy of the site and report any file that differs from the real one.
    Exits 1 if the generator no longer reproduces the committed pages (so a regeneration would change or delete something)."""
    import filecmp
    import shutil
    import subprocess
    import sys
    import tempfile

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with tempfile.TemporaryDirectory() as tmp:
        copy = os.path.join(tmp, "site")
        shutil.copytree(root, copy, ignore=shutil.ignore_patterns(".git", ".venv", "node_modules", "__pycache__", "*.jpg", "*.jpeg", "*.png", "*.webp", "*.svg", "*.woff2"))
        run = subprocess.run([sys.executable, os.path.join(copy, "scripts", "build_gift_guides.py")], capture_output=True, text=True)
        if run.returncode:
            print(run.stderr or run.stdout)
            return 1
        stale = []
        for dirpath, dirs, files in os.walk(copy):
            dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__")]
            for name in files:
                if not name.endswith((".html", ".xml")):
                    continue
                new_path = os.path.join(dirpath, name)
                rel = os.path.relpath(new_path, copy)
                old_path = os.path.join(root, rel)
                if not os.path.exists(old_path) or not filecmp.cmp(new_path, old_path, shallow=False):
                    stale.append(rel)
        if stale:
            print("build_gift_guides.py would change these files (the generator is out of sync with the pages):\n  " + "\n  ".join(sorted(stale)[:20]))
            return 1
    print("gift guides OK: the generator reproduces the committed pages")
    return 0


def main():
    import sys
    if "--check" in sys.argv:
        sys.exit(check())
    if "--checked" in sys.argv:
        apply_checked_date(sys.argv[sys.argv.index("--checked") + 1])
    check_lengths()
    os.makedirs(OUT, exist_ok=True)
    pages = {"index.html": hub_page()}
    for g in GUIDES:
        pages[g["slug"] + ".html"] = guide_page(g)
    for name, text in pages.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
            f.write(text)
    print(f"wrote {len(pages)} pages | review pages linked: {add_review_links()} | sitemap entries added: {add_sitemap()} | homepage block: {'updated' if update_homepage() else 'NOT FOUND'}")
    # The pages above are written with a plain header; build_nav.py adds the dropdown menus, the season
    # script and the cache-busting versions. Run it here so the two can never get out of step.
    import build_nav
    build_nav.main()


if __name__ == "__main__":
    main()
