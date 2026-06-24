#!/usr/bin/env node
/* #07 The Drawer — capture the cash-shift screens: My Drawer, open float, close/count-out
 * (expected vs counted vs variance), daily log. Login as pam. */
const puppeteer = require('puppeteer');
const BASE = 'https://sandbox-banco.lapiazza.app';
const OUT = '/home/angel/repos/helixnet/videos/banco/born-once-07-drawer-that-wouldnt-close/assets/shots';
require('fs').mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const shot = (p, n) => p.screenshot({ path: `${OUT}/${n}.png` }).then(() => console.log('  shot:', n));
const clickText = (p, t) => p.evaluate((t) => {
  const els = [...document.querySelectorAll('a,button,div,span,li,h3,h4')];
  const el = els.find(e => e.innerText && e.innerText.trim() === t) || els.find(e => e.innerText && e.innerText.includes(t));
  if (el) { (el.closest('button,a,[role=button]') || el).click(); return true; } return false;
}, t);

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox', '--hide-scrollbars'] });
  const page = await b.newPage();
  await page.setViewport({ width: 432, height: 768, deviceScaleFactor: 2.5 });
  await page.goto(`${BASE}/pos`, { waitUntil: 'networkidle2', timeout: 45000 }); await sleep(1200);
  await page.evaluate(() => { const e = [...document.querySelectorAll('a,button')].find(x => x.innerText.trim() === 'Login'); if (e) e.click(); });
  await page.waitForNavigation({ waitUntil: 'networkidle2' }).catch(() => {}); await sleep(1200);
  if (await page.$('#username')) {
    await page.type('#username', 'pam', { delay: 25 }); await page.type('#password', 'helix_pass', { delay: 25 });
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle2' }).catch(() => {}), page.click('#kc-login, button[type=submit]')]); await sleep(2800);
  }
  console.log('  ->', page.url());
  await shot(page, 'dash');
  console.log('  nav:', JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('a,button')].map(e => e.innerText.trim().replace(/\n/g, ' ')).filter(Boolean).slice(0, 25))));

  for (const route of ['/pos/drawer', '/pos/shift', '/pos/cash', '/pos/my-drawer', '/pos/cashup']) {
    try { const r = await page.goto(`${BASE}${route}`, { waitUntil: 'networkidle2', timeout: 15000 });
      console.log(`  ${route} -> ${r.status()} ${page.url()}`);
      if (r.status() < 400 && !page.url().endsWith('/dashboard')) { await sleep(1500); await shot(page, 'rt-' + route.split('/').pop()); }
    } catch (e) { console.log(`  ${route} err`); }
  }
  // from dashboard, click the drawer area
  await page.goto(`${BASE}/pos/dashboard`, { waitUntil: 'networkidle2', timeout: 20000 }).catch(() => {}); await sleep(1500);
  for (const label of ['My Drawer', 'expected in drawer', 'Drawer', 'Close Shift', 'Open it to take']) {
    if (await clickText(page, label)) { console.log('  clicked:', label); await sleep(2000); await shot(page, 'drw-' + label.split(' ')[0].toLowerCase()); break; }
  }
  console.log('  after-click nav:', JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('a,button')].map(e => e.innerText.trim().replace(/\n/g, ' ')).filter(Boolean).slice(0, 25))));
  await b.close(); console.log('done');
})();
