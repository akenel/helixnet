// Ep 2 playthrough — "Ask the Neighbourhood" (the Help Board). Headless bug-hunt before recording.
// Log in as Mike -> Help Board loads -> post a NEED -> it appears -> open a post (replies show).
// Usage: node tests/e2e/ep02-playthrough.js
const puppeteer = require('puppeteer');
const fs = require('fs');

const SQUARE = 'https://staging.lapiazza.app';
const STAMP = Date.now();
const TITLE = `Need Help Moving a Garage - 20 hands for a crane [${String(STAMP).slice(-5)}]`;
const SHOTS = '/tmp/ep2shots';
fs.mkdirSync(SHOTS, { recursive: true });

const out = [], errors = [], bad = [];
const step = (ok, m) => { const s = `${ok ? '✅' : '❌'} ${m}`; out.push(s); console.log(s); };

(async () => {
  const browser = await puppeteer.launch({ headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('response', r => { if (r.status() >= 400 && r.url().includes('lapiazza')) bad.push(`${r.status()} ${r.request().method()} ${r.url().replace(/https:\/\/[^/]+/, '')}`); });
  const shot = async n => { try { await page.screenshot({ path: `${SHOTS}/${n}.png` }); } catch (e) {} };

  try {
    // 1. log in as Mike (demo ROPC -> bh_session cookie)
    await page.goto(SQUARE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
    const login = await page.evaluate(async () => {
      const r = await fetch('/api/v1/demo/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'mike' }) });
      return { status: r.status, body: await r.text() };
    });
    step(login.status === 200, `Logged in as Mike (demo ROPC ${login.status})`);

    // 2. Help Board loads
    await page.goto(SQUARE + '/helpboard', { waitUntil: 'networkidle2', timeout: 30000 });
    const boardOk = await page.waitForFunction(
      () => { try { const t = document.body.innerText; return /help|need|offer|ask/i.test(t) && !/loading/i.test(t.slice(0, 50)); } catch (e) { return false; } },
      { timeout: 20000, polling: 400 }).then(() => true).catch(() => false);
    await shot('1-board'); step(boardOk, 'Help Board page loaded');

    // 3. post a NEED (the teaching beat: ask the neighbourhood)
    const created = await page.evaluate(async (title) => {
      const r = await fetch('/api/v1/helpboard/posts', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ help_type: 'need', title, category: 'moving', urgency: 'urgent',
          body: "Moving my whole garage before a relocation - there's a 1000-lb car crane that needs about 20 hands to lift safely. Fit folks welcome. Saturday. Cookies provided." })
      });
      return { status: r.status, body: (await r.text()).slice(0, 200) };
    }, TITLE);
    step(created.status === 201, `Posted the NEED (${created.status})` + (created.status !== 201 ? ' -> ' + created.body : ''));

    // 4. it appears on the board
    await page.goto(SQUARE + '/helpboard', { waitUntil: 'networkidle2', timeout: 30000 });
    const appears = await page.waitForFunction(
      (frag) => { try { return document.body.innerText.includes(frag); } catch (e) { return false; } },
      { timeout: 15000, polling: 400 }, String(STAMP).slice(-5)).then(() => true).catch(() => false);
    await shot('2-posted'); step(appears, 'The new post shows on the board');

    // 5. open a post -> detail + replies
    await page.evaluate(() => { const c = document.querySelector('[\\@click^="openPost"], .cursor-pointer'); if (c) c.click(); });
    const detailOk = await page.waitForFunction(
      () => { try { return /reply|replies|I need help|I can help/i.test(document.body.innerText); } catch (e) { return false; } },
      { timeout: 12000, polling: 400 }).then(() => true).catch(() => false);
    await shot('3-detail'); step(detailOk, 'Opened a post (detail + replies render)');
  } catch (e) {
    step(false, 'Playthrough threw: ' + e.message); await shot('error');
  }

  console.log(`\n=== CONSOLE ERRORS (${errors.length}) ===`); errors.slice(0, 10).forEach(e => console.log('  ' + e.slice(0, 150)));
  console.log(`=== 4xx/5xx (${bad.length}) ===`); [...new Set(bad)].slice(0, 15).forEach(b => console.log('  ' + b));
  console.log('\n=== SUMMARY ==='); out.forEach(l => console.log(l));
  console.log('screenshots:', SHOTS);
  await browser.close();
})();
