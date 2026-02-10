#!/usr/bin/env node
/**
 * KC EP7 - "Authentication Flows" -- Automated Screen Recording Script
 *
 * HOW TO USE:
 * 1. Close ALL browser windows
 * 2. Open OBS, set to Screen Capture (PipeWire)
 * 3. Hit Record in OBS
 * 4. Run: node scripts/kc-record-ep7.js
 * 5. Stop OBS when the console says "RECORDING COMPLETE"
 *
 * Total runtime: ~3:30
 *
 * SCENES:
 *   1. Login to Keycloak
 *   2. Authentication flows list (7 built-in flows)
 *   3. Browser flow detail (Cookie, Kerberos, IdP Redirector, forms sub-flow, OTP)
 *   4. Direct Grant flow (Username, Password, Conditional OTP)
 *   5. Registration flow (Profile Creation, Password, Recaptcha, Terms)
 *   6. Reset Credentials flow (Choose User, Send Email, Reset Password, OTP)
 *   7. First Broker Login flow (Review Profile, Create/Link User)
 *   8. Docker Auth flow (single step -- Docker Authenticator)
 *   9. Clients flow (4 auth methods -- all Alternative)
 *  10. Required Actions tab (11 configurable actions)
 *  11. Policies tab (Password, OTP, Webauthn policies)
 *  12. Final shot -- flows list
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

async function clickFlowLink(page, flowName) {
  const clicked = await page.evaluate((name) => {
    const links = document.querySelectorAll('table tbody tr td a');
    for (const l of links) {
      if (l.textContent.trim().toLowerCase().includes(name.toLowerCase())) {
        l.click();
        return l.textContent.trim();
      }
    }
    return null;
  }, flowName);
  if (clicked) {
    await sleep(2000);
  }
  return clicked;
}

async function clickTab(page, tabName) {
  await page.evaluate((name) => {
    const tabs = document.querySelectorAll('[role="tab"], .pf-c-tabs__link, button');
    for (const t of tabs) {
      if (t.textContent.trim().includes(name)) { t.click(); return; }
    }
  }, tabName);
  await sleep(PAUSE.MEDIUM);
}

(async () => {
  console.log('\n========================================');
  console.log('  KC EP7 - Authentication Flows');
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
  // SCENE 2: Authentication Flows List -- THE OPENING SHOT (10s)
  // 7 built-in flows: browser, clients, direct grant, docker auth,
  // first broker login, registration, reset credentials
  // ============================================================
  console.log('SCENE 2: *** AUTHENTICATION FLOWS LIST -- 7 BUILT-IN FLOWS ***');
  await navigateTo(page, 'authentication');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 3: Browser Flow -- THE BIG ONE -- MONEY SHOT (10s)
  // Cookie (Alt), Kerberos (Disabled), IdP Redirector (Alt),
  // forms sub-flow -> Username Password (Required), Conditional OTP
  // ============================================================
  console.log('SCENE 3: *** BROWSER FLOW -- THE MAIN LOGIN FLOW ***');
  await clickFlowLink(page, 'browser');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 4: Direct Grant Flow (8s)
  // Username Validation (Required), Password (Required),
  // Conditional OTP sub-flow
  // ============================================================
  console.log('SCENE 4: Direct Grant flow (API/CLI auth)...');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'direct grant');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 5: Registration Flow (8s)
  // registration form sub-flow -> Profile Creation, Password,
  // Recaptcha (Disabled), Terms and Conditions (Disabled)
  // ============================================================
  console.log('SCENE 5: Registration flow (new user signup)...');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'registration');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 6: Reset Credentials Flow (8s)
  // Choose User, Send Reset Email, Reset Password,
  // Conditional OTP sub-flow
  // ============================================================
  console.log('SCENE 6: Reset Credentials flow (password reset)...');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'reset credentials');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 7: First Broker Login Flow (8s)
  // Review Profile, User creation or linking sub-flow ->
  // Create User If Unique (Alt), Handle Existing Account (Alt)
  // ============================================================
  console.log('SCENE 7: First Broker Login flow (identity federation)...');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'first broker login');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 8: Docker Auth Flow (6s)
  // Single step: Docker Authenticator (Required)
  // The simplest flow -- one step only
  // ============================================================
  console.log('SCENE 8: Docker Auth flow (single step)...');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'docker auth');
  await sleep(PAUSE.MEDIUM);

  // ============================================================
  // SCENE 9: Clients Flow (8s)
  // Client Id and Secret (Alt), Signed Jwt (Alt),
  // Signed Jwt with Client Secret (Alt), X509 Certificate (Alt)
  // ============================================================
  console.log('SCENE 9: Clients flow (4 auth methods)...');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'clients');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 10: Required Actions Tab -- MONEY SHOT (10s)
  // 11 configurable actions: OTP, Terms, Update Password,
  // Update Profile, Verify Email, Delete Account, Webauthn, etc.
  // ============================================================
  console.log('SCENE 10: *** REQUIRED ACTIONS -- 11 CONFIGURABLE ACTIONS ***');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickTab(page, 'Required actions');
  await sleep(PAUSE.XLONG);

  // ============================================================
  // SCENE 11: Policies Tab (8s)
  // Password Policy, OTP Policy, Webauthn Policy,
  // Webauthn Passwordless Policy, CIBA Policy
  // ============================================================
  console.log('SCENE 11: Policies tab (security policies)...');
  await clickTab(page, 'Policies');
  await sleep(PAUSE.LONG);

  // ============================================================
  // SCENE 12: Final Shot -- Back to Flows List (8s)
  // Close on the 7 built-in flows
  // ============================================================
  console.log('SCENE 12: Final shot -- flows list...');
  await navigateTo(page, 'authentication');
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
