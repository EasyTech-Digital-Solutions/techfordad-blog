// "Ask TechForDad" chat panel. Loaded by js/main.js the first time the floating button is pressed.
// Answers come from the Worker at /api/chat (worker/src/index.js). When it is unavailable (daily free allowance used
// up, offline, local copy), the panel searches js/chat-index.json in the browser and lists matching articles instead.
(function () {
  if (window.TFDChat) return;
  const self = document.currentScript;
  const INDEX_URL = self ? self.src.replace(/chat\.js(\?.*)?$/, 'chat-index.json$1') : '/js/chat-index.json';
  const API = '/api/chat';
  const MAX = 500;
  const STARTERS = [
    'Which tablet is easiest for a beginner?',
    'Is there a medical alert with no monthly fee?',
    'What is a good gift for a parent with dementia?',
  ];
  const country = document.documentElement.lang === 'en-CA' ? 'CA'
    : /^\/(blog|gift-guides)\//.test(location.pathname) ? 'US' : '';
  const slug = location.pathname.split('/').pop().replace(/\.html$/, '') || 'home';
  let session = (crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2)).slice(0, 36);
  const history = [];
  const transcript = [];
  let busy = false;
  let pageIndex = null;
  let turn = 0;

  function track(name, params) {
    if (typeof gtag === 'function') gtag('event', name, Object.assign({ article_slug: slug, country: country || 'none' }, params));
  }
  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  // ---------------------------------------------------------------- panel
  const launcher = document.getElementById('chat-launcher');
  const panel = el('div', 'chat-panel');
  panel.id = 'chat-panel';
  panel.hidden = true;
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-modal', 'false');
  panel.setAttribute('aria-labelledby', 'chat-title');

  const head = el('div', 'chat-head');
  const title = el('h2', 'chat-title', 'Ask TechForDad');
  title.id = 'chat-title';
  const close = el('button', 'chat-close', '×');
  close.type = 'button';
  close.setAttribute('aria-label', 'Close the chat');
  head.append(title, close);

  const note = el('p', 'chat-note');
  const privacy = el('a', '', 'How chats are used');
  privacy.href = '/privacy-policy.html#chat';
  note.append('Answers come from TechForDad’s articles. AI can make mistakes, so check the article before you buy. Please don’t type names, phone numbers or medical details. ', privacy);

  const log = el('div', 'chat-log');
  log.setAttribute('role', 'log');
  log.setAttribute('aria-live', 'polite');
  log.setAttribute('aria-label', 'Conversation');

  const starters = el('div', 'chat-starters');
  starters.setAttribute('role', 'group');
  starters.setAttribute('aria-label', 'Example questions');
  STARTERS.forEach(q => {
    const b = el('button', 'chat-starter', q);
    b.type = 'button';
    b.addEventListener('click', () => ask(q));
    starters.appendChild(b);
  });

  const form = el('form', 'chat-form');
  const label = el('label', 'chat-label', 'Your question');
  label.htmlFor = 'chat-input';
  const input = el('textarea', 'chat-input');
  input.id = 'chat-input';
  input.rows = 2;
  input.maxLength = MAX;
  input.placeholder = 'For example: which phone is easiest for my dad?';
  const send = el('button', 'chat-send', 'Send');
  send.type = 'submit';
  form.append(label, input, send);

  panel.append(head, note, log, starters, form);
  document.body.appendChild(panel);

  let opened = false;
  function open() {
    panel.hidden = false;
    if (!opened) { opened = true; log.scrollTop = log.scrollHeight; }  // a conversation restored from another page
    document.documentElement.setAttribute('data-chat', 'open');
    if (launcher) launcher.setAttribute('aria-expanded', 'true');
    input.focus();
    track('chat_open', {});
  }
  function hide() {
    panel.hidden = true;
    document.documentElement.removeAttribute('data-chat');
    if (launcher) { launcher.setAttribute('aria-expanded', 'false'); launcher.focus(); }
  }
  close.addEventListener('click', hide);
  panel.addEventListener('keydown', e => { if (e.key === 'Escape') hide(); });
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event('submit')); }
  });
  form.addEventListener('submit', e => { e.preventDefault(); ask(input.value); });

  // ---------------------------------------------------------------- messages
  function bubble(who) {
    const b = el('div', 'chat-msg chat-msg-' + who);
    log.appendChild(b);
    log.scrollTop = log.scrollHeight;
    return b;
  }

  // Plain text only (never HTML): paragraphs, and "- " lines become a list.
  function renderText(box, text) {
    let list = null;
    text.replace(/\*\*/g, '').split(/\n+/).map(s => s.trim()).filter(Boolean).forEach(line => {
      const item = line.match(/^(?:[-*•]|\d+[.)])\s+(.*)$/);
      if (item) {
        if (!list) { list = el('ul', 'chat-list'); box.appendChild(list); }
        list.appendChild(el('li', '', item[1]));
      } else {
        list = null;
        box.appendChild(el('p', '', line));
      }
    });
  }

  function renderLinks(box, heading, links, mode) {
    const safe = links.filter(l => l && typeof l.url === 'string' && l.url.startsWith('/') && !l.url.startsWith('//'));
    if (!safe.length) return;
    box.appendChild(el('p', 'chat-sources-title', heading));
    const ul = el('ul', 'chat-sources');
    safe.forEach(l => {
      const li = el('li');
      const a = el('a', '', l.title);
      a.href = l.url.split('#')[0];  // open the article at its top: a #section lands mid-page, under the sticky header
      a.addEventListener('click', () => track('chat_source_click', { link_url: l.url, chat_mode: mode }));
      li.appendChild(a);
      ul.appendChild(li);
    });
    box.appendChild(ul);
  }

  // Check Price buttons for the products the answer names (links and tags chosen by the Worker; checked again here).
  const TAGS = ['techfordad0b-20', 'abhikar91-20', 'techfordad-gifts-20'];
  function renderProducts(box, products) {
    const ok = (products || []).filter(p => {
      try {
        const u = new URL(p.url);
        return u.protocol === 'https:' && /^www\.amazon\.(com|ca)$/.test(u.hostname) && TAGS.includes(u.searchParams.get('tag'));
      } catch (e) { return false; }
    });
    if (!ok.length) return;
    const wrap = el('div', 'chat-products');
    ok.forEach(p => {
      const ca = new URL(p.url).hostname.endsWith('.ca');
      const a = el('a', 'chat-buy');
      a.href = p.url;
      a.target = '_blank';
      a.rel = 'sponsored noopener';
      a.dataset.cta = 'chat';
      a.dataset.product = p.name;
      a.setAttribute('aria-label', 'Check Price on Amazon' + (ca ? '.ca' : '') + ': ' + p.name);
      a.append(el('span', 'chat-buy-name', p.name), el('span', 'chat-buy-cta', 'Check Price on Amazon' + (ca ? '.ca' : '') + ' →'));
      wrap.appendChild(a);
    });
    wrap.appendChild(el('p', 'chat-disclosure', 'As an Amazon Associate I earn from qualifying purchases. Prices change, so check the current price on Amazon.'));
    box.appendChild(wrap);
  }

  function renderFeedback(box, reply) {
    const wrap = el('div', 'chat-feedback');
    wrap.setAttribute('role', 'group');
    wrap.setAttribute('aria-label', 'Was this answer helpful?');
    wrap.appendChild(el('span', '', 'Helpful?'));
    [['Yes', true], ['No', false]].forEach(([text, helpful]) => {
      const b = el('button', 'chat-fb', text);
      b.type = 'button';
      b.addEventListener('click', () => {
        track('chat_feedback', { helpful: helpful ? 'yes' : 'no' });
        fetch(API + '/feedback', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ id: reply.id, helpful }) }).catch(() => {});
        wrap.replaceChildren(el('span', '', 'Thanks for telling us.'));
        reply.feedback = true;
        save();
      });
      wrap.appendChild(b);
    });
    box.appendChild(wrap);
  }

  // ---------------------------------------------------------------- fallback search (no AI)
  const STOP = new Set('a an and are best can do does for from good how i in is it me my of on or the to what which who with you your our their his her mom dad mother father parent parents senior seniors elderly old older someone'.split(' '));
  const words = s => (s.toLowerCase().match(/[a-z0-9]+/g) || []).filter(w => w.length > 1 && !STOP.has(w))
    .map(w => w.length > 4 ? w.replace(/(es|s)$/, '') : w);

  async function search(question) {
    if (!pageIndex) {
      try { pageIndex = (await (await fetch(INDEX_URL)).json()).pages; } catch (e) { pageIndex = []; }
    }
    const q = words(question);
    if (!q.length) return [];
    const scored = pageIndex.map(p => {
      const t = words(p.t), d = words(p.d);
      let score = 0, bestHits = 0;
      q.forEach(w => { if (t.includes(w)) score += 3; if (d.includes(w)) score += 1; });
      p.h.forEach(([, text]) => { bestHits = Math.max(bestHits, q.filter(w => words(text).includes(w)).length); });
      score += bestHits * 2;
      if (country && p.c) score *= p.c === country ? 1.25 : 0.6;
      return { score, title: p.t, url: p.u };
    }).filter(r => r.score >= 3).sort((a, b) => b.score - a.score);
    return scored.slice(0, 3);
  }

  // ---------------------------------------------------------------- one reply, as data (so it can be saved and redrawn)
  function renderReply(box, r) {
    if (r.text) renderText(box, r.text);
    renderProducts(box, r.products);
    if (r.links && r.links.length) renderLinks(box, r.linksTitle, r.links, r.mode);
    if (r.browse) {
      const p = el('p', '', 'I couldn’t find a matching article. You can browse ');
      const a = el('a', '', 'all reviews');
      a.href = '/blog/index.html';
      p.append(a, '.');
      box.appendChild(p);
    }
    if (r.feedback) box.appendChild(el('p', 'chat-feedback', 'Thanks for telling us.'));
    else if (r.id) renderFeedback(box, r);
  }

  // ---------------------------------------------------------------- keep the conversation while the reader moves between pages
  // sessionStorage: this tab only, gone when the tab closes (the privacy policy says so).
  const KEY = 'tfdChat';
  function save() {
    try { sessionStorage.setItem(KEY, JSON.stringify({ session, history: history.slice(-8), turn, transcript: transcript.slice(-20) })); } catch (e) { /* storage blocked */ }
  }
  function restore() {
    let saved = null;
    try { saved = JSON.parse(sessionStorage.getItem(KEY) || 'null'); } catch (e) { /* storage blocked or corrupt */ }
    if (!saved || !Array.isArray(saved.transcript)) return;
    session = typeof saved.session === 'string' ? saved.session : session;
    turn = Number(saved.turn) || 0;
    (Array.isArray(saved.history) ? saved.history : []).forEach(t => history.push(t));
    saved.transcript.forEach(entry => {
      transcript.push(entry);
      if (entry.who === 'user') bubble('user').textContent = entry.text;
      else renderReply(bubble('bot'), entry.reply);
    });
    if (transcript.length) starters.hidden = true;
  }

  // ---------------------------------------------------------------- ask
  async function ask(raw) {
    const question = raw.trim().slice(0, MAX);
    if (!question || busy) return;
    busy = true;
    send.disabled = true;
    starters.hidden = true;
    input.value = '';
    bubble('user').textContent = question;
    transcript.push({ who: 'user', text: question });
    const box = bubble('bot');
    box.setAttribute('aria-busy', 'true');
    box.appendChild(el('p', 'chat-wait', 'Looking through TechForDad’s articles…'));
    turn += 1;
    track('chat_question', { chat_turn: turn });
    const started = Date.now();

    let data = null, status = 0;
    try {
      const res = await fetch(API, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ question, history: history.slice(-8), page: location.pathname, country, session }),
      });
      status = res.status;
      if (res.headers.get('content-type') && res.headers.get('content-type').includes('application/json')) data = await res.json();
    } catch (e) { /* offline or blocked: handled below */ }

    const mode = status === 200 && data ? data.mode : status === 429 ? 'slow_down' : 'unavailable';
    let reply;
    if (mode === 'ai' && data.answer) {
      reply = { mode, text: data.answer, products: data.products || [], links: data.sources || [], linksTitle: 'Read more on TechForDad:', id: data.id };
      history.push({ role: 'user', content: question }, { role: 'assistant', content: data.answer });
    } else if (mode === 'no_match') {
      reply = { mode, text: data.answer, links: await search(question), linksTitle: 'These articles might still help:', id: data.id };
    } else if (mode === 'slow_down') {
      reply = { mode, text: 'That was a lot of questions in a short time. Please wait a minute, then try again.' };
    } else {
      const found = data && data.sources && data.sources.length ? data.sources : await search(question);
      reply = { mode, text: 'The AI helper is resting right now, so here is a quick search of the site instead.',
        links: found, linksTitle: 'These TechForDad articles look like a match:', browse: !found.length };
    }
    box.replaceChildren();
    box.removeAttribute('aria-busy');
    renderReply(box, reply);
    transcript.push({ who: 'bot', reply });
    save();
    track('chat_answer', { chat_mode: mode, source_count: (data && data.sources || []).length,
      product_count: (data && data.products || []).length, latency_ms: Date.now() - started });
    log.scrollTop = Math.max(0, box.offsetTop - log.offsetTop - 8);  // start of the answer, not its end
    busy = false;
    send.disabled = false;
    input.focus();
  }

  restore();
  window.TFDChat = { open: open, close: hide };
})();
