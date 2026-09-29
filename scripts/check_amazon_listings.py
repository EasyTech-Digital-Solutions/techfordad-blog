#!/usr/bin/env python3
"""Check Amazon.com product listings before publishing (or re-checking) a Gift Guides post.

    python3 scripts/check_amazon_listings.py OUT.json ASIN [ASIN ...]

For each ASIN it reads the public listing (US storefront, USD) and records the title,
buy-box price when Amazon exposes one, star rating, rating count, and whether the listing
has an Add to Cart button (i.e. is buyable) or is unavailable / renewed. Amazon serves the
page in the visitor's currency, so the script asks for USD via cookie. Prices are often
missing for variation pages, so treat a missing price as "check by hand", not as "free".
Keep the delay: Amazon rate-limits fast, repeated requests.
"""
import re,sys,time,html,json,urllib.request
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
CK='i18n-prefs=USD; lc-main=en_US'
def page(asin):
    req=urllib.request.Request(f'https://www.amazon.com/dp/{asin}',headers={'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9','Cookie':CK})
    try:
        r=urllib.request.urlopen(req,timeout=25); return r.status,r.read().decode('utf8','ignore')
    except Exception as e:
        return getattr(e,'code',0),''
def clean(x): return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',x or ''))).strip()
def verify(asin):
    s,t=page(asin)
    if s!=200: return dict(asin=asin,status=s)
    if len(t)<20000 or 'captcha' in t.lower():
        # Amazon serves a tiny robot-check page when it rate-limits; wait several minutes and retry.
        return dict(asin=asin,status='blocked')
    g=lambda p,f=re.S:(re.search(p,t,f) or [None,None])[1]
    title=clean(g(r'id="productTitle"[^>]*>(.*?)</span>'))
    # buy-box price: first a-offscreen inside the core price block
    core=g(r'(id="corePrice_feature_div".{0,2500})') or g(r'(id="corePriceDisplay_desktop_feature_div".{0,2500})') or ''
    prices=re.findall(r'class="a-offscreen">\s*(\$[\d,]+\.?\d*)',core)
    price=(re.search(r'"displayPrice"\s*:\s*"(\$[^"]+)"',t) or [None,None])[1] or (prices[0] if prices else None)
    strike=re.findall(r'data-a-strike="true"[^>]*>\s*<span class="a-offscreen">\s*(\$[\d,]+\.?\d*)',core)
    listp=strike[0] if strike else None
    rating=g(r'(\d\.\d) out of 5 stars')
    cnt=g(r'id="acrCustomerReviewText"[^>]*>\s*\(?([\d,\.KkMm]+)') or g(r'([\d,]+) (?:global )?ratings')
    cart='add-to-cart-button' in t
    unavailable=bool(re.search(r'Currently unavailable',t)) and not cart
    ships=clean(g(r'id="fulfillerInfoFeature_feature_div"(.{0,600})')); sold=clean(g(r'id="merchantInfoFeature_feature_div"(.{0,700})'))
    who=(sold or ships)[:70]
    renewed=bool(re.search(r'\bRenewed\b|Like-New|Refurbished',title))
    return dict(asin=asin,status=s,title=title[:80],price=price,list=listp,rating=rating,ratings=cnt,cart=cart,unavailable=unavailable,who=who,renewed=renewed)
if __name__=='__main__':
    out=[]
    for a in sys.argv[2:]:
        d=verify(a); out.append(d); print(json.dumps(d,ensure_ascii=False),flush=True); time.sleep(1.6)
    open(sys.argv[1],'w',encoding='utf8').write(json.dumps(out,indent=1,ensure_ascii=False))
