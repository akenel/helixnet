#!/usr/bin/env node
/**
 * KC EP8 - "Multi-Tenant Platform" -- Automated Screen Recording Script
 *
 * HOW TO USE:
 * 1. Close ALL browser windows
 * 2. Open OBS, set to Screen Capture (PipeWire)
 * 3. Hit Record in OBS
 * 4. Run: node scripts/kc-record-ep8.js
 * 5. Stop OBS when the console says "RECORDING COMPLETE"
 *
 * Total runtime: ~3:30
 *
 * SCENES:
 *   1. Login to Keycloak
 *   2. Master realm dashboard (the control plane)
 *   3. Master realm clients (5 realm-clients -- each tenant registers here)
 *   4. HelixPOS Dev -- users (9 users, the biggest tenant)
 *   5. HelixPOS Dev -- roles (5 emoji RBAC roles)
 *   6. HelixNet Dev -- users (6 users, platform realm)
 *   7. HelixNet Dev -- roles (4 emoji roles)
 *   8. 420 Wholesale -- users (4 users, cannabis wholesale)
 *   9. 420 Wholesale -- roles (buyer/seller/network-boss)
 *  10. Artemis Headshop -- users (5 users, retail Luzern)
 *  11. BlowUp V2 -- dashboard (custom branded welcome)
 *  12. BlowUp V2 -- users
 *  13. Final: master realm dashboard (the big picture)
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

async function humanType(page, selector, text) {
  await page.focus(selector);
  for (const char of text) {
    await page.keyboard.type(char, { delay: PAUSE.TYPE });
  }
}

async function navigateTo(page, realmId, section) {
  const url = `${KC_BASE}/#/${realmId}/${section}`;
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(1500);
}

async function clickViewAll(page) {
  await page.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
      if (b.textContent.includes('View all')) { b.click(); return; }
    }
  });
  await sleep(2000);
}

(async () => {
  console.log('\n========================================');
  console.log('  KC EP8 - Multi-Tenant Platform');
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
  // SCENE 2: Master Realm Dashboard -- THE CONTROL PLANE (8s)
  // "Welcome to Keycloak" -- master realm, the root of all tenants
  // ============================================================
  console.log('SCENE 2: *** MASTER REALM -- THE CONTROL PLANE ***');
  await navigateTo(page, 'master', '');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 3: Master Realm Clients -- MONEY SHOT (10s)
  // 5 realm-clients: each tenant realm registers as a client here
  // artemis-realm, blowup-realm, blowup-v2-realm, fourtwenty-realm, etc.
  // ============================================================
  console.log('SCENE 3: *** MASTER CLIENTS -- 5 REALM CLIENTS ***');
  await navigateTo(page, 'master', 'clients');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 4: HelixPOS Dev -- Users (8s)
  // The biggest tenant: 9 users across multiple stores
  // aleena, andy, felix, leandra, michael, pam, pos-auditor, pos-developer, ralph
  // ============================================================
  console.log('SCENE 4: HelixPOS Dev -- Users (9 users, biggest tenant)...');
  await navigateTo(page, 'kc-pos-realm-dev', 'users');
  await sleep(1500);
  await clickViewAll(page);
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 5: HelixPOS Dev -- Roles -- MONEY SHOT (8s)
  // 5 emoji RBAC roles: admin, auditor, cashier, developer, manager
  // ============================================================
  console.log('SCENE 5: *** HelixPOS Dev -- 5 EMOJI RBAC ROLES ***');
  await navigateTo(page, 'kc-pos-realm-dev', 'roles');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 6: HelixNet Dev -- Users (6s)
  // Platform realm: 6 users
  // ============================================================
  console.log('SCENE 6: HelixNet Dev -- Users (6 users, platform)...');
  await navigateTo(page, 'kc-realm-dev', 'users');
  await sleep(1500);
  await clickViewAll(page);
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 7: HelixNet Dev -- Roles (6s)
  // 4 emoji roles: admin, auditor, developer, guest
  // ============================================================
  console.log('SCENE 7: HelixNet Dev -- 4 emoji roles...');
  await navigateTo(page, 'kc-realm-dev', 'roles');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 8: 420 Wholesale -- Users (8s)
  // Swiss cannabis wholesale: chuck, demo, mosey, supplier
  // Emails: @bern-store.ch, @420-network.ch
  // ============================================================
  console.log('SCENE 8: 420 Wholesale -- Users (Swiss cannabis wholesale)...');
  await navigateTo(page, 'fourtwenty', 'users');
  await sleep(1500);
  await clickViewAll(page);
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 9: 420 Wholesale -- Roles (6s)
  // Custom roles: pos-buyer, pos-seller, pos-network-boss
  // ============================================================
  console.log('SCENE 9: 420 Wholesale -- roles (buyer/seller/network-boss)...');
  await navigateTo(page, 'fourtwenty', 'roles');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 10: Artemis Headshop -- Users (8s)
  // Retail headshop Luzern: felix (Owner), leandra (Designer),
  // mike (Developer), pam (Cashier), ralph (Manager)
  // ============================================================
  console.log('SCENE 10: Artemis Headshop -- Users (Luzern retail)...');
  await navigateTo(page, 'artemis', 'users');
  await sleep(1500);
  await clickViewAll(page);
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 11: BlowUp V2 -- Dashboard -- MONEY SHOT (8s)
  // Custom branded welcome page with BlowUp V2 logo
  // Shows each realm can have its own branding
  // ============================================================
  console.log('SCENE 11: *** BlowUp V2 -- CUSTOM BRANDED DASHBOARD ***');
  await navigateTo(page, 'blowup-v2', '');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 12: BlowUp V2 -- Users (6s)
  // Minimal: just 2 users (pos-owner, pos-staff)
  // ============================================================
  console.log('SCENE 12: BlowUp V2 -- Users (minimal tenant)...');
  await navigateTo(page, 'blowup-v2', 'users');
  await sleep(1500);
  await clickViewAll(page);
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 13: Final Shot -- Master Realm Dashboard (8s)
  // Back to the control plane -- the big picture
  // ============================================================
  console.log('SCENE 13: Final shot -- Master realm (the big picture)...');
  await navigateTo(page, 'master', '');
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
