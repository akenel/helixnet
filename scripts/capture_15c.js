#!/usr/bin/env node
/* #15 — re-grab the three beats that need scrolling, via scrollIntoView (robust).
 * summary (Total Sales), the sale rows, and the Reset-Filters row (the "no button"). */
const puppeteer = require('puppeteer');
const BASE = 'https://sandbox-banco.lapiazza.app';
const OUT = '/home/angel/repos/helixnet/videos/banco/Season 3 - Never Alone/born-once-15-the-snag/assets/shots';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox','--disable-setuid-sandbox','--hide-scrollbars'] });
  const p = await b.newPage();
  await p.setViewport({ width: 432, height: 768, deviceScaleFactor: 2.5 });
  await p.goto(`${BASE}/pos`, { waitUntil: 'networkidle2', timeout: 45000 }); await sleep(1500);
  await p.evaluate(() => { const t=[...document.querySelectorAll('a,button')].find(e=>e.innerText.trim()==='Login'); if(t)t.click(); });
  await p.waitForNavigation({ waitUntil:'networkidle2', timeout:45000 }).catch(()=>{}); await sleep(1200);
  await p.type('#username','felix',{delay:25}); await p.type('#password','helix_pass',{delay:25});
  await Promise.all([ p.waitForNavigation({waitUntil:'networkidle2',timeout:45000}).catch(()=>{}), p.click('#kc-login, button[type=submit]') ]); await sleep(2500);
  await p.goto(`${BASE}/pos/transactions`, { waitUntil:'networkidle2', timeout:30000 }).catch(()=>{}); await sleep(3000);

  // kind: 'summary' | 'rows' | 'reset' — find the element with plain JS, scroll it to center.
  const grab = async (kind, name) => {
    const ok = await p.evaluate((kind) => {
      let el = null;
      if (kind === 'summary') {
        el = [...document.querySelectorAll('div.card')].find(c => /Total Sales/.test(c.textContent));
      } else if (kind === 'rows') {
        el = document.querySelector('.md\\:hidden .card') || document.querySelector('table tbody tr');
      } else if (kind === 'reset') {
        el = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Reset Filters');
      }
      if (!el) return false;
      el.scrollIntoView({ block: 'center', inline: 'nearest' });
      return true;
    }, kind);
    await sleep(700);
    await p.screenshot({ path: `${OUT}/${name}.png` });
    console.log('  ', name, 'found:', ok);
  };

  await grab('summary', 'tx-04-summary');
  await grab('rows',    'tx-05-rows');
  await grab('reset',   'tx-03-toolbar-nobutton');
  await b.close(); console.log('done');
})();
