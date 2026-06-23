#!/usr/bin/env node
/* #05 The Delivery — capture receiving + box-split screens. Login as Ralph, find the
 * receiving flow, and the "bought a box? split it" feature on the sale screen. */
const puppeteer = require('puppeteer');
const BASE = 'https://sandbox-banco.lapiazza.app';
const PASS = 'helix_pass';
const OUT = '/home/angel/repos/helixnet/videos/banco/born-once-05-the-delivery/assets/shots';
require('fs').mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const shot = (p, n) => p.screenshot({ path: `${OUT}/${n}.png` }).then(() => console.log('  shot:', n));
const clickText = (p, t) => p.evaluate((t) => {
  const els = [...document.querySelectorAll('a,button,div,span,li,h3,h4')];
  const el = els.find(e => e.innerText && e.innerText.trim() === t)
          || els.find(e => e.innerText && e.innerText.includes(t));
  if (el) { (el.closest('button,a,[role=button]') || el).click(); return true; } return false;
}, t);

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox', '--hide-scrollbars'] });
  const page = await b.newPage();
  await page.setViewport({ width: 432, height: 768, deviceScaleFactor: 2.5 });
  await page.goto(`${BASE}/pos`, { waitUntil: 'networkidle2', timeout: 45000 });
  await sleep(1200);
  await page.evaluate(() => { const e = [...document.querySelectorAll('a,button')].find(x => x.innerText.trim() === 'Login'); if (e) e.click(); });
  await page.waitForNavigation({ waitUntil: 'networkidle2' }).catch(() => {}); await sleep(1200);
  if (await page.$('#username')) {
    await page.type('#username', 'ralph', { delay: 25 }); await page.type('#password', PASS, { delay: 25 });
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle2' }).catch(() => {}), page.click('#kc-login, button[type=submit]')]); await sleep(2500);
  }
  console.log('  logged in ->', page.url());

  // dump nav to find receiving
  const nav = await page.evaluate(() => [...document.querySelectorAll('a,button')].map(e => e.innerText.trim()).filter(Boolean).slice(0, 40));
  console.log('  nav:', JSON.stringify(nav));

  // try receiving routes
  for (const route of ['/pos/receiving', '/pos/receive', '/pos/goods-in', '/pos/deliveries']) {
    try {
      const r = await page.goto(`${BASE}${route}`, { waitUntil: 'networkidle2', timeout: 15000 });
      console.log(`  ${route} -> ${r.status()} ${page.url()}`);
      if (r.status() < 400 && page.url().includes(route.split('/').pop())) { await sleep(1500); await shot(page, 'rcv-' + route.split('/').pop()); }
    } catch (e) { console.log(`  ${route} err`); }
  }

  // box-split on the sale screen
  await page.goto(`${BASE}/pos`, { waitUntil: 'networkidle2', timeout: 30000 }).catch(() => {}); await sleep(1200);
  await clickText(page, 'New Sale'); await sleep(2000);
  await shot(page, 'sale');
  const split = await clickText(page, 'bought a box');
  console.log('  box-split clicked:', split); await sleep(1500);
  await shot(page, 'box-split');
  await b.close(); console.log('done');
})();
