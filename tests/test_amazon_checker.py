"""scripts/check_amazon_listings.py decides whether a listing is live before it goes on the site, so its page reading is tested."""
import importlib.util

import pages as P

spec = importlib.util.spec_from_file_location("check_amazon_listings", P.ROOT / "scripts" / "check_amazon_listings.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

SHORTCUT = '<span data-target="#add-to-cart-button" aria-label="Add to cart, shift, alt, K"></span>'
OTHER_STARS = '<i class="a-icon"><span>2.7 out of 5 stars</span></i>'
OWN_RATING = '<span id="acrPopover" data-action="x" title="4.7 out of 5 stars"></span><span id="acrCustomerReviewText">(2,757 ratings)</span>'
SELLER = ('<div id="merchantInfoFeature_feature_div"><span class="offer-display-feature-text-message">Amazon.com</span></div>'
          '<div id="returnsInfoFeature_feature_div"><span class="offer-display-feature-text-message">Returnable until Jan 31</span></div>')


def test_the_keyboard_shortcut_is_not_a_buy_button():
    page = SHORTCUT + '<div id="outOfStock" class="a-box">Currently unavailable. We don\'t know when.</div>'
    d = checker.parse(page)
    assert d["cart"] is False and d["unavailable"] is True


def test_a_real_button_means_buyable():
    d = checker.parse(SHORTCUT + '<input id="add-to-cart-button" name="submit.add-to-cart">' + SELLER)
    assert d["cart"] is True and d["unavailable"] is False and d["who"] == "Amazon.com"


def test_no_featured_offers_is_reported():
    d = checker.parse(SHORTCUT + '<span>No featured offers available</span>')
    assert d["cart"] is False and d["no_offer"] is True


def test_the_rating_comes_from_the_products_own_box():
    d = checker.parse(OTHER_STARS + OWN_RATING)
    assert d["rating"] == "4.7" and d["ratings"] == "2,757"


def test_used_offers_are_flagged():
    page = '<input id="add-to-cart-button">' + SELLER.replace("Amazon.com", "Amazon Resale")
    assert checker.parse(page)["renewed"] is True


def test_a_review_mentioning_captcha_is_not_a_robot_check():
    assert checker.is_robot_check("x" * 1_500_000 + "The browser doesn't support Captcha") is False


def test_a_short_page_is_a_robot_check():
    assert checker.is_robot_check("<form action='/errors/validateCaptcha'>") is True
    assert checker.is_robot_check("x" * 30_000 + "Enter the characters: captcha") is True
