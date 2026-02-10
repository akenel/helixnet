#!/usr/bin/env node
/** EP5 Dry Run -- probe role details, user role mappings, client scopes */
const puppeteer = require('puppeteer');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const KC = 'https://keycloak.helix.local/admin/master/console';
const DIR = '/tmp/kc-ep5-dryrun';

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

  // POS Realm Roles
  console.log('POS Realm Roles...');
  await page.goto(`${KC}/#/kc-pos-realm-dev/roles`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  await snap(page, 'pos-roles-list');

  // Get role names
  const roles = await page.$$eval('table tbody tr td a', els => els.map(e => e.textContent.trim()));
  console.log('Roles found:', roles);

  // Click each role to see detail page
  for (const roleName of roles) {
    console.log(`  Opening role: ${roleName}`);
    await page.goto(`${KC}/#/kc-pos-realm-dev/roles`, { waitUntil: 'networkidle2' });
    await sleep(1500);

    // Click the role link
    await page.evaluate((name) => {
      const links = document.querySelectorAll('table tbody tr td a');
      for (const l of links) { if (l.textContent.trim() === name) { l.click(); return; } }
    }, roleName);
    await sleep(2000);
    await snap(page, `role-${roleName}`);

    // Check for tabs (Users in role, etc.)
    const tabs = await page.$$eval('[role="tab"], button', els =>
      els.map(e => e.textContent.trim()).filter(t => t.length > 0 && t.length < 40)
    );
    console.log(`    Tabs: ${tabs.join(', ')}`);
  }

  // Show different users with different roles
  console.log('\nUser role mappings...');
  const testUsers = ['pam', 'ralph', 'michael', 'felix'];

  await page.goto(`${KC}/#/kc-pos-realm-dev/users`, { waitUntil: 'networkidle2' });
  await sleep(1500);
  await page.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) { if (b.textContent.includes('View all')) { b.click(); return; } }
  });
  await sleep(2000);

  for (const userName of testUsers) {
    console.log(`  User: ${userName}`);
    // Click user from list
    await page.goto(`${KC}/#/kc-pos-realm-dev/users`, { waitUntil: 'networkidle2' });
    await sleep(1500);
    await page.evaluate(() => {
      const btns = document.querySelectorAll('button');
      for (const b of btns) { if (b.textContent.includes('View all')) { b.click(); return; } }
    });
    await sleep(2000);

    await page.evaluate((name) => {
      const links = document.querySelectorAll('table tbody tr td a');
      for (const l of links) { if (l.textContent.trim() === name) { l.click(); return; } }
    }, userName);
    await sleep(2000);

    // Click Role mapping tab
    await page.evaluate(() => {
      const tabs = document.querySelectorAll('[role="tab"], button');
      for (const t of tabs) { if (t.textContent.includes('Role mapping')) { t.click(); return; } }
    });
    await sleep(2000);
    await snap(page, `user-${userName}-roles`);

    // Get roles for this user
    const userRoles = await page.$$eval('table tbody tr td', els =>
      els.map(e => e.textContent.trim()).filter(t => t.includes('pos-'))
    );
    console.log(`    Roles: ${userRoles.join(', ')}`);
  }

  // Client scopes
  console.log('\nClient scopes...');
  await page.goto(`${KC}/#/kc-pos-realm-dev/client-scopes`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  await snap(page, 'client-scopes');

  // Authentication flows
  console.log('Authentication flows...');
  await page.goto(`${KC}/#/kc-pos-realm-dev/authentication`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  await snap(page, 'auth-flows');

  // Realm settings
  console.log('Realm settings...');
  await page.goto(`${KC}/#/kc-pos-realm-dev/realm-settings`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  await snap(page, 'realm-settings');

  await browser.close();
  console.log('\nDry run complete. Screenshots:', DIR);
})();
