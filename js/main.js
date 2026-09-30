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
