#!/usr/bin/env node
/** EP6 Dry Run -- probe client details, client scopes, service accounts */
const puppeteer = require('puppeteer');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const KC = 'https://keycloak.helix.local/admin/master/console';
const DIR = '/tmp/kc-ep6-dryrun';

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

  // POS Clients list
  console.log('POS Clients list...');
  await page.goto(`${KC}/#/kc-pos-realm-dev/clients`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  await snap(page, 'clients-list');

  // Get client names
  const clients = await page.$$eval('table tbody tr td a', els => els.map(e => e.textContent.trim()));
  console.log('Clients found:', clients);

  // Click each helix client to see detail
  const helixClients = clients.filter(c => c.startsWith('helix_'));
  for (const clientName of helixClients) {
    console.log(`\n  Opening client: ${clientName}`);
    await page.goto(`${KC}/#/kc-pos-realm-dev/clients`, { waitUntil: 'networkidle2' });
    await sleep(1500);

    await page.evaluate((name) => {
      const links = document.querySelectorAll('table tbody tr td a');
      for (const l of links) { if (l.textContent.trim() === name) { l.click(); return; } }
    }, clientName);
    await sleep(2000);
    await snap(page, `client-${clientName}-settings`);

    // Get all tabs
    const tabs = await page.$$eval('[role="tab"], .pf-c-tabs__link', els =>
      els.map(e => e.textContent.trim()).filter(t => t.length > 0 && t.length < 40)
    );
    console.log(`    Tabs: ${tabs.join(', ')}`);

    // Click Credentials tab if exists
    const hasCredentials = tabs.some(t => t.includes('Credentials'));
    if (hasCredentials) {
      await page.evaluate(() => {
        const allTabs = document.querySelectorAll('[role="tab"], .pf-c-tabs__link');
        for (const t of allTabs) { if (t.textContent.includes('Credentials')) { t.click(); return; } }
      });
      await sleep(2000);
      await snap(page, `client-${clientName}-credentials`);
    }

    // Click Client scopes tab
    const hasScopes = tabs.some(t => t.includes('Client scopes'));
    if (hasScopes) {
      await page.evaluate(() => {
        const allTabs = document.querySelectorAll('[role="tab"], .pf-c-tabs__link');
        for (const t of allTabs) { if (t.textContent.includes('Client scopes')) { t.click(); return; } }
      });
      await sleep(2000);
      await snap(page, `client-${clientName}-scopes`);
    }

    // Click Roles tab
    const hasRoles = tabs.some(t => t === 'Roles');
    if (hasRoles) {
      await page.evaluate(() => {
        const allTabs = document.querySelectorAll('[role="tab"], .pf-c-tabs__link');
        for (const t of allTabs) { if (t.textContent.trim() === 'Roles') { t.click(); return; } }
      });
      await sleep(2000);
      await snap(page, `client-${clientName}-roles`);
    }

    // Click Service account roles tab
    const hasSA = tabs.some(t => t.includes('Service account'));
    if (hasSA) {
      await page.evaluate(() => {
        const allTabs = document.querySelectorAll('[role="tab"], .pf-c-tabs__link');
        for (const t of allTabs) { if (t.textContent.includes('Service account')) { t.click(); return; } }
      });
      await sleep(2000);
      await snap(page, `client-${clientName}-service-account`);
    }
  }

  // Also check the realm-level client scopes (dedicated vs optional)
  console.log('\nRealm client scopes...');
  await page.goto(`${KC}/#/kc-pos-realm-dev/client-scopes`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  await snap(page, 'realm-client-scopes');

  await browser.close();
  console.log('\nDry run complete. Screenshots:', DIR);
})();
