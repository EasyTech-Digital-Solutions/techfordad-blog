"""The newsletter signup form tells Mailchimp where each subscriber signed up (scripts/build_newsletter_fields.py)."""
import re
import sys

import pytest

import pages as P

sys.path.insert(0, str(P.ROOT / "scripts"))
import build_newsletter_fields as N  # noqa: E402
import build_related as R  # noqa: E402

FORM = re.compile(r'<form class="email-form"[^>]*list-manage[^>]*>(.*?)</form>', re.S)
PAGES = [rel for rel, _ in N.pages() if FORM.search(P.read(rel))]
ACTION = "https://us2.list-manage.com/subscribe/post?u=4d4642fb82dc99daa1b66f684&amp;id=8cf3d53e8d"


def _fields(rel):
    inner = FORM.search(P.read(rel)).group(1)
    return dict(re.findall(r'<input type="hidden" name="([A-Z]+)" value="([^"]*)"/>', inner.split("<!-- /nl-fields -->")[0]))


def test_the_signup_form_is_on_every_content_page_family():
    assert len(PAGES) >= 40
    assert "index.html" in PAGES and any(p.startswith("gift-guides/") for p in PAGES) and any(p.startswith("guides/") for p in PAGES)


@pytest.mark.parametrize("rel", PAGES)
def test_the_form_carries_the_page_topic_and_country(rel):
    text = P.read(rel)
    assert text.count("<!-- nl-fields -->") == 1, "exactly one block of hidden fields"
    f = _fields(rel)
    assert f["SOURCE"] == ("home" if rel == "index.html" else rel.removesuffix(".html"))
    assert f["TOPIC"] and f["TOPIC"] != "other", f"{rel} has no topic: add it to FAMILY in scripts/build_newsletter_fields.py"
    if rel.endswith("-canada.html"):
        assert f.get("COUNTRY") == "CA"
    elif rel.startswith(("blog/", "gift-guides/")) and R.topic_of(rel) and R.TOPICS[R.topic_of(rel)][0] != R.TOPICS[R.topic_of(rel)][1]:
        assert f.get("COUNTRY") == "US"
    elif rel in ("index.html",) or rel.startswith("guides/"):
        assert "COUNTRY" not in f, "pages not tied to a country send no COUNTRY"
    assert set(f) <= {"SOURCE", "TOPIC", "COUNTRY"}, "only the three Mailchimp fields the owner created"


@pytest.mark.parametrize("rel", PAGES[:12])
def test_the_form_still_posts_to_the_same_audience_and_keeps_its_spam_trap(rel):
    text = P.read(rel)
    assert f'action="{ACTION}"' in text and 'method="post"' in text
    assert 'name="b_4d4642fb82dc99daa1b66f684_8cf3d53e8d"' in text, "the honeypot field is gone"
    assert 'type="email" name="EMAIL"' in text and "required" in FORM.search(text).group(1)


def test_every_topic_key_has_a_newsletter_family():
    missing = sorted(set(R.TOPICS) - set(N.FAMILY))
    assert not missing, f"add these topics to FAMILY in scripts/build_newsletter_fields.py: {missing}"


def test_gift_guides_and_home_have_their_own_topics():
    assert _fields("index.html")["TOPIC"] == "home"
    assert {_fields(p)["TOPIC"] for p in PAGES if p.startswith("gift-guides/")} == {"gifts"}


def test_the_privacy_policy_says_what_is_recorded_at_signup():
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", P.read("privacy-policy.html")))
    assert "which page of our site you signed up from" in text and "which links in our emails you click" in text
    assert "Mailchimp" in text and "delete your address" in text
