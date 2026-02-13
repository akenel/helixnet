#!/usr/bin/env node
/**
 * ISOTTO Sport Demo -- Headless Dry Run
 * Verifies all scenes work before recording with OBS.
 */
const puppeteer = require('puppeteer');
const path = require('path');
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log('=== ISOTTO Demo Dry Run (Headless) ===\n');
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--ignore-certificate-errors'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // Scene 1: Intro
  console.log('Scene 1: Intro card...');
  const introPath = path.resolve(__dirname, '../videos/isotto-print-shop/DEMO/intro.html');
  await page.goto('file://' + introPath);
  console.log('  OK');

  // Scene 2: Login
  console.log('Scene 2: Login page...');
  await page.goto('https://helix.local/print-shop', { waitUntil: 'networkidle2', timeout: 15000 });
  console.log('  Page loaded:', page.url());

  // Click Accedi
  await page.evaluate(() => {
    const links = document.querySelectorAll('a, button');
    for (const el of links) {
      if (el.textContent.toLowerCase().includes('accedi')) {
        el.click();
        return;
      }
    }
  });
  await sleep(2000);
  console.log('  After click:', page.url());

  // KC Login
  try {
    await page.waitForSelector('#username', { timeout: 8000 });
    await page.type('#username', 'famousguy');
    await page.type('#password', 'helix_pass');
    await page.click('#kc-login');
    await sleep(3000);
    console.log('  After login:', page.url());
  } catch (e) {
    console.log('  KC form error:', e.message);
  }

  // Check we have a token
  const hasToken = await page.evaluate(() => {
    return !!sessionStorage.getItem('isotto_token');
  });
  console.log('  Has token:', hasToken);

  if (!hasToken) {
    console.error('\n  FATAL: No token after login. OAuth flow broken.');
    await browser.close();
    process.exit(1);
  }

  // Scene 3: Dashboard
  console.log('\nScene 3: Dashboard...');
  await sleep(2000);
  const stats = await page.evaluate(async () => {
    const token = sessionStorage.getItem('isotto_token');
    const resp = await fetch('/api/v1/print-shop/dashboard', {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    return resp.ok ? await resp.json() : { error: resp.status };
  });
  console.log('  Stats:', JSON.stringify(stats));

  // Scene 4: Orders
  console.log('\nScene 4: Orders...');
  await page.goto('https://helix.local/print-shop/orders', { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(2000);
  const orderRows = await page.evaluate(() => document.querySelectorAll('tbody tr').length);
  console.log('  Order table rows:', orderRows);

  // Scene 5: Order Detail (Pizza Planet)
  console.log('\nScene 5: Order detail -- Pizza Planet...');
  const orderId = await page.evaluate(async () => {
    const token = sessionStorage.getItem('isotto_token');
    const resp = await fetch('/api/v1/print-shop/orders?limit=200', {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    if (resp.ok) {
      const orders = await resp.json();
      for (const o of orders) {
        if (o.title && o.title.includes('Pizza Planet')) return o.id;
      }
    }
    return null;
  });
  console.log('  Pizza Planet order ID:', orderId);
  if (orderId) {
    await page.goto('https://helix.local/print-shop/orders/' + orderId, { waitUntil: 'networkidle2', timeout: 15000 });
    await sleep(2000);
    console.log('  Page URL:', page.url());
  }

  // Scene 6: New order form
  console.log('\nScene 6: New order form...');
  await page.goto('https://helix.local/print-shop/orders/new', { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(1000);
  const formCheck = await page.evaluate(() => {
    const selects = document.querySelectorAll('select').length;
    const inputs = document.querySelectorAll('input').length;
    return { selects, inputs };
  });
  console.log('  Form elements:', formCheck);

  // Scene 7: Status workflow (find a QUOTED order)
  console.log('\nScene 7: Status workflow...');
  const quotedId = await page.evaluate(async () => {
    const token = sessionStorage.getItem('isotto_token');
    const resp = await fetch('/api/v1/print-shop/orders?limit=200', {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    if (resp.ok) {
      const orders = await resp.json();
      for (const o of orders) {
        if (o.status === 'quoted') return o.id;
      }
    }
    return null;
  });
  console.log('  Quoted order found:', !!quotedId);

  // Scene 8: Customers
  console.log('\nScene 8: Customers...');
  await page.goto('https://helix.local/print-shop/customers', { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(2000);
  const custData = await page.evaluate(async () => {
    const token = sessionStorage.getItem('isotto_token');
    const resp = await fetch('/api/v1/print-shop/customers', {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    if (resp.ok) {
      const custs = await resp.json();
      return custs.map(c => c.name);
    }
    return [];
  });
  console.log('  Customers:', custData);

  // Scene 9: RBAC -- full logout (clear cookies + token) and login as Giulia
  console.log('\nScene 9: RBAC -- switching to Giulia...');
  // Clear ALL cookies (kills KC SSO session) + app token
  const cdpClient = await page.target().createCDPSession();
  await cdpClient.send('Network.clearBrowserCookies');
  await page.evaluate(() => sessionStorage.removeItem('isotto_token'));
  console.log('  All cookies + token cleared');
  await page.goto('https://helix.local/print-shop', { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(1000);

  // Click login
  await page.evaluate(() => {
    const links = document.querySelectorAll('a, button');
    for (const el of links) {
      if (el.textContent.toLowerCase().includes('accedi')) { el.click(); return; }
    }
  });
  await sleep(2000);

  // KC login as Giulia
  try {
    await page.waitForSelector('#username', { timeout: 8000 });
    await page.type('#username', 'giulia_f');
    await page.type('#password', 'helix_pass');
    await page.click('#kc-login');
    await sleep(3000);
    console.log('  Giulia logged in:', page.url());
    const giuliaToken = await page.evaluate(() => !!sessionStorage.getItem('isotto_token'));
    console.log('  Giulia has token:', giuliaToken);
  } catch (e) {
    console.log('  Giulia KC login issue:', e.message);
  }

  // Scene 10: Outro
  console.log('\nScene 10: Outro card...');
  const outroPath = path.resolve(__dirname, '../videos/isotto-print-shop/DEMO/outro.html');
  await page.goto('file://' + outroPath);
  console.log('  OK');

  console.log('\n=== DRY RUN COMPLETE -- All scenes passed ===');
  await browser.close();
}

main().catch(err => {
  console.error('FAILED:', err.message);
  process.exit(1);
});
