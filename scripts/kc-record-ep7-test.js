#!/usr/bin/env node
/** EP7 Dry Run -- probe authentication flows, flow details, execution steps */
const puppeteer = require('puppeteer');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const KC = 'https://keycloak.helix.local/admin/master/console';
const DIR = '/tmp/kc-ep7-dryrun';

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

  // Authentication flows list
  console.log('Authentication flows list...');
  await page.goto(`${KC}/#/kc-pos-realm-dev/authentication`, { waitUntil: 'networkidle2' });
  await sleep(2000);
  await snap(page, 'auth-flows-list');

  // Get flow names
  const flows = await page.$$eval('table tbody tr td a, [data-testid] a', els =>
    els.map(e => e.textContent.trim()).filter(t => t.length > 0 && t.length < 60)
  );
  console.log('Flows found:', flows);

  // Try to get flows from the table or list
  const flowLinks = await page.$$eval('table tbody tr td:first-child a, td a[href*="authentication"]', els =>
    els.map(e => ({ text: e.textContent.trim(), href: e.href }))
  );
  console.log('Flow links:', flowLinks);

  // Click each flow to see its detail/execution steps
  const flowNames = ['browser', 'direct grant', 'registration', 'reset credentials', 'first broker login', 'docker auth', 'clients'];
  for (const flowName of flowNames) {
    console.log(`\n  Opening flow: ${flowName}`);
    await page.goto(`${KC}/#/kc-pos-realm-dev/authentication`, { waitUntil: 'networkidle2' });
    await sleep(1500);

    // Try clicking the flow link
    const clicked = await page.evaluate((name) => {
      // Try table links first
      const links = document.querySelectorAll('table tbody tr td a');
      for (const l of links) {
        if (l.textContent.trim().toLowerCase().includes(name.toLowerCase())) {
          l.click();
          return l.textContent.trim();
        }
      }
      // Try any link on the page
      const allLinks = document.querySelectorAll('a');
      for (const l of allLinks) {
        if (l.textContent.trim().toLowerCase().includes(name.toLowerCase())) {
          l.click();
          return l.textContent.trim();
        }
      }
      return null;
    }, flowName);

    if (clicked) {
      console.log(`    Clicked: ${clicked}`);
      await sleep(2500);
      await snap(page, `flow-${flowName.replace(/\s+/g, '-')}`);

      // Check for execution steps / sub-flows
      const pageContent = await page.evaluate(() => {
        const items = [];
        // Look for execution step rows
        document.querySelectorAll('tr, [class*="execution"], [class*="flow"]').forEach(el => {
          const text = el.textContent.trim().substring(0, 100);
          if (text.length > 0) items.push(text);
        });
        return items.slice(0, 20);
      });
      console.log(`    Page items (first 20):`, pageContent.slice(0, 5));
    } else {
      console.log(`    Could not find flow: ${flowName}`);
    }
  }

  // Also check Required Actions tab
  console.log('\nRequired Actions...');
  await page.goto(`${KC}/#/kc-pos-realm-dev/authentication`, { waitUntil: 'networkidle2' });
  await sleep(1500);
  // Click Required Actions tab
  await page.evaluate(() => {
    const tabs = document.querySelectorAll('[role="tab"], .pf-c-tabs__link, button');
    for (const t of tabs) {
      if (t.textContent.includes('Required actions')) { t.click(); return; }
    }
  });
  await sleep(2000);
  await snap(page, 'required-actions');

  // Check Policies tab
  console.log('Policies...');
  await page.evaluate(() => {
    const tabs = document.querySelectorAll('[role="tab"], .pf-c-tabs__link, button');
    for (const t of tabs) {
      if (t.textContent.includes('Policies')) { t.click(); return; }
    }
  });
  await sleep(2000);
  await snap(page, 'policies');

  await browser.close();
  console.log('\nDry run complete. Screenshots:', DIR);
})();
