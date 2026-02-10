#!/usr/bin/env node
/**
 * KC EP5 - "RBAC Deep Dive" -- Automated Screen Recording Script
 *
 * HOW TO USE:
 * 1. Close ALL browser windows
 * 2. Open OBS, set to Screen Capture (PipeWire)
 * 3. Hit Record in OBS
 * 4. Run: node scripts/kc-record-ep5.js
 * 5. Stop OBS when the console says "RECORDING COMPLETE"
 *
 * Total runtime: ~3 minutes
 *
 * SCENES:
 *   1. Login to Keycloak
 *   2. POS Realm Roles list (5 custom roles with emoji icons)
 *   3. Role detail: pos-admin (crown - full control)
 *   4. Role detail: pos-cashier (money - limited discount)
 *   5. Role detail: pos-manager (briefcase - unlimited)
 *   6. Users in role: pos-cashier
 *   7. User Pam - cashier only
 *   8. User Ralph - cashier + manager
 *   9. User Michael - developer only
 *  10. User Felix - admin + cashier + manager (super user)
 *  11. Client scopes (10 OIDC scopes)
 *  12. Authentication flows
 *  13. Realm settings + endpoints
 *  14. Final shot - roles list
 */

const puppeteer = require('puppeteer');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PAUSE = {
  SHORT: 2500,    // Quick view
  MEDIUM: 4000,   // Read content
  LONG: 6000,     // Study screen
  XLONG: 8000,    // Money shots
  TYPE: 90,       // Per character (human speed)
};

const KC_BASE = 'https://keycloak.helix.local/admin/master/console';
const POS_REALM = 'kc-pos-realm-dev';

async function humanType(page, selector, text) {
  await page.focus(selector);
  for (const char of text) {
    await page.keyboard.type(char, { delay: PAUSE.TYPE });
  }
}

async function navigateTo(page, section) {
  const url = `${KC_BASE}/#/${POS_REALM}/${section}`;
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(1500);
}

async function clickRoleMappingTab(page) {
  await page.evaluate(() => {
    const tabs = document.querySelectorAll('[role="tab"], button');
    for (const tab of tabs) {
      if (tab.textContent.includes('Role mapping')) { tab.click(); return; }
    }
  });
  await sleep(PAUSE.MEDIUM);
}

async function clickUsersInRoleTab(page) {
  await page.evaluate(() => {
    const tabs = document.querySelectorAll('[role="tab"], button');
    for (const tab of tabs) {
      if (tab.textContent.includes('Users in role')) { tab.click(); return; }
    }
  });
  await sleep(PAUSE.MEDIUM);
}

async function openUser(page, userName) {
  await navigateTo(page, 'users');
  await sleep(1000);
  // Click "View all users"
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      if (btn.textContent.includes('View all')) { btn.click(); return; }
    }
  });
  await sleep(2500);
  // Click the user
  await page.evaluate((name) => {
    const links = document.querySelectorAll('table tbody tr td a');
    for (const l of links) {
      if (l.textContent.trim() === name) { l.click(); return; }
    }
  }, userName);
  await sleep(2000);
}

async function openRole(page, roleName) {
  await navigateTo(page, 'roles');
  await sleep(1500);
  await page.evaluate((name) => {
    const links = document.querySelectorAll('table tbody tr td a');
    for (const l of links) {
      if (l.textContent.trim().includes(name)) { l.click(); return; }
    }
  }, roleName);
  await sleep(2000);
}

(async () => {
  console.log('\n========================================');
  console.log('  KC EP5 - RBAC Deep Dive');
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
  await sleep(PAUSE.SHORT);

  // ============================================================
  // SCENE 2: POS Realm Roles List -- THE OPENING MONEY SHOT (12s)
  // 5 custom roles with emoji icons and descriptions
  // ============================================================
  console.log('SCENE 2: *** POS REALM ROLES -- 5 CUSTOM ROLES ***');
  await navigateTo(page, 'roles');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 3: Role Detail -- pos-admin (8s)
  // Crown icon, "Full control over POS realm and configuration"
  // ============================================================
  console.log('SCENE 3: Role detail -- pos-admin...');
  await openRole(page, 'pos-admin');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 4: Role Detail -- pos-cashier (8s)
  // Money bag, "Limited to 10% discount threshold"
  // ============================================================
  console.log('SCENE 4: Role detail -- pos-cashier...');
  await openRole(page, 'pos-cashier');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 5: Role Detail -- pos-manager (8s)
  // Briefcase, "Unlimited discounts and reporting"
  // ============================================================
  console.log('SCENE 5: Role detail -- pos-manager...');
  await openRole(page, 'pos-manager');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 6: Users in Role -- pos-cashier (8s)
  // Shows which users have this role
  // ============================================================
  console.log('SCENE 6: Users in role -- pos-cashier...');
  await openRole(page, 'pos-cashier');
  await clickUsersInRoleTab(page);
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 7: User Pam -- Cashier Only (8s)
  // Front-line worker, one role
  // ============================================================
  console.log('SCENE 7: User Pam -- cashier only...');
  await openUser(page, 'pam');
  await clickRoleMappingTab(page);
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 8: User Ralph -- Cashier + Manager (8s)
  // Senior staff, can override discounts
  // ============================================================
  console.log('SCENE 8: User Ralph -- cashier + manager...');
  await openUser(page, 'ralph');
  await clickRoleMappingTab(page);
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 9: User Michael -- Developer Only (8s)
  // Testing role, no cash access
  // ============================================================
  console.log('SCENE 9: User Michael -- developer only...');
  await openUser(page, 'michael');
  await clickRoleMappingTab(page);
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 10: User Felix -- THE SUPER USER (10s)
  // Admin + Cashier + Manager = full power -- MONEY SHOT #2
  // ============================================================
  console.log('SCENE 10: *** User Felix -- SUPER USER -- MONEY SHOT ***');
  await openUser(page, 'felix');
  await clickRoleMappingTab(page);
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 11: Client Scopes (6s)
  // 10 OIDC scopes -- how JWT tokens carry role info
  // ============================================================
  console.log('SCENE 11: Client scopes...');
  await navigateTo(page, 'client-scopes');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 12: Authentication Flows (6s)
  // 7 built-in flows -- browser, clients, direct grant, etc.
  // ============================================================
  console.log('SCENE 12: Authentication flows...');
  await navigateTo(page, 'authentication');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 13: Realm Settings (10s)
  // General tab -- realm ID, display name, frontend URL, SSL, endpoints
  // ============================================================
  console.log('SCENE 13: Realm settings...');
  await navigateTo(page, 'realm-settings');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 14: Final Shot -- Back to Roles (8s)
  // Close on the 5 custom roles -- the defining feature
  // ============================================================
  console.log('SCENE 14: Final shot -- roles list...');
  await navigateTo(page, 'roles');
  await sleep(PAUSE.XLONG);

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
