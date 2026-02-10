#!/usr/bin/env node
/**
 * KC EP6 - "Client Architecture" -- Automated Screen Recording Script
 *
 * HOW TO USE:
 * 1. Close ALL browser windows
 * 2. Open OBS, set to Screen Capture (PipeWire)
 * 3. Hit Record in OBS
 * 4. Run: node scripts/kc-record-ep6.js
 * 5. Stop OBS when the console says "RECORDING COMPLETE"
 *
 * Total runtime: ~3 minutes
 *
 * SCENES:
 *   1. Login to Keycloak
 *   2. Clients list (3 helix_pos clients with emoji names)
 *   3. helix_pos_web -- Settings (public SPA, 7+ redirect URIs)
 *   4. helix_pos_web -- Client scopes (8 scopes)
 *   5. helix_pos_mobile -- Settings (public native, custom scheme callback)
 *   6. helix_pos_mobile -- Client scopes (6 scopes)
 *   7. helix_pos_service -- Settings (CONFIDENTIAL, client auth ON)
 *   8. helix_pos_service -- Credentials (Client ID & Secret -- MONEY SHOT)
 *   9. helix_pos_service -- Service account roles
 *  10. helix_pos_service -- Client scopes (5 scopes, minimal)
 *  11. Realm client scopes (10 total, OIDC + SAML)
 *  12. Final shot -- clients list
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

async function clickTab(page, tabName) {
  await page.evaluate((name) => {
    const tabs = document.querySelectorAll('[role="tab"], .pf-c-tabs__link');
    for (const t of tabs) {
      if (t.textContent.trim().includes(name)) { t.click(); return; }
    }
  }, tabName);
  await sleep(PAUSE.MEDIUM);
}

async function openClient(page, clientName) {
  await navigateTo(page, 'clients');
  await sleep(1500);
  await page.evaluate((name) => {
    const links = document.querySelectorAll('table tbody tr td a');
    for (const l of links) {
      if (l.textContent.trim() === name) { l.click(); return; }
    }
  }, clientName);
  await sleep(2000);
}

(async () => {
  console.log('\n========================================');
  console.log('  KC EP6 - Client Architecture');
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
  // SCENE 2: Clients List -- THE OPENING MONEY SHOT (10s)
  // 3 helix_pos clients with emoji names and descriptions
  // ============================================================
  console.log('SCENE 2: *** CLIENTS LIST -- 3 HELIX POS CLIENTS ***');
  await navigateTo(page, 'clients');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 3: helix_pos_web -- Settings (8s)
  // Public client, 7+ redirect URIs for different environments
  // ============================================================
  console.log('SCENE 3: helix_pos_web -- Settings (Public SPA)...');
  await openClient(page, 'helix_pos_web');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 4: helix_pos_web -- Client Scopes (6s)
  // 8 scopes including optional address, phone, offline_access
  // ============================================================
  console.log('SCENE 4: helix_pos_web -- Client scopes...');
  await clickTab(page, 'Client scopes');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 5: helix_pos_mobile -- Settings (8s)
  // Public client, custom scheme helixpos://oauth/callback
  // ============================================================
  console.log('SCENE 5: helix_pos_mobile -- Settings (Native App)...');
  await openClient(page, 'helix_pos_mobile');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 6: helix_pos_mobile -- Client Scopes (6s)
  // 6 scopes, leaner than web
  // ============================================================
  console.log('SCENE 6: helix_pos_mobile -- Client scopes...');
  await clickTab(page, 'Client scopes');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 7: helix_pos_service -- Settings (8s)
  // CONFIDENTIAL client -- Client authentication ON
  // ============================================================
  console.log('SCENE 7: *** helix_pos_service -- CONFIDENTIAL CLIENT ***');
  await openClient(page, 'helix_pos_service');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 8: helix_pos_service -- Credentials -- MONEY SHOT (10s)
  // Client ID and Client Secret with Regenerate button
  // ============================================================
  console.log('SCENE 8: *** CREDENTIALS -- CLIENT SECRET -- MONEY SHOT ***');
  await clickTab(page, 'Credentials');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 9: helix_pos_service -- Service Account Roles (8s)
  // Shows service-account-helix_pos_service user link
  // ============================================================
  console.log('SCENE 9: Service account roles...');
  await clickTab(page, 'Service accounts roles');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 10: helix_pos_service -- Client Scopes (6s)
  // 5 scopes only -- minimal, machine-to-machine
  // ============================================================
  console.log('SCENE 10: helix_pos_service -- Client scopes...');
  await clickTab(page, 'Client scopes');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 11: Realm Client Scopes (8s)
  // 10 total scopes shared across all clients
  // ============================================================
  console.log('SCENE 11: Realm client scopes...');
  await navigateTo(page, 'client-scopes');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 12: Final Shot -- Back to Clients List (8s)
  // Close on the 3 helix clients
  // ============================================================
  console.log('SCENE 12: Final shot -- clients list...');
  await navigateTo(page, 'clients');
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
