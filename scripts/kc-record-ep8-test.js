#!/usr/bin/env node
/** EP8 Dry Run -- probe multi-tenant platform: all 6 realms, their configs */
const puppeteer = require('puppeteer');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const KC = 'https://keycloak.helix.local/admin/master/console';
const DIR = '/tmp/kc-ep8-dryrun';

const REALMS = [
  { id: 'master', name: 'Keycloak (master)' },
  { id: 'kc-pos-realm-dev', name: 'HelixPOS Development' },
  { id: 'kc-realm-dev', name: 'HelixNet Development' },
  { id: 'fourtwenty', name: '420 Wholesale' },
  { id: 'artemis', name: 'Artemis Headshop' },
  { id: 'blowup-v2', name: 'BlowUp V2' },
];

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

  // For each realm, capture: dashboard, users, clients, roles
  for (const realm of REALMS) {
    console.log(`\n=== REALM: ${realm.name} (${realm.id}) ===`);

    // Dashboard / Welcome
    console.log('  Dashboard...');
    await page.goto(`${KC}/#/${realm.id}`, { waitUntil: 'networkidle2', timeout: 15000 });
    await sleep(2000);
    await snap(page, `${realm.id}-dashboard`);

    // Users
    console.log('  Users...');
    await page.goto(`${KC}/#/${realm.id}/users`, { waitUntil: 'networkidle2', timeout: 15000 });
    await sleep(2000);
    // Click "View all users" button if present
    await page.evaluate(() => {
      const btns = document.querySelectorAll('button');
      for (const b of btns) {
        if (b.textContent.includes('View all')) { b.click(); return; }
      }
    });
    await sleep(2000);
    await snap(page, `${realm.id}-users`);

    // Count users
    const userCount = await page.evaluate(() => {
      const rows = document.querySelectorAll('table tbody tr');
      return rows.length;
    });
    console.log(`    Users visible: ${userCount}`);

    // Clients
    console.log('  Clients...');
    await page.goto(`${KC}/#/${realm.id}/clients`, { waitUntil: 'networkidle2', timeout: 15000 });
    await sleep(2000);
    await snap(page, `${realm.id}-clients`);

    // Count clients
    const clientData = await page.evaluate(() => {
      const rows = document.querySelectorAll('table tbody tr');
      return Array.from(rows).map(r => {
        const cells = r.querySelectorAll('td');
        return cells.length > 0 ? cells[0].textContent.trim() : '';
      }).filter(t => t.length > 0);
    });
    console.log(`    Clients: ${clientData.join(', ')}`);

    // Realm Roles
    console.log('  Realm Roles...');
    await page.goto(`${KC}/#/${realm.id}/roles`, { waitUntil: 'networkidle2', timeout: 15000 });
    await sleep(2000);
    await snap(page, `${realm.id}-roles`);

    const roleData = await page.evaluate(() => {
      const rows = document.querySelectorAll('table tbody tr');
      return Array.from(rows).map(r => {
        const cells = r.querySelectorAll('td');
        return cells.length > 0 ? cells[0].textContent.trim() : '';
      }).filter(t => t.length > 0);
    });
    console.log(`    Roles: ${roleData.join(', ')}`);

    // Realm Settings (General tab)
    if (realm.id !== 'master') {
      console.log('  Realm Settings...');
      await page.goto(`${KC}/#/${realm.id}/realm-settings`, { waitUntil: 'networkidle2', timeout: 15000 });
      await sleep(2000);
      await snap(page, `${realm.id}-settings`);
    }
  }

  // Final: realm dropdown showing all 6
  console.log('\nRealm dropdown...');
  await page.goto(`${KC}/#/master`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(1500);
  // Open realm dropdown
  const toggle = await page.$('.pf-c-context-selector__toggle');
  if (toggle) {
    await toggle.click();
    await sleep(1500);
    await snap(page, 'realm-dropdown-open');
    const realmNames = await page.evaluate(() => {
      const items = document.querySelectorAll('.pf-c-context-selector__menu-list-item button');
      return Array.from(items).map(i => i.textContent.trim());
    });
    console.log('  Realms in dropdown:', realmNames);
  }

  await browser.close();
  console.log('\nDry run complete. Screenshots:', DIR);
})();
