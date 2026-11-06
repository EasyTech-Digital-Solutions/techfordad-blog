#!/usr/bin/env python3
"""Check Amazon.com product listings before publishing (or re-checking) a Gift Guides post.

    python3 scripts/check_amazon_listings.py OUT.json ASIN [ASIN ...]

For each ASIN it reads the public listing (US storefront, USD) and records the title,
buy-box price when Amazon exposes one, star rating, rating count, the seller, and whether the
listing has a real Add to Cart button (i.e. is buyable) or is unavailable / renewed. Amazon hides
prices and buy buttons from visitors outside the US, so the script first sets a US delivery ZIP,
as a visitor would with "Deliver to". Prices are often missing for variation pages, so treat a
missing price as "check by hand", not as "free".
Keep the delay: Amazon rate-limits fast, repeated requests.
"""
import re,sys,time,html,json,http.cookiejar,urllib.request
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
CK='i18n-prefs=USD; lc-main=en_US'
ZIP='10001'
OPENER=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
ZIP_SET=False
# The real buttons. The bare string add-to-cart-button is on every page (a keyboard-shortcut target).
BUY_BUTTONS=('id="add-to-cart-button"','id="add-to-cart-button-ubb"','name="submit.add-to-cart"','id="buy-now-button"','name="submit.buy-now"')
NOT_SELLER=re.compile(r'^(Returnable|Eligible|Return|Free|Secure|Payment|Packaging|Gift)',re.I)
def page(path,headers=None,data=None):
    req=urllib.request.Request('https://www.amazon.com'+path,headers={'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9','Cookie':CK,**(headers or {})},data=data)
    try:
        r=OPENER.open(req,timeout=25); return r.status,r.read().decode('utf8','ignore')
    except Exception as e:
        return getattr(e,'code',0),''
def set_zip(asin):
    """Choose the delivery ZIP from a product page (the home page answers scripts with a challenge). True when Amazon accepts it."""
    s,t=page(f'/dp/{asin}')
    m=re.search(r'"anti-csrftoken-a2z"\s*:\s*"([^"]+)"\s*\}\s*,\s*"name"\s*:\s*"glow-modal"\s*,\s*"url"\s*:\s*"([^"]+)"',html.unescape(t))
    if s!=200 or not m: return False
    time.sleep(2)
    s,modal=page(m.group(2),{'anti-csrftoken-a2z':m.group(1),'X-Requested-With':'XMLHttpRequest'})
    m2=re.search(r'CSRF_TOKEN\s*:\s*"([^"]+)"',modal)
    if s!=200 or not m2: return False
    time.sleep(2)
    body=json.dumps({'locationType':'LOCATION_INPUT','zipCode':ZIP,'deviceType':'web','storeContext':'generic','pageType':'Detail','actionSource':'glow'}).encode()
    s,res=page('/portal-migration/hz/glow/address-change?actionSource=glow',{'anti-csrftoken-a2z':m2.group(1),'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},body)
    try: return s==200 and bool(json.loads(res).get('isValidAddress'))
    except ValueError: return False
def clean(x): return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',x or ''))).strip()
def is_robot_check(t):
    # Amazon serves a tiny robot-check page when it rate-limits; wait several minutes and retry.
    # Product pages run past 1 MB, and a customer review on one can say "captcha".
    return len(t)<20000 or (len(t)<200000 and 'captcha' in t.lower())
def parse(t):
    """The listing's fields from one product page."""
    g=lambda p,f=re.S:(re.search(p,t,f) or [None,None])[1]
    title=clean(g(r'id="productTitle"[^>]*>(.*?)</span>'))
    # buy-box price: first a-offscreen inside the core price block, else the add-to-cart form
    core=g(r'(id="corePrice_feature_div".{0,3000})') or g(r'(id="corePriceDisplay_desktop_feature_div".{0,3000})') or g(r'(id="apex_desktop".{0,3000})') or ''
    prices=re.findall(r'class="a-offscreen">\s*(\$[\d,]+\.?\d*)',core)
    price=prices[0] if prices else g(r'name="items\[0\.base\]\[customerVisiblePrice\]\[displayString\]" value="(\$[\d,]+\.?\d*)"')
    strike=re.findall(r'data-a-strike="true"[^>]*>\s*<span class="a-offscreen">\s*(\$[\d,]+\.?\d*)',core)
    listp=strike[0] if strike else None
    # the product's own rating box: the first "out of 5 stars" on a page can belong to another product
    rating=g(r'id="acrPopover"[^>]*title="(\d(?:\.\d)?) out of 5 stars') or g(r'id="averageCustomerReviews".{0,1500}?(\d\.\d) out of 5 stars')
    cnt=g(r'id="acrCustomerReviewText"[^>]*>\s*\(?([\d,\.KkMm]+)')
    cart=any(b in t for b in BUY_BUTTONS)
    oos=clean(g(r'id="outOfStock"[^>]*>(.*?)</div>'))
    unavailable=not cart and bool(re.search(r'currently unavailable|cannot be shipped',oos,re.I))
    no_offer=not cart and 'No featured offers available' in t
    def feature(name):  # the value line inside one buy-box block (Ships from / Sold by)
        i=t.find(f'id="{name}_feature_div"')
        m=re.search(r'offer-display-feature-text-message">(.*?)</span>',t[i:i+3000],re.S) if i>=0 else None
        return clean(m.group(1)) if m else None
    who=feature('merchantInfoFeature') or clean(g(r'id="sellerProfileTriggerId"[^>]*>(.*?)</a>')) or None
    if who and NOT_SELLER.search(who): who=None
    renewed=bool(re.search(r'\bRenewed\b|Like-New|Refurbished',title)) or bool(who and re.search(r'warehouse|resale',who,re.I))
    return dict(title=title[:80],price=price,list=listp,rating=rating,ratings=cnt,cart=cart,unavailable=unavailable,no_offer=no_offer,who=who,renewed=renewed,
                deliver_to=clean(g(r'id="glow-ingress-line2"[^>]*>(.*?)</span>'))[:40])
def verify(asin):
    global ZIP_SET
    if not ZIP_SET:
        ZIP_SET=set_zip(asin)
        if not ZIP_SET: print('note: could not set the US delivery ZIP; from outside the US, buttons and prices may be missing',file=sys.stderr,flush=True)
        time.sleep(1.6)
    s,t=page(f'/dp/{asin}')
    if s!=200: return dict(asin=asin,status=s)
    if is_robot_check(t): return dict(asin=asin,status='blocked')
    return dict(asin=asin,status=s,**parse(t))
if __name__=='__main__':
    out=[]
    for a in sys.argv[2:]:
        d=verify(a); out.append(d); print(json.dumps(d,ensure_ascii=False),flush=True); time.sleep(1.6)
    open(sys.argv[1],'w',encoding='utf8').write(json.dumps(out,indent=1,ensure_ascii=False))
