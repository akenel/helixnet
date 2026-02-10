#!/usr/bin/env node
/** Quick dry run -- validate realm navigation + POS users */
const puppeteer = require('puppeteer');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const KC = 'https://keycloak.helix.local/admin/master/console';
const DIR = '/tmp/kc-ep4-dryrun2';

let n = 0;
async function snap(page, label) {
  n++;
  const f = `${DIR}/${String(n).padStart(2,'0')}-${label}.png`;
  await page.screenshot({ path: f });
  console.log(`  [${f}]`);
}

(async () => {
  require('fs').mkdirSync(DIR, { recursive: true });
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--ignore-certificate-errors']
  });
  const page = (await browser.pages())[0];
  await page.setViewport({ width: 1920, height: 1080 });

  // Login
  console.log('Login...');
  await page.goto(`${KC}/`, { waitUntil: 'networkidle2', timeout: 15000 });
  await page.waitForSelector('#username');
  await page.type('#username', 'helix_user');
  await page.type('#password', 'helix_pass');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 }),
    page.click('#kc-login')
  ]);
  await sleep(2000);
  await snap(page, 'master-dashboard');

  // Navigate to POS realm users via URL
  console.log('POS realm users...');
  await page.goto(`${KC}/#/kc-pos-realm-dev/users`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  // Click View all users
  await page.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) { if (b.textContent.includes('View all')) { b.click(); return; } }
  });
  await sleep(2000);
  await snap(page, 'pos-users');

  // Check what users we see
  const users = await page.$$eval('table tbody tr td a', els => els.map(e => e.textContent.trim()));
  console.log('Users:', users);

  // Click first user
  if (users.length > 0) {
    const firstLink = await page.$('table tbody tr td a');
    await firstLink.click();
    await sleep(2000);
    await snap(page, 'pos-user-detail');

    // Role mapping
    await page.evaluate(() => {
      const tabs = document.querySelectorAll('[role="tab"], button');
      for (const t of tabs) { if (t.textContent.includes('Role mapping')) { t.click(); return; } }
    });
    await sleep(2000);
    await snap(page, 'pos-user-roles');
  }

  // POS realm roles
  console.log('POS realm roles...');
  await page.goto(`${KC}/#/kc-pos-realm-dev/roles`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  const roles = await page.$$eval('table tbody tr td a', els => els.map(e => e.textContent.trim()));
  console.log('Roles:', roles);
  await snap(page, 'pos-realm-roles');

  // POS clients
  console.log('POS clients...');
  await page.goto(`${KC}/#/kc-pos-realm-dev/clients`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  await snap(page, 'pos-clients');

  // 420 realm
  console.log('420 realm...');
  await page.goto(`${KC}/#/fourtwenty/welcome`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  await snap(page, '420-welcome');

  // Artemis realm
  console.log('Artemis realm...');
  await page.goto(`${KC}/#/artemis/welcome`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  await snap(page, 'artemis-welcome');

  await browser.close();
  console.log('\nDry run 2 complete. Screenshots:', DIR);
})();
