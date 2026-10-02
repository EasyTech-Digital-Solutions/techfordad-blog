// FAQ Toggle
document.querySelectorAll('.faq-q').forEach(q => {
  q.addEventListener('click', () => {
    const item = q.parentElement;
    const isOpen = item.classList.contains('open');
    document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
    if (!isOpen) item.classList.add('open');
  });
});

// GA4 events — gtag is defined inline in each page's <head>; guard in case it's blocked.
function track(name, params) {
  if (typeof gtag === 'function') gtag('event', name, params);
}

// Affiliate clicks — one delegated listener covers every Amazon link (.com and .ca).
// auxclick catches middle-click "open in new tab".
function onAffiliateClick(e) {
  if (e.type === 'auxclick' && e.button !== 1) return;
  const a = e.target.closest('a[href*="amazon."]');
  if (!a) return;
  let url;
  try { url = new URL(a.href); } catch { return; }
  if (!/(^|\.)amazon\.(com|ca)$/.test(url.hostname)) return;

  // Which numbered product button is this? (1-based position among the per-product buttons on the page)
  const productButtons = [...document.querySelectorAll('a.btn-check-price[data-cta="product_section"]')];
  const idx = productButtons.indexOf(a);

  // Where on the page was it clicked? Buttons carry data-cta (product_section, comparison_table);
  // other Amazon links are sidebar or inline links.
  let ctaLocation = a.dataset.cta || 'inline';
  if (!a.dataset.cta && a.closest('.sidebar-box')) ctaLocation = 'sidebar';
  if (!a.dataset.cta && a.closest('table')) ctaLocation = 'comparison_table';

  // Measures outbound clicks to Amazon only, not purchases or commission.
  track('amazon_affiliate_click', {
    product_name: a.dataset.product || a.textContent.trim().slice(0, 100),
    article_slug: location.pathname.split('/').pop().replace(/\.html$/, '') || 'home',
    product_position: idx > -1 ? idx + 1 : 0,   // 0 = not one of the numbered product buttons
    cta_location: ctaLocation,
    country: /\.ca$/.test(url.hostname) ? 'CA' : 'US'
  });
}
document.addEventListener('click', onAffiliateClick);
document.addEventListener('auxclick', onAffiliateClick);

