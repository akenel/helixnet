#!/usr/bin/env node
/* Born Once #15 "The Snag" — capture the BEFORE state of Transaction History
 * (felix, sandbox = still the old no-export build). Grabs the list+totals and the
 * toolbar where an export button SHOULD be and isn't. Portrait 1080x1920, no chrome. */
const puppeteer = require('puppeteer');
const fs = require('fs');

const BASE = 'https://sandbox-banco.lapiazza.app';
const USER = 'felix', PASS = 'helix_pass';
const OUT = '/home/angel/repos/helixnet/videos/banco/Season 3 - Never Alone/born-once-15-the-snag/assets/shots';
fs.mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const shot = async (page, name, opts={}) => { await page.screenshot({ path: `${OUT}/${name}.png`, ...opts }); console.log('  shot:', name); };

(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox','--disable-setuid-sandbox','--hide-scrollbars'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 432, height: 768, deviceScaleFactor: 2.5 });

  await page.goto(`${BASE}/pos`, { waitUntil: 'networkidle2', timeout: 45000 });
  await sleep(1500);
  await page.evaluate(() => { const t=[...document.querySelectorAll('a,button')].find(e=>e.innerText.trim()==='Login'); if(t)t.click(); });
  await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 45000 }).catch(()=>{});
  await sleep(1200);
  if (await page.$('#username')) {
    await page.type('#username', USER, { delay: 25 });
    await page.type('#password', PASS, { delay: 25 });
    await Promise.all([ page.waitForNavigation({ waitUntil:'networkidle2', timeout:45000 }).catch(()=>{}), page.click('#kc-login, button[type=submit], input[type=submit]') ]);
    await sleep(2500);
  }
  console.log('  after login url:', page.url());

  // Transaction History
  await page.goto(`${BASE}/pos/transactions`, { waitUntil: 'networkidle2', timeout: 30000 }).catch(()=>{});
  await sleep(2800);
  await shot(page, 'debug-tx-top');
  console.log('  title:', await page.title());
  // how many rows / is there data?
  const info = await page.evaluate(() => ({
    rows: document.querySelectorAll('table tbody tr, [class*="card"]').length,
    hasReset: [...document.querySelectorAll('button')].some(b=>/Reset Filters/.test(b.innerText)),
    hasExport: [...document.querySelectorAll('button')].some(b=>/CSV|Print/.test(b.innerText)),
    totals: ([...document.querySelectorAll('*')].find(e=>/Total Sales/.test(e.innerText)) ? 'present' : 'none'),
  }));
  console.log('  page info:', JSON.stringify(info));

  // Beat 1 — the list + totals (top of page)
  await page.evaluate(() => window.scrollTo(0,0)); await sleep(500);
  await shot(page, 'tx-01-list-top');
  // Beat 2 — full page (the whole report, for a tall pan)
  await shot(page, 'tx-02-fullpage', { fullPage: true });
  // Beat 3 — focus the filter card's action row (the "no button" — only Reset Filters there)
  const box = await page.evaluate(() => {
    const b=[...document.querySelectorAll('button')].find(e=>/Reset Filters/.test(e.innerText));
    if(!b) return null; const r=b.closest('.card')?.getBoundingClientRect()||b.getBoundingClientRect();
    return {x:Math.max(0,r.x),y:Math.max(0,r.y),w:r.width,h:r.height};
  });
  if (box) { await page.evaluate(y=>window.scrollTo(0,y), Math.max(0,box.y-40)); await sleep(500); await shot(page,'tx-03-toolbar-nobutton'); }

  await browser.close();
  console.log('done');
})();
