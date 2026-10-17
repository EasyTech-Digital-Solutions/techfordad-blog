// Unit tests for the chat Worker with fake Cloudflare bindings. Run: node --test worker/test/
// (tests/test_chat.py runs this as part of the suite.)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import worker, { scrub, stripForeignLinks, productsFor, mentioned, withSafetyLines } from '../src/index.js';

const ORIGIN = 'https://www.techfordad.com';
const CHUNK = {
  url: '/blog/best-tablets-for-seniors.html#ipad', title: 'Best Tablets for Seniors', section: 'iPad',
  country: 'US', text: 'Best Tablets for Seniors - iPad\nThe iPad is the easiest tablet for most seniors.', hash: 'x',
  products: JSON.stringify([
    { name: 'Apple iPad (11th Generation)', url: 'https://www.amazon.com/dp/B0IPAD' },
    { name: 'Amazon Fire HD 10', url: 'https://www.amazon.com/dp/B0FIRE' },
  ]),
};
const CA_CHUNK = {
  ...CHUNK, country: 'CA',
  products: JSON.stringify([{ name: 'Apple iPad (11th Generation)', url: 'https://www.amazon.ca/dp/B0IPADCA' }]),
};

function fakeEnv({ matches = [{ score: 0.8, metadata: CHUNK }], answer = 'The iPad is the easiest pick.', aiError = null, embedError = null } = {}) {
  const calls = { models: [], sql: [] };
  return {
    calls,
    env: {
      CHAT_MODEL: 'test-model',
      MIN_SCORE: '0.6',
      AI: {
        async run(model, input) {
          calls.models.push({ model, input });
          if (model.includes('bge')) {
            if (embedError) throw new Error(embedError);
            return { data: [[0.1, 0.2]] };
          }
          if (aiError) throw new Error(aiError);
          return { response: answer };
        },
      },
      VECTORIZE: { async query() { return { matches }; } },
      DB: {
        prepare(sql) {
          return { bind: (...args) => ({ run: async () => { calls.sql.push({ sql, args }); } }) };
        },
      },
    },
  };
}

async function call(env, body, { origin = ORIGIN, path = '/api/chat' } = {}) {
  const waits = [];
  const req = new Request('https://www.techfordad.com' + path, {
    method: 'POST', headers: { 'content-type': 'application/json', origin }, body: JSON.stringify(body),
  });
  const res = await worker.fetch(req, env, { waitUntil: p => waits.push(p) });
  await Promise.all(waits);
  return { status: res.status, data: await res.json() };
}

test('rejects other websites', async () => {
  const { env } = fakeEnv();
  const r = await call(env, { question: 'hi' }, { origin: 'https://evil.example' });
  assert.equal(r.status, 403);
});

test('rejects empty and over-long questions', async () => {
  const { env } = fakeEnv();
  assert.equal((await call(env, { question: '  ' })).status, 400);
  assert.equal((await call(env, { question: 'x'.repeat(501) })).status, 413);
});

test('answers from the excerpts and returns our article as the source', async () => {
  const { env, calls } = fakeEnv();
  const r = await call(env, { question: 'Which tablet is easiest?', country: 'US', page: '/blog/x.html' });
  assert.equal(r.status, 200);
  assert.equal(r.data.mode, 'ai');
  assert.equal(r.data.answer, 'The iPad is the easiest pick.');
  assert.deepEqual(r.data.sources, [{ title: CHUNK.title, url: CHUNK.url }]);
  const chatCall = calls.models.find(c => c.model === 'test-model');
  assert.match(chatCall.input.messages[0].content, /EXCERPTS:[\s\S]*easiest tablet for most seniors/);
  assert.equal(calls.sql.length, 1, 'the chat is logged');
});

test('Check Price buttons only for products the answer names, with the US tag', async () => {
  const { env } = fakeEnv();
  const r = await call(env, { question: 'Which tablet?', country: 'US', page: '/blog/best-tablets-for-seniors.html' });
  assert.deepEqual(r.data.products, [{ name: 'Apple iPad (11th Generation)', url: 'https://www.amazon.com/dp/B0IPAD?tag=techfordad0b-20' }]);
});

test('affiliate tag and store follow the page the chat is open on', () => {
  const answer = 'The iPad is the easiest. The Fire HD 10 is cheaper.';
  const us = productsFor([CHUNK, CA_CHUNK], answer, '/blog/x.html', 'US');
  assert.deepEqual(us.map(p => p.url), ['https://www.amazon.com/dp/B0IPAD?tag=techfordad0b-20', 'https://www.amazon.com/dp/B0FIRE?tag=techfordad0b-20']);
  const ca = productsFor([CHUNK, CA_CHUNK], answer, '/blog/x-canada.html', 'CA');
  assert.deepEqual(ca.map(p => p.url), ['https://www.amazon.ca/dp/B0IPADCA?tag=abhikar91-20'], 'Canada pages get amazon.ca only');
  const gifts = productsFor([CHUNK], answer, '/gift-guides/tech-gifts.html', 'US');
  assert.ok(gifts.every(p => p.url.endsWith('tag=techfordad-gifts-20')), 'gift guides keep their own tag');
});

