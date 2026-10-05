() => {
  // Runs inside the page. Returns plain data; the Python tests decide what counts as a failure.
  const vw = innerWidth;
  const vis = (e) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none';
  };
  const inScroller = (e) => {
    for (let n = e.parentElement; n && n !== document.body; n = n.parentElement) {
      const o = getComputedStyle(n).overflowX;
      if (o === 'auto' || o === 'scroll') return true;
    }
    return false;
  };
  const label = (e) => e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/)[0] : '');
  const $$ = (s) => [...document.querySelectorAll(s)];

  // Anything sticking out past the right edge of the screen (outside a scrolling box).
  const wide = $$('body *')
    .filter((e) => !/^(SCRIPT|STYLE|PATH|SVG|BR)$/i.test(e.tagName) && vis(e) && !inScroller(e)
      && getComputedStyle(e).position !== 'fixed' && e.getBoundingClientRect().right > vw + 1)
    .slice(0, 5)
    .map((e) => `${label(e)} right=${Math.round(e.getBoundingClientRect().right)}`);

  const images = $$('img');
  const brokenImages = images.filter((i) => i.getAttribute('src') && i.complete && i.naturalWidth === 0).map((i) => i.getAttribute('src'));
  const imagesWithoutAlt = images.filter((i) => !i.hasAttribute('alt')).map((i) => i.getAttribute('src'));

  // Buttons and links we own, which must be easy to tap.
  const targetSelectors = '.page-tools button, .page-tools a, .table-tools button, .perk-btn, .btn-check-price, .nav-cta, .nav-toggle, .faq-q, .country-badge-pill';
  const smallTargets = $$(targetSelectors).filter(vis)
    .map((e) => ({ el: label(e), w: Math.round(e.getBoundingClientRect().width), h: Math.round(e.getBoundingClientRect().height) }))
    .filter((t) => t.h < 43.5);

  // Print & share toolbar
  const bars = $$('.page-tools');
  let toolbar = { count: bars.length };
  if (bars.length) {
    const bar = bars[0];
    const host = bar.parentElement;
    const first = [...host.children].find((c) => c !== bar && !c.classList.contains('print-only') && c.getBoundingClientRect().width > 0);
    toolbar.labels = [...bar.querySelectorAll('button, a')].map((b) => b.textContent.trim());
    toolbar.leftDelta = first ? Math.round(bar.getBoundingClientRect().left - first.getBoundingClientRect().left) : null;
    toolbar.rightOverflow = Math.round(bar.getBoundingClientRect().right - vw);
    const tops = new Set([...bar.querySelectorAll('button, a')].map((b) => Math.round(b.getBoundingClientRect().top)));
    toolbar.rows = tops.size;
  }

  // Comparison table: the section under <h2 id="comparison">
  const compare = document.querySelector('h2#comparison');
  const sectionHasTable = (h) => {
    for (let n = h.nextElementSibling; n && n.tagName !== 'H2'; n = n.nextElementSibling) {
      if (n.tagName === 'TABLE' || n.querySelector('table')) return true;
    }
    return false;
  };
  const hasCompareTable = !!compare && sectionHasTable(compare);
  const tableTools = $$('.table-tools');
  const hint = document.querySelector('.table-tools .table-hint');
  const scroller = (() => {
    if (!compare) return null;
    for (let n = compare.nextElementSibling; n && n.tagName !== 'H2'; n = n.nextElementSibling) {
      if (n.tagName === 'TABLE') return n.parentElement;
      if (n.querySelector && n.querySelector('table')) return n;
    }
    return null;
  })();

  // Membership offers
  const perk = {
    notes: $$('.perk-note').length,
    cta: $$('.perk-cta').length,
    tips: $$('.perk-line').length,
    cardNotes: $$('.card-perk').length,
    buttons: $$('.perk-btn').map((b) => ({ href: b.href, text: b.textContent.trim(), h: Math.round(b.getBoundingClientRect().height) })),
  };

  const links = $$('a[href]').map((a) => ({
    href: a.getAttribute('href'),
    abs: a.href,
    rel: a.getAttribute('rel') || '',
    target: a.getAttribute('target') || '',
    text: a.textContent.trim().slice(0, 60),
    cta: a.getAttribute('data-cta') || '',
    product: a.getAttribute('data-product') || '',
  }));

  const smallProsCons = $$('.pros li, .cons li').filter((e) => vis(e) && parseFloat(getComputedStyle(e).fontSize) < 14).length;
  const header = document.querySelector('header');
  const toggle = document.querySelector('.nav-toggle');

  return {
    title: document.title,
    lang: document.documentElement.lang,
    h1Count: $$('h1').length,
    h1Text: ($$('h1')[0] || {}).textContent ? $$('h1')[0].textContent.trim() : '',
    canonical: (document.querySelector('link[rel="canonical"]') || {}).href || '',
    viewportMeta: !!document.querySelector('meta[name="viewport"]'),
    vw,
    docWidth: document.documentElement.scrollWidth,
    wide,
    brokenImages,
    imagesWithoutAlt,
    smallTargets,
    toolbar,
    hasCompareTable,
    compareId: compare ? compare.id : null,
    layout: (() => {
      const art = document.querySelector('article.article-body');
      const side = document.querySelector('aside.article-sidebar');
      if (!art || !side) return { article: !!art, sidebar: !!side };
      const a = art.getBoundingClientRect(), s = side.getBoundingClientRect();
      return { article: true, sidebar: true, sideRight: s.left >= a.right - 1, sideBelow: s.top >= a.bottom - 1, boxes: [...side.querySelectorAll('.sidebar-box h3')].map((h) => h.textContent.trim()) };
    })(),
    tableToolsCount: tableTools.length,
    hintVisible: !!hint && !hint.hidden,
    tableScrolls: scroller ? scroller.scrollWidth > scroller.clientWidth + 1 : null,
    perk,
    links,
    smallProsCons,
    hasHeader: !!header && vis(header),
    hasFooter: !!document.querySelector('footer'),
    navToggleVisible: !!toggle && vis(toggle),
    badge: (() => {
      const e = document.querySelector('.country-badge-pill');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { count: $$('.country-badge').length, tag: e.tagName, text: e.querySelector('span').textContent.trim(), href: e.getAttribute('href'), label: e.getAttribute('aria-label') || e.closest('.country-badge').getAttribute('aria-label'),
        top: Math.round(r.top), left: Math.round(r.left), right: Math.round(r.right), bottom: Math.round(r.bottom), height: Math.round(r.height), vw, vh: innerHeight };
    })(),
    buySummary: (() => {
      const e = document.querySelector('.buy-summary');
      const tl = document.querySelector('.toc a[href="#top-picks"], .toc a[href="#which-one"]');
      return e ? { dup: e.classList.contains('buy-summary-dup'), shown: getComputedStyle(e).display !== 'none', tocLinkShown: tl ? !!tl.offsetParent : null } : null;
    })(),
    author: (() => {
      const e = document.querySelector('.author-box'), f = document.querySelector('footer'), n = document.querySelector('.newsletter');
      if (!e || !f) return null;
      const r = e.getBoundingClientRect(), fr = f.getBoundingClientRect();
      return { height: Math.round(r.height), gapToFooter: Math.round(fr.top - r.bottom), afterNewsletter: !n || (n.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0 };
    })(),
    adSlots: $$('.ad-slot').map((e) => {
      const r = e.getBoundingClientRect(), hero = document.querySelector('.article-hero');
      return { where: [...e.classList].find((c) => c.startsWith('ad-slot-')), shown: getComputedStyle(e).display !== 'none', top: Math.round(r.top + scrollY), height: Math.round(r.height),
        heroBottom: hero ? Math.round(hero.getBoundingClientRect().bottom + scrollY) : 0, inside: !!e.closest('ul, ol, table, .product-card, .toc, .toc-box, .faq-item, .perk-offers, .buy-summary, .sources') };
    }),
    faqCount: $$('.faq-item').length,
    scrollY: scrollY,
  };
}
