#!/usr/bin/env node
/* Born Once #16 "The Button" — drive the REAL feedback widget as felix on sandbox,
 * file Felix's complaint (feeds #17's triage), and shoot: the 💬 button, the open
 * "Send feedback" card, the typed message, and the "Filed as BL-…" confirmation. */
const puppeteer = require('puppeteer');
const fs = require('fs');
const BASE = 'https://sandbox-banco.lapiazza.app', USER = 'felix', PASS = 'helix_pass';
const OUT = '/home/angel/repos/helixnet/videos/banco/Season 3 - Never Alone/born-once-16-the-button/assets/shots';
fs.mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const shot = async (p, n) => { await p.screenshot({ path: `${OUT}/${n}.png` }); console.log('  shot:', n); };

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox','--disable-setuid-sandbox','--hide-scrollbars'] });
  const p = await b.newPage(); await p.setViewport({ width: 432, height: 768, deviceScaleFactor: 2.5 });
  await p.goto(`${BASE}/pos`, { waitUntil:'networkidle2', timeout:45000 }); await sleep(1500);
  await p.evaluate(() => { const t=[...document.querySelectorAll('a,button')].find(e=>e.innerText.trim()==='Login'); if(t)t.click(); });
  await p.waitForNavigation({ waitUntil:'networkidle2', timeout:45000 }).catch(()=>{}); await sleep(1200);
  await p.type('#username', USER, { delay:25 }); await p.type('#password', PASS, { delay:25 });
  await Promise.all([ p.waitForNavigation({waitUntil:'networkidle2',timeout:45000}).catch(()=>{}), p.click('#kc-login, button[type=submit]') ]); await sleep(2500);
  await p.goto(`${BASE}/pos/transactions`, { waitUntil:'networkidle2', timeout:30000 }).catch(()=>{}); await sleep(2800);

  // Beat 1 — the 💬 button in the corner (ensure visible)
  await p.evaluate(() => { const fab=document.querySelector('.lpfb-btn'); if(fab) fab.style.display='flex'; });
  await sleep(400); await shot(p, 'fb-01-button');

  // open the card
  const opened = await p.evaluate(() => { const o=document.querySelector('#lpfb-open'); if(o){o.click();return true;} return false; });
  console.log('  opened card:', opened); await sleep(900);
  await shot(p, 'fb-02-card');

  // Beat 3 — type Felix's complaint in his own words (kind 🐛 Bug + 🟡 Annoying are the defaults)
  await p.type('#lpfb-title', "Can't print my sales", { delay: 35 });
  await p.type('#lpfb-body', "I can see all my sales for the day but there's no way to print the list or save a file for my accountant. Can you add that?", { delay: 12 });
  await sleep(500); await shot(p, 'fb-03-typed');

  // Beat 4 — Send → "Filed as BL-…"
  await p.evaluate(() => { const s=document.querySelector('#lpfb-send'); if(s) s.click(); });
  await sleep(3500);
  const ref = await p.evaluate(() => { const r=document.querySelector('#lpfb-done-ref'); return r ? r.innerText : null; });
  console.log('  filed as:', ref);
  await shot(p, 'fb-04-filed');

  await b.close(); console.log('done');
})();