test('no buttons for products the answer does not name, or links to other stores', () => {
  const bad = { ...CHUNK, products: JSON.stringify([{ name: 'Apple iPad (11th Generation)', url: 'https://evil.example/dp/1' }]) };
  assert.deepEqual(productsFor([bad], 'The iPad is good.', '/blog/x.html', 'US'), []);
  assert.deepEqual(productsFor([CHUNK], 'Try a large-button phone.', '/blog/x.html', 'US'), []);
  assert.ok(mentioned('Samsung Galaxy Tab A9+', 'the Galaxy Tab A9+ is a good pick'));
  assert.ok(!mentioned('Apple iPad (11th Generation)', 'an Android tablet'));
});

test('off-topic question gets a fixed reply without calling the chat model', async () => {
  const { env, calls } = fakeEnv({ matches: [{ score: 0.3, metadata: CHUNK }] });
  const r = await call(env, { question: 'Write my homework essay' });
  assert.equal(r.data.mode, 'no_match');
  assert.ok(!calls.models.some(c => c.model === 'test-model'));
});

test('daily allowance used up: says so, so the page can fall back to search', async () => {
  const { env } = fakeEnv({ embedError: '4006: you have used up your daily free allocation of 10,000 neurons' });
  const r = await call(env, { question: 'Which tablet?' });
  assert.equal(r.status, 200);
  assert.equal(r.data.mode, 'limit');
});

test('personal details are removed before the model sees them or they are stored', async () => {
  const { env, calls } = fakeEnv();
  await call(env, { question: 'My dad bob@example.com at 416-555-1234 in M5V 2T6 needs a tablet' });
  const sent = JSON.stringify(calls.models) + JSON.stringify(calls.sql);
  assert.ok(!sent.includes('bob@example.com') && !sent.includes('555-1234') && !sent.includes('M5V'), sent);
});

test('links to other websites are removed from answers', () => {
  const out = stripForeignLinks('Buy it at https://www.amazon.com/dp/B0X?tag=bad or amazon.ca/dp/123 and read https://www.techfordad.com/blog/a.html');
  assert.ok(!/amazon/.test(out), out);
  assert.ok(out.includes('https://www.techfordad.com/blog/a.html'));
});

test('scrub keeps ordinary prices and model numbers', () => {
  assert.equal(scrub('About $499 for the Galaxy A36'), 'About $499 for the Galaxy A36');
});

test('feedback is recorded', async () => {
  const { env, calls } = fakeEnv();
  const r = await call(env, { id: 'abc', helpful: true }, { path: '/api/chat/feedback' });
  assert.equal(r.status, 200);
  assert.match(calls.sql[0].sql, /UPDATE chats SET helpful/);
});

test('an emergency gets 911 first, even when no article matches', async () => {
  const { env } = fakeEnv({ matches: [{ score: 0.3, metadata: CHUNK }] });
  const r = await call(env, { question: "My dad fell and can't get up, what do I do?" });
  assert.equal(r.data.mode, 'no_match');
  assert.match(r.data.answer, /^If someone is hurt or in danger right now, call 911/);
  const ai = await call(fakeEnv({ answer: 'A medical alert pendant can help next time.' }).env, { question: 'My mom fell, what should I buy?' });
  assert.match(ai.data.answer, /^If someone is hurt[\s\S]*medical alert pendant/);
});

test('health answers always end with ask their doctor', () => {
  assert.match(withSafetyLines('What blood pressure reading is too high?', 'Above 180/120 is a crisis.'), /180\/120[\s\S]*Ask their doctor/);
  assert.equal(withSafetyLines('Is hearing loss normal?', 'Ask your audiologist.'), 'Ask your audiologist.', 'no duplicate when the model already says it');
  assert.equal(withSafetyLines('Which tablet is easiest?', 'The iPad.'), 'The iPad.', 'no health line on product questions');
});

test('asked whether TechForDad tested something, the answer says plainly that it does not test products', () => {
  const out = withSafetyLines('Did you test the Apple Watch fall detection yourselves?',
    "I couldn't find that on TechForDad. The article says Apple says it turns on automatically for people 55 or older.");
  assert.match(out, /^TechForDad does not test products itself\./);
  assert.ok(!/couldn't find/.test(out), out);
  assert.ok(!/medical advice/.test(out), 'fall detection is a product feature, not a health question');
  assert.equal(withSafetyLines('Have you tried the Jitterbug?', 'TechForDad does not test products. The article says...'),
    'TechForDad does not test products. The article says...', 'no duplicate when the model already says it');
  assert.equal(withSafetyLines('Which tablet is easiest?', 'The iPad.'), 'The iPad.');
  assert.match(withSafetyLines('My mom fell, does fall detection help?', 'Yes.'), /Ask their doctor/, 'a real fall still gets the health line');
});
