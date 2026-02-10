const puppeteer = require('puppeteer');
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--ignore-certificate-errors']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // Login
  await page.goto('https://keycloak.helix.local/admin/', { waitUntil: 'networkidle2', timeout: 15000 });
  await page.waitForSelector('#username', { timeout: 10000 });
  await page.type('#username', 'helix_user');
  await page.type('#password', 'helix_pass');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 }),
    page.click('#kc-login')
  ]);
  await sleep(2000);

  // Open realm dropdown
  console.log('=== Opening realm selector ===');
  const realmToggle = await page.$('.pf-c-context-selector__toggle');
  if (realmToggle) {
    await realmToggle.click();
    await sleep(1000);
    // Get realm list items
    const realms = await page.$$eval('.pf-c-context-selector__menu-list-item button, .pf-c-context-selector__menu-list-item a', els =>
      els.map(e => ({ text: e.textContent.trim(), tag: e.tagName }))
    );
    console.log('Realms found:', JSON.stringify(realms, null, 2));
    await page.screenshot({ path: '/tmp/kc-realms-dropdown.png' });
    console.log('Screenshot: /tmp/kc-realms-dropdown.png');

    // Click kc-pos-realm-dev
    const posRealm = await page.$('button:has-text("kc-pos-realm-dev")');
    // Try alternative: evaluate click
    await page.evaluate(() => {
      const items = document.querySelectorAll('.pf-c-context-selector__menu-list-item button');
      for (const item of items) {
        if (item.textContent.trim() === 'kc-pos-realm-dev') {
          item.click();
          return true;
        }
      }
      return false;
    });
    await sleep(2000);
    console.log('Switched to POS realm, URL:', page.url());

    // Navigate to Users
    await page.goto('https://keycloak.helix.local/admin/master/console/#/kc-pos-realm-dev/users', { waitUntil: 'networkidle2', timeout: 15000 });
    await sleep(2000);
    await page.screenshot({ path: '/tmp/kc-users-list.png' });

    // Check for user table
    const userRows = await page.$$eval('table tbody tr td a, [data-testid*="user"] a', els =>
      els.map(e => ({ text: e.textContent.trim(), href: e.href }))
    );
    console.log('\nUsers found:', JSON.stringify(userRows, null, 2));

    // Try clicking "View all users" if list is empty
    const viewAll = await page.evaluate(() => {
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        if (btn.textContent.includes('View all')) {
          btn.click();
          return 'clicked view all';
        }
      }
      return 'no view all button';
    });
    console.log('View all:', viewAll);
    await sleep(2000);

    const userRows2 = await page.$$eval('table tbody tr td a', els =>
      els.map(e => ({ text: e.textContent.trim(), href: e.href }))
    );
    console.log('Users after view all:', JSON.stringify(userRows2, null, 2));
    await page.screenshot({ path: '/tmp/kc-users-after-viewall.png' });

    // Get the URL pattern for user detail
    if (userRows2.length > 0) {
      console.log('\nFirst user URL:', userRows2[0].href);
    }
  }

  // Check Realm Roles page
  await page.goto('https://keycloak.helix.local/admin/master/console/#/kc-pos-realm-dev/roles', { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(2000);
  const roles = await page.$$eval('table tbody tr td a', els =>
    els.map(e => ({ text: e.textContent.trim() }))
  );
  console.log('\nRealm Roles:', JSON.stringify(roles, null, 2));
  await page.screenshot({ path: '/tmp/kc-realm-roles.png' });

  // Check Clients page
  await page.goto('https://keycloak.helix.local/admin/master/console/#/kc-pos-realm-dev/clients', { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(2000);
  const clients = await page.$$eval('table tbody tr td a', els =>
    els.map(e => ({ text: e.textContent.trim() }))
  );
  console.log('\nClients:', JSON.stringify(clients, null, 2));
  await page.screenshot({ path: '/tmp/kc-clients.png' });

  await browser.close();
  console.log('\nAll probes done.');
})();
