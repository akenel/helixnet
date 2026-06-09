// Dream Weavers regression — the episodes' critical flows as assertions. The story IS the test.
// Exits non-zero if any flow breaks -> used as the BLOCKING gate before a prod deploy.
// Target via env: SQUARE / BOTTEGA (default: staging). Usage: node tests/e2e/dream-weavers-regression.js
const puppeteer = require('puppeteer');

const SQUARE = process.env.SQUARE || 'https://staging.lapiazza.app';
const BOTTEGA = process.env.BOTTEGA || 'https://staging-bottega.lapiazza.app';
const EVENT_ITEM = 'garage-moving-day-tool-sale-trapani';

let pass = 0; const fails = [];
const ok = (cond, name) => { if (cond) { pass++; console.log('  ✅ ' + name); } else { fails.push(name); console.log('  ❌ ' + name); } };

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors'] });
  const page = await b.newPage();
  await page.setViewport({ width: 1280, height: 800 });
  // skip the cookie/install banners AND the 18+ gate for the flows that need to reach content
  await page.evaluateOnNewDocument(() => { try { localStorage.setItem('cookie_consent', 'accepted'); localStorage.setItem('pwa_install_dismissed', '1'); localStorage.setItem('age18_confirmed', '1'); } catch (e) {} });

  try {
    console.log('— pages load —');
    for (const [name, url] of [['Square home', SQUARE + '/'], ['Bottega workshop', BOTTEGA + '/compute/bottega'], ['Help Board', SQUARE + '/helpboard']]) {
      const r = await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 }).catch(() => null);
      ok(r && r.status() < 400, `${name} loads (${r ? r.status() : 'ERR'})`);
    }

    console.log('— Ep 1: signup -> workshop menu (the role-bug regression) —');
    await page.goto(BOTTEGA + '/get-started', { waitUntil: 'networkidle2', timeout: 30000 });
    await page.type('input[placeholder="Flora Ferrara"]', 'Regression Bot', { delay: 4 });
    await page.type('input[placeholder="you@example.com"]', `angel.kenel+reg${Date.now()}@gmail.com`, { delay: 3 });
    await page.type('input[placeholder="at least 6 characters"]', 'helix_pass', { delay: 4 });
    await page.type('textarea[placeholder*="cook with"]', 'Regression user, fixes motorbikes.', { delay: 2 });
    await page.evaluate(() => { const cb = [...document.querySelectorAll('input[type=checkbox]')].find(x => (x.getAttribute('x-model') || '') === 'age16'); if (cb && !cb.checked) cb.click(); });  // 16+ gate
    await page.evaluate(() => { const btn = [...document.querySelectorAll('button')].find(x => /build my bottega/i.test(x.textContent)); if (btn) btn.click(); });
    await page.waitForFunction(() => location.pathname.includes('/compute/bottega') || /Welcome,/.test(document.body.innerText), { timeout: 45000 }).catch(() => {});
    await page.waitForFunction(() => location.pathname.includes('/compute/bottega'), { timeout: 30000 }).catch(() => {});
    const menuOk = await page.waitForFunction(() => { try { const t = document.body.innerText; return /Find Your Edge/i.test(t) && !/loading menu/i.test(t); } catch (e) { return false; } }, { timeout: 25000, polling: 500 }).then(() => true).catch(() => false);
    ok(menuOk, 'Fresh signup lands in Workshop with the menu loaded');

    console.log('— Ep 2/3: help-post create (as Mike) —');
    await page.goto(SQUARE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
    const login = await page.evaluate(() => fetch('/api/v1/demo/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'mike' }) }).then(r => r.status));
    ok(login === 200, `demo-login (mike) works (${login})`);
    const postStatus = await page.evaluate(() => fetch('/api/v1/helpboard/posts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ help_type: 'need', title: 'Regression check post please ignore', category: 'moving', urgency: 'normal', body: 'automated regression' }) }).then(r => r.status));
    ok(postStatus === 201, `Help-post create returns 201 (${postStatus})`);

    console.log('— Ep 9 + age policy: the safety scan + the 18+ gate —');
    const scamStatus = await page.evaluate(() => fetch('/api/v1/helpboard/posts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ help_type: 'offer', title: 'Regression scam check ignore', category: 'moving', urgency: 'normal', body: 'DM me on Telegram @x, join here first https://t.me/x' }) }).then(r => r.status));
    ok(scamStatus === 201, `Funnel post still creates (scan is fail-open) (${scamStatus})`);
    const html18 = await page.evaluate(async (u) => { try { const r = await fetch(u); return await r.text(); } catch (e) { return ''; } }, SQUARE + '/items/' + EVENT_ITEM);
    ok(/age-restricted|age18_confirmed|18 or older/i.test(html18), '18+ gate markup present on age-restricted listing');

    console.log('— Ep 10: who-viewed endpoint mounted + owner-gated —');
    const viewersUnauth = await page.evaluate(async (sq) => { try { const r = await fetch(sq + '/api/v1/items/00000000-0000-0000-0000-000000000000/viewers', { headers: { 'Cookie': '' } }); return r.status; } catch (e) { return 0; } }, SQUARE);
    ok([401, 403, 404].includes(viewersUnauth), `who-viewed endpoint mounted/guarded (${viewersUnauth})`);
  } catch (e) {
    fails.push('regression threw: ' + e.message);
    console.log('  ❌ regression threw: ' + e.message);
  }

  await b.close();
  console.log(`\n════ ${pass} passed, ${fails.length} failed ════`);
  if (fails.length) { console.log('🔴 FAILED: ' + fails.join('; ')); process.exit(1); }
  console.log('🟢 all story flows green');
})();
