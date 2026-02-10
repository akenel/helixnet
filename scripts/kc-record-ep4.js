#!/usr/bin/env node
/**
 * KC EP4 - "Keys to the Kingdom" -- Automated Screen Recording Script
 *
 * HOW TO USE:
 * 1. Open OBS, set Window Capture to the Chrome window
 * 2. Hit Record in OBS
 * 3. Run: node scripts/kc-record-ep4.js
 * 4. Stop OBS when the console says "RECORDING COMPLETE"
 *
 * Total runtime: ~4 minutes
 */

const puppeteer = require('puppeteer');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PAUSE = {
  SHORT: 2500,
  MEDIUM: 4000,
  LONG: 6000,
  XLONG: 8000,
  TYPE: 90,
};

// Realms with their KC IDs and display names
const REALMS = {
  master:    { id: 'master',           label: 'Keycloak' },
  pos:       { id: 'kc-pos-realm-dev', label: 'HelixPOS' },
  dev:       { id: 'kc-realm-dev',     label: 'HelixNet' },
  fourtwenty:{ id: 'fourtwenty',       label: '420 Wholesale' },
  artemis:   { id: 'artemis',          label: 'Artemis Headshop' },
  blowup:    { id: 'blowup-v2',       label: 'BlowUp' },
};

const KC_BASE = 'https://keycloak.helix.local/admin/master/console';

async function humanType(page, selector, text) {
  await page.focus(selector);
  for (const char of text) {
    await page.keyboard.type(char, { delay: PAUSE.TYPE });
  }
}

async function navigateToRealm(page, realmId, section) {
  const url = section
    ? `${KC_BASE}/#/${realmId}/${section}`
    : `${KC_BASE}/#/${realmId}`;
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(1500);
}

(async () => {
  console.log('\n========================================');
  console.log('  KC EP4 - Keys to the Kingdom');
  console.log('  Automated Recording Script');
  console.log('========================================');
  console.log('\n>>> Chrome opening in 3 seconds...');
  console.log('>>> START OBS RECORDING NOW!\n');
  await sleep(3000);

  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: [
      '--no-sandbox',
      '--ignore-certificate-errors',
      '--start-maximized',
    ]
  });

  const page = (await browser.pages())[0];

  // ============================================================
  // SCENE 1: The Login (15s)
  // ============================================================
  console.log('SCENE 1: Keycloak Login...');
  await page.goto('https://keycloak.helix.local/admin/', {
    waitUntil: 'networkidle2', timeout: 15000
  });
  await page.waitForSelector('#username', { timeout: 10000 });
  await sleep(PAUSE.MEDIUM);

  await humanType(page, '#username', 'helix_user');
  await sleep(400);
  await humanType(page, '#password', 'helix_pass');
  await sleep(PAUSE.SHORT);

  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 }),
    page.click('#kc-login')
  ]);

  // ============================================================
  // SCENE 2: Master Realm Dashboard (10s)
  // ============================================================
  console.log('SCENE 2: Master Realm Dashboard...');
  await sleep(PAUSE.LONG);

  // Show Server Info tab
  const infoTab = await page.$('[data-testid="infoTab"]');
  if (infoTab) {
    await infoTab.click();
    await sleep(PAUSE.MEDIUM);
  }

  // Back to Welcome
  const welcomeTab = await page.$('[data-testid="welcomeTab"]');
  if (welcomeTab) {
    await welcomeTab.click();
    await sleep(PAUSE.SHORT);
  }

  // ============================================================
  // SCENE 3: THE MONEY SHOT - All Realms in Dropdown (15s)
  // ============================================================
  console.log('SCENE 3: *** REALM DROPDOWN -- THE MONEY SHOT ***');

  // Open dropdown
  await page.click('.pf-c-context-selector__toggle');
  await sleep(PAUSE.LONG);

  // Scroll to bottom to show all realms
  await page.evaluate(() => {
    const list = document.querySelector('.pf-c-context-selector__menu-list');
    if (list) list.scrollTop = list.scrollHeight;
  });
  await sleep(PAUSE.LONG);

  // Scroll back to top
  await page.evaluate(() => {
    const list = document.querySelector('.pf-c-context-selector__menu-list');
    if (list) list.scrollTop = 0;
  });
  await sleep(PAUSE.MEDIUM);

  // Close dropdown
  await page.keyboard.press('Escape');
  await sleep(PAUSE.SHORT);

  // ============================================================
  // SCENE 4: POS Realm Dashboard (6s)
  // ============================================================
  console.log('SCENE 4: POS Realm...');
  await navigateToRealm(page, 'kc-pos-realm-dev', 'welcome');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 5: POS Users List (8s)
  // ============================================================
  console.log('SCENE 5: POS Users...');
  await navigateToRealm(page, 'kc-pos-realm-dev', 'users');
  await sleep(1500);

  // Click "View all users"
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      if (btn.textContent.includes('View all')) { btn.click(); return; }
    }
  });
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 6: User Detail + Role Mapping (12s)
  // ============================================================
  console.log('SCENE 6: User Detail...');
  const firstUser = await page.$('table tbody tr td a');
  if (firstUser) {
    const userName = await page.evaluate(el => el.textContent.trim(), firstUser);
    console.log(`  Opening user: ${userName}`);
    await firstUser.click();
    await sleep(PAUSE.MEDIUM);

    // Click Role mapping tab
    await page.evaluate(() => {
      const tabs = document.querySelectorAll('[role="tab"], button');
      for (const tab of tabs) {
        if (tab.textContent.includes('Role mapping')) { tab.click(); return; }
      }
    });
    await sleep(PAUSE.LONG);
  }

  // ============================================================
  // SCENE 7: Realm Roles (6s)
  // ============================================================
  console.log('SCENE 7: Realm Roles...');
  await navigateToRealm(page, 'kc-pos-realm-dev', 'roles');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 8: Clients (6s)
  // ============================================================
  console.log('SCENE 8: Clients...');
  await navigateToRealm(page, 'kc-pos-realm-dev', 'clients');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 9: Quick tour of other realms (15s)
  // ============================================================
  console.log('SCENE 9: 420 Wholesale realm...');
  await navigateToRealm(page, 'fourtwenty', 'welcome');
  await sleep(PAUSE.MEDIUM);

  console.log('  Artemis Headshop realm...');
  await navigateToRealm(page, 'artemis', 'welcome');
  await sleep(PAUSE.MEDIUM);

  console.log('  BlowUp realm...');
  await navigateToRealm(page, 'blowup-v2', 'welcome');
  await sleep(PAUSE.MEDIUM);

  // ============================================================
  // SCENE 10: Back to Master -- Final Realm Dropdown (10s)
  // ============================================================
  console.log('SCENE 10: Final shot -- back to master...');
  await navigateToRealm(page, 'master', 'welcome');
  await sleep(PAUSE.SHORT);

  // Open realm dropdown one final time
  await page.click('.pf-c-context-selector__toggle');
  await sleep(PAUSE.XLONG);

  // Close dropdown
  await page.keyboard.press('Escape');
  await sleep(PAUSE.LONG);

  // ============================================================
  // END
  // ============================================================
  console.log('\n========================================');
  console.log('  RECORDING COMPLETE');
  console.log('  >>> STOP OBS NOW! <<<');
  console.log('========================================\n');

  await sleep(5000);
  await browser.close();
  console.log('Done. Check your OBS recording.');
})();
