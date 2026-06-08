// Ep 1 playthrough — drives the real script end-to-end on staging, headless, to surface bugs
// BEFORE a human records. Square -> sign up (fresh +alias) -> land in Workshop -> menu loads.
// Captures console errors + 4xx/5xx + screenshots. Usage: node tests/e2e/ep01-playthrough.js
const puppeteer = require('puppeteer');
const fs = require('fs');

const SQUARE = 'https://staging.lapiazza.app';
const BOTTEGA = 'https://staging-bottega.lapiazza.app';
const STAMP = Date.now();
const EMAIL = `angel.kenel+ep${STAMP}@gmail.com`;
const NAME = 'Ep One Tester';
const PASS = 'helix_pass';
const ABOUT = 'I fix old motorbikes and love to cook — testing the one-motion signup.';
const SHOTS = '/tmp/ep1shots';
fs.mkdirSync(SHOTS, { recursive: true });

const out = [], errors = [], bad = [];
const step = (ok, m) => { const s = `${ok ? '✅' : '❌'} ${m}`; out.push(s); console.log(s); };

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('response', r => { if (r.status() >= 400 && r.url().includes('lapiazza')) bad.push(`${r.status()} ${r.request().method()} ${r.url().replace(/https:\/\/[^/]+/, '')}`); });
  const shot = async n => { try { await page.screenshot({ path: `${SHOTS}/${n}.png` }); } catch (e) {} };

  try {
    await page.goto(SQUARE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
    await shot('1-square'); step(true, 'Square home loaded');

    await page.goto(BOTTEGA + '/get-started', { waitUntil: 'networkidle2', timeout: 30000 });
    await page.type('input[placeholder="Flora Ferrara"]', NAME, { delay: 25 });
    await page.type('input[placeholder="you@example.com"]', EMAIL, { delay: 15 });
    await page.type('input[placeholder="at least 6 characters"]', PASS, { delay: 20 });
    await page.type('textarea[placeholder*="cook with"]', ABOUT, { delay: 8 });
    await shot('2-filled');
    await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => /build my bottega/i.test(x.textContent)); if (b) b.click(); });
    step(true, `Submitted signup as ${EMAIL}`);

    await page.waitForFunction(() => location.pathname.includes('/compute/bottega') || /Welcome,/.test(document.body.innerText), { timeout: 45000 });
    await shot('3-after-submit');
    await page.waitForFunction(() => location.pathname.includes('/compute/bottega'), { timeout: 30000 }).catch(() => {});
    if (!page.url().includes('/compute/bottega')) {
      await page.evaluate(() => { const a = [...document.querySelectorAll('a')].find(x => /enter your bottega/i.test(x.textContent)); if (a) a.click(); });
      await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 }).catch(() => {});
    }
    step(page.url().includes('/compute/bottega'), `Landed in the Workshop`);

    const menuOk = await page.waitForFunction(
      () => { try { const t = document.body ? document.body.innerText : ''; return /Find Your Edge/i.test(t) && !/loading menu/i.test(t); } catch (e) { return false; } },
      { timeout: 25000, polling: 500 }).then(() => true).catch(() => false);
    await shot('4-workshop');
    step(menuOk, menuOk ? 'Recipe MENU loaded for the fresh signup ✅ (role bug fixed end-to-end)' : 'Recipe menu did NOT load — still broken');
  } catch (e) {
    step(false, 'Playthrough threw: ' + e.message); await shot('error');
  }

  console.log(`\n=== CONSOLE ERRORS (${errors.length}) ===`); errors.slice(0, 10).forEach(e => console.log('  ' + e.slice(0, 150)));
  console.log(`=== 4xx/5xx (${bad.length}) ===`); [...new Set(bad)].slice(0, 15).forEach(b => console.log('  ' + b));
  console.log('\n=== SUMMARY ==='); out.forEach(l => console.log(l));
  console.log('screenshots:', SHOTS);
  await browser.close();
})();
