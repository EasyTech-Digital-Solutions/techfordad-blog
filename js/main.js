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
  track('affiliate_click', {
    store: url.hostname.replace(/^www\./, ''),
    product: url.searchParams.get('k') || url.pathname,
    link_class: a.className || '',
    link_url: a.href
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

// Auto-updating copyright year
document.querySelectorAll('#year').forEach(el => {
  el.textContent = new Date().getFullYear();
});
