#!/usr/bin/env node
/* Capture the MANAGER edit screen — log in as Ralph, open the catalogue, open the cream's
 * edit form (photo, specs, cost, reorder). The centerpiece of #04 "Make It Proper". */
const puppeteer = require('puppeteer');
const BASE = 'https://sandbox-banco.lapiazza.app';
const USER = process.env.CAP_USER || 'ralph';
const PASS = 'helix_pass';
const OUT = '/home/angel/repos/helixnet/videos/banco/born-once-04-make-it-proper/assets/shots';
require('fs').mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const shot = (p, n) => p.screenshot({ path: `${OUT}/${n}.png` }).then(() => console.log('  shot:', n));

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox', '--hide-scrollbars'] });
  const page = await b.newPage();
  await page.setViewport({ width: 432, height: 768, deviceScaleFactor: 2.5 });
  await page.goto(`${BASE}/pos`, { waitUntil: 'networkidle2', timeout: 45000 });
  await sleep(1200);
  await page.evaluate(() => { const e = [...document.querySelectorAll('a,button')].find(x => x.innerText.trim() === 'Login'); if (e) e.click(); });
  await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 45000 }).catch(() => {});
  await sleep(1200);
  if (await page.$('#username')) {
    await page.type('#username', USER, { delay: 25 });
    await page.type('#password', PASS, { delay: 25 });
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle2' }).catch(() => {}), page.click('#kc-login, button[type=submit]')]);
    await sleep(2500);
  }
  console.log('  logged in as', USER, '->', page.url());

  await page.goto(`${BASE}/pos/catalog`, { waitUntil: 'networkidle2', timeout: 30000 }).catch(() => {});
  await sleep(2000);
  await shot(page, 'edit-01-catalog-ralph');

  // open the cream's product (click the HempSana row/card)
  const opened = await page.evaluate(() => {
    const el = [...document.querySelectorAll('div,li,a,button,h3,h4,span')].find(e => e.innerText && e.innerText.includes('HempSana'));
    if (el) { (el.closest('[role=button],button,a,li,div') || el).click(); return true; }
    return false;
  });
  console.log('  opened product:', opened);
  await sleep(2000);
  await shot(page, 'edit-02-product');
  const fields = await page.evaluate(() => ({
    buttons: [...document.querySelectorAll('button,a')].map(e => e.innerText.trim()).filter(Boolean).slice(0, 30),
    inputs: [...document.querySelectorAll('input,textarea,select')].map(e => (e.placeholder || e.name || e.id || e.type)).slice(0, 30),
  }));
  console.log('  fields:', JSON.stringify(fields));

  // try to reach an explicit Edit form
  if (await page.evaluate(() => { const e = [...document.querySelectorAll('button,a')].find(x => /edit/i.test(x.innerText)); if (e) { e.click(); return true; } return false; })) {
    await sleep(1800); await shot(page, 'edit-03-editform');
  }
  await b.close();
  console.log('done');
})();
