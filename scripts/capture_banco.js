#!/usr/bin/env node
/* Born Once — Puppeteer screen capture for the Banco POS.
 * Logs in as Pam, drives the app, screenshots the screens each episode needs,
 * at a portrait viewport (1080x1920) with no browser chrome. First pass: log in
 * and grab home + catalogue + product, with debug shots so we can see the DOM. */
const puppeteer = require('puppeteer');

const BASE = 'https://sandbox-banco.lapiazza.app';
const USER = 'pam', PASS = 'helix_pass';
const OUT = '/home/angel/repos/helixnet/videos/banco/born-once-03-forty-franc-cream/assets/shots';
const fs = require('fs');
fs.mkdirSync(OUT, { recursive: true });

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function shot(page, name) {
  await page.screenshot({ path: `${OUT}/${name}.png` });
  console.log('  shot:', name);
}

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--hide-scrollbars'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 432, height: 768, deviceScaleFactor: 2.5 });

  console.log('goto /pos');
  await page.goto(`${BASE}/pos`, { waitUntil: 'networkidle2', timeout: 45000 });
  await sleep(1500);
  await shot(page, 'debug-01-landing');
  console.log('  title:', await page.title());

  // 1) click the main "Login" control -> triggers Keycloak OIDC redirect
  const clicked = await page.evaluate(() => {
    const els = [...document.querySelectorAll('a,button')];
    const t = els.find(e => e.innerText.trim() === 'Login');
    if (t) { t.click(); return true; }
    return false;
  });
  console.log('  clicked Login:', clicked);
  await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 45000 }).catch(() => {});
  await sleep(1500);
  console.log('  now at:', page.url());
  await shot(page, 'debug-02-keycloak');

  // 2) Keycloak login form
  const kcUser = await page.$('#username') || await page.$('input[name=username]');
  if (kcUser) {
    await page.type('#username', USER, { delay: 25 });
    await page.type('#password', PASS, { delay: 25 });
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 45000 }).catch(() => {}),
      page.click('#kc-login, button[type=submit], input[type=submit]'),
    ]);
    await sleep(2500);
  } else {
    console.log('  !! no keycloak username field found');
  }
  await shot(page, 'debug-03-after-login');
  console.log('  url:', page.url());

  // catalogue (cream + photo)
  await page.goto(`${BASE}/pos/catalog`, { waitUntil: 'networkidle2', timeout: 30000 }).catch(() => {});
  await sleep(2000);
  await shot(page, 'catalog');

  const clickText = async (txt) => page.evaluate((t) => {
    const els = [...document.querySelectorAll('a,button,div,span,li,h3,h4')];
    const el = els.find(e => e.innerText && e.innerText.trim() === t)
            || els.find(e => e.innerText && e.innerText.trim().startsWith(t))
            || els.find(e => e.innerText && e.innerText.includes(t));
    if (el) { (el.closest('button,a,[role=button]') || el).click(); return true; }
    return false;
  }, txt);
  const dump = async () => page.evaluate(() => [...document.querySelectorAll('button,a')]
    .map(e => e.innerText.trim()).filter(Boolean).slice(0, 25));

  // sale flow: New Sale -> find the cream -> tap -> cart
  await page.goto(`${BASE}/pos`, { waitUntil: 'networkidle2', timeout: 30000 }).catch(() => {});
  await sleep(1500);
  console.log('  newsale clicked:', await clickText('New Sale'));
  await sleep(2500); await shot(page, 'sale-01-newsale');
  console.log('  buttons:', JSON.stringify(await dump()));

  // add the cream to the cart via its real barcode (bulletproof)
  const bcSel = await page.evaluate(() => {
    const i = [...document.querySelectorAll('input')].find(e =>
      /barcode/i.test(e.placeholder || ''));
    if (i) { i.id = i.id || 'cap-bc'; return '#' + i.id; }
    return null;
  });
  console.log('  barcodeSel:', bcSel);
  if (bcSel) {
    await page.type(bcSel, '764999083106', { delay: 50 });
    await sleep(600);
    await shot(page, 'sale-02-barcode');
    await clickText('Find by Barcode');
    await sleep(2500);
    await shot(page, 'sale-03-result');
    console.log('  result buttons:', JSON.stringify(await dump()));
    if (!(await clickText('Add to Cart'))) await clickText('Add');
    await sleep(1800);
    await shot(page, 'sale-04-cart');
  }

  await browser.close();
  console.log('done');
})();