// Email form — Mailchimp opens in a new tab (target="_blank"), so this page never
// navigates away. Show a brief "submitting" state, then revert to a success message
// since the real confirmation happens in the new tab.
document.querySelectorAll('.email-form').forEach(form => {
  form.addEventListener('submit', () => {
    track('newsletter_signup', { form_location: form.closest('section, aside, footer')?.className || '' });
    const btn = form.querySelector('button[type="submit"]');
    if (btn) {
      const originalText = btn.textContent;
      btn.textContent = '✓ Submitting…';
      btn.style.background = '#16A34A';
      setTimeout(() => {
        btn.textContent = '✓ Check the new tab';
        setTimeout(() => {
          btn.textContent = originalText;
          btn.style.background = '';
        }, 3000);
      }, 1500);
    }
  });
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// Mobile nav toggle
const navToggle = document.querySelector('.nav-toggle');
const siteNav = document.getElementById('site-nav');
if (navToggle && siteNav) {
  navToggle.addEventListener('click', () => {
    const isOpen = siteNav.classList.toggle('open');
    navToggle.classList.toggle('active', isOpen);
    navToggle.setAttribute('aria-expanded', isOpen);
  });
  siteNav.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      siteNav.classList.remove('open');
      navToggle.classList.remove('active');
      navToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

// Reviews dropdown — opens on hover via CSS (desktop), and on click/tap/keyboard here.
// Only one menu is open at a time: opening or hovering one closes the others.
const navDropdowns = Array.from(document.querySelectorAll('.nav-dropdown'));
const canHover = window.matchMedia('(hover: hover) and (min-width: 1081px)');
navDropdowns.forEach(dd => {
  const btn = dd.querySelector('.nav-dropdown-toggle');
  if (!btn) return;
  const setOpen = open => {
    dd.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', String(open));
  };
  dd._setOpen = setOpen;
  const closeOthers = () => navDropdowns.forEach(o => { if (o !== dd && o._setOpen) o._setOpen(false); });
  btn.addEventListener('click', () => {
    const willOpen = !dd.classList.contains('open');
    if (willOpen) closeOthers();
    setOpen(willOpen);
  });
  dd.addEventListener('mouseenter', () => { if (canHover.matches) closeOthers(); });
  dd.addEventListener('focusin', closeOthers);
  document.addEventListener('click', e => {
    if (!dd.contains(e.target)) setOpen(false);
  });
  dd.addEventListener('keydown', e => {
    if (e.key === 'Escape' && dd.classList.contains('open')) {
      setOpen(false);
      btn.focus();
    }
  });
  dd.querySelectorAll('a').forEach(a => a.addEventListener('click', () => setOpen(false)));
});

// Gift announcement bar: dismiss and remember for 14 days (js/season.js reads this before first paint).
document.querySelectorAll('.gift-bar-close').forEach(btn => {
  btn.addEventListener('click', () => {
    document.documentElement.setAttribute('data-gift-bar', 'closed');
    try { localStorage.setItem('giftBarClosed', String(Date.now())); } catch (e) { /* storage blocked */ }
  });
});

// Homepage gift block: in gift season move it up, just above "Our Top Picks".
(function () {
  const gift = document.querySelector('.gift-feature');
  const top = document.querySelector('.top-picks');
  if (gift && top && document.documentElement.getAttribute('data-gifts') === 'peak') {
    top.parentNode.insertBefore(gift, top);
  }
})();

// Auto-updating copyright year
document.querySelectorAll('#year').forEach(el => {
  el.textContent = new Date().getFullYear();
});

// Print & share toolbar — articles, gift guides and guides (not the index pages).
// Injected here so every page gets it without editing the HTML. Shares the canonical
// page URL (never an affiliate link) so a text or email to a sibling stays clean.
(function () {
  if (!/^\/(blog|gift-guides|guides)\/[^/]+\.html$/.test(location.pathname) || /\/index\.html$/.test(location.pathname)) return;
  // Gift guides nest their content in .article-inner (a centred 820px column); put the toolbar there.
  const host = document.querySelector('.article-body .article-inner') ||
    document.querySelector('article.article-body, .article-body, .about-body');
  if (!host) return;
  host.classList.add('print-host');

  const canonical = document.querySelector('link[rel="canonical"]');
  const url = (canonical && canonical.href) || location.origin + location.pathname;
  const h1 = document.querySelector('h1');
  const title = (h1 && h1.textContent.trim()) || document.title;
  const message = title + '\n' + url;
  const page = location.pathname;

  const bar = document.createElement('div');
  bar.className = 'page-tools';
  bar.setAttribute('role', 'group');
  bar.setAttribute('aria-label', 'Print or share this page');
  const status = document.createElement('span');
  status.className = 'page-tools-status';
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');

  function addButton(label, onClick) {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = label;
    b.addEventListener('click', onClick);
    bar.appendChild(b);
    return b;
  }
  function addLink(label, href, method) {
    const a = document.createElement('a');
    a.textContent = label;
    a.href = href;
    a.addEventListener('click', () => track('share', { method: method, content_type: 'article', item_id: page }));
    bar.appendChild(a);
  }
  function say(msg) {
    status.textContent = msg;
    setTimeout(() => { status.textContent = ''; }, 3000);
  }
  function copyLink() {
    const done = () => { track('share', { method: 'copy_link', content_type: 'article', item_id: page }); say('Link copied'); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(done, () => say('Could not copy. Copy the address from your browser instead.'));
    } else {
      const t = document.createElement('textarea');
      t.value = url; t.style.position = 'fixed'; t.style.opacity = '0';
      document.body.appendChild(t); t.select();
      try { document.execCommand('copy') ? done() : say('Could not copy. Copy the address from your browser instead.'); } catch (e) { say('Could not copy. Copy the address from your browser instead.'); }
      t.remove();
    }
  }

  addButton('Print this page', () => window.print());

  // Compact print modes: mark some sections, hide the rest of the article for one print,
  // then restore it. 'summary' = picks + comparison table, 'table' = comparison table only.
  let marked = [];
  let printMode = 'full';
  let savedY = null;  // scroll position to restore: closing the print dialog can jump the page to the top
  function section(id) {
    const h = host.querySelector('h2#' + id);
    const nodes = [];
    if (!h) return nodes;
    nodes.push(h);
    for (let n = h.nextElementSibling; n && n.tagName !== 'H2'; n = n.nextElementSibling) nodes.push(n);
    return nodes;
  }
  function printSections(nodes, mode) {
    savedY = window.scrollY;
    marked = nodes;
    printMode = mode;
    nodes.forEach(n => n.classList.add('print-keep'));
    document.body.classList.add('print-summary');
    window.print();
  }
  window.addEventListener('afterprint', () => {
    document.body.classList.remove('print-summary');
    marked.forEach(n => n.classList.remove('print-keep'));
    marked = [];
    printMode = 'full';
    if (savedY !== null) {
      const y = savedY;
      savedY = null;
      const restore = () => window.scrollTo({ top: y, behavior: 'instant' });
      restore();
      requestAnimationFrame(restore);  // again after the browser re-lays out the page
    }
  });
  const summaryNodes = [].concat(section('top-picks'), section('which-one'), section('comparison'));
  if (summaryNodes.length) addButton('Print quick comparison', () => printSections(summaryNodes, 'summary'));

  if (navigator.share) {
    addButton('Share', () => {
      navigator.share({ title: title, url: url }).then(
        () => track('share', { method: 'native', content_type: 'article', item_id: page }),
        () => {}  // dismissed the share sheet
      );
    });
  } else {
    addLink('Text it', 'sms:?&body=' + encodeURIComponent(message), 'sms');
    addLink('Email it', 'mailto:?subject=' + encodeURIComponent(title) + '&body=' + encodeURIComponent(message), 'email');
  }
  addButton('Copy link', copyLink);
  bar.appendChild(status);

  // Shown only when printing: where the page came from and when, since prices change.
  const printHead = document.createElement('p');
  printHead.className = 'print-only print-head';
  const printFoot = document.createElement('p');
  printFoot.className = 'print-only print-foot';
  host.insertBefore(printHead, host.firstChild);
  bar.id = 'page-tools';
  host.insertBefore(bar, host.firstChild);

  // One-click print right where the reader is looking at the comparison table.
  const tableSection = section('comparison');
  const wrap = tableSection.find(n => n.tagName === 'TABLE' || (n.querySelector && n.querySelector('table')));
  if (wrap) {
    const tools = document.createElement('div');
    tools.className = 'table-tools';
    const printTable = document.createElement('button');
    printTable.type = 'button';
    printTable.textContent = 'Print this table';
    printTable.addEventListener('click', () => printSections(tableSection, 'table'));
    const more = document.createElement('a');
    more.href = '#page-tools';
    more.textContent = 'More print and share options \u2191';
    more.addEventListener('click', e => {
      e.preventDefault();
      bar.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const first = bar.querySelector('button, a');
      if (first) setTimeout(() => first.focus({ preventScroll: true }), 400);
    });
    tools.appendChild(printTable);
    tools.appendChild(more);
    // Tell phone readers when the table is wider than the screen.
    const hint = document.createElement('p');
    hint.className = 'table-hint';
    hint.textContent = 'Swipe the table sideways to see every column \u2192';
    hint.hidden = true;
    tools.appendChild(hint);
    wrap.parentNode.insertBefore(tools, wrap);
    const scroller = wrap.tagName === 'TABLE' ? wrap.parentElement : wrap;
    const updateHint = () => { hint.hidden = scroller.scrollWidth <= scroller.clientWidth + 1; };
    updateHint();
    window.addEventListener('resize', updateHint);
    window.addEventListener('load', updateHint);
  }
  host.appendChild(printFoot);

  window.addEventListener('beforeprint', () => {
    if (savedY === null) savedY = window.scrollY;  // Ctrl/Cmd+P and the full-page button
    const today = new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
    printHead.textContent = 'TechForDad · ' + url;
    printFoot.textContent = 'Printed ' + today + '. Prices and availability change, so check the retailer before you buy.';
    track('print', { content_type: 'article', item_id: page, print_mode: printMode });
  });
})();
