#!/usr/bin/env node
/**
 * KC EP7 - "Authentication Flows" -- VOICE-DRIVEN Recording Script
 *
 * Scene timings matched to Angel's voice recordings (Feb 12, 2026).
 * Each pause = exact voice duration so video and audio sync perfectly.
 *
 * HOW TO USE:
 * 1. Close ALL browser windows
 * 2. Open OBS, set to Screen Capture (PipeWire)
 * 3. Run: node scripts/kc-record-ep7-voiced.js
 * 4. When console says ">>> START OBS RECORDING NOW!" -- hit Record
 * 5. Stop OBS when the console says "RECORDING COMPLETE"
 *
 * Total runtime: ~7:45 (voice-paced, not speed-paced)
 *
 * SCENES (12 total, voice-duration driven):
 *   1. Login .................. 29.1s
 *   2. Auth flows list ........ 28.5s
 *   3. Browser flow (MONEY) ... 59.9s
 *   4. Direct grant ........... 27.8s
 *   5. Registration ........... 39.8s
 *   6. Reset credentials ...... 34.0s
 *   7. First broker login ..... 30.6s
 *   8. Docker auth ............ 19.1s
 *   9. Clients flow ........... 34.8s
 *  10. Required actions (MONEY) 45.0s
 *  11. Policies ............... 48.0s
 *  12. Final shot ............. 37.4s
 */

const puppeteer = require('puppeteer');
const sleep = ms => new Promise(r => setTimeout(r, ms));

// Voice durations per scene (seconds) -- from normalized recordings
const VOICE = {
  S1:  29100,   // Login intro
  S2:  28500,   // Authentication flows list
  S3:  59900,   // Browser flow -- MONEY SHOT (longest scene)
  S4:  27800,   // Direct grant
  S5:  39800,   // Registration
  S6:  34000,   // Reset credentials
  S7:  30600,   // First broker login
  S8:  19100,   // Docker auth (shortest)
  S9:  34800,   // Clients flow
  S10: 45000,   // Required actions -- MONEY SHOT
  S11: 48000,   // Policies
  S12: 37400,   // Final shot
};

const TYPE_SPEED = 90;  // ms per character (human speed)

const KC_BASE = 'https://keycloak.helix.local/admin/master/console';
const POS_REALM = 'kc-pos-realm-dev';

async function humanType(page, selector, text) {
  await page.focus(selector);
  for (const char of text) {
    await page.keyboard.type(char, { delay: TYPE_SPEED });
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
  await sleep(2000);
}

function sceneTime(voiceMs) {
  // Voice duration is the scene hold time
  // Navigation happens before this, so the pause IS the voice window
  return voiceMs;
}

(async () => {
  console.log('\n========================================');
  console.log('  KC EP7 - Authentication Flows');
  console.log('  VOICE-DRIVEN Recording Script');
  console.log('  Scene timings matched to voiceover');
  console.log('========================================');
  console.log('\n>>> Chrome opening in 3 seconds...');
  console.log('>>> GET OBS READY!\n');
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
  // SCENE 1: The Login (29.1s voice)
  // "Welcome back... Episode 7... Authentication Flows..."
  // ============================================================
  console.log('SCENE 1: Keycloak Login... (29.1s voice)');
  console.log('>>> START OBS RECORDING NOW! <<<');
  await page.goto('https://keycloak.helix.local/admin/', {
    waitUntil: 'networkidle2', timeout: 15000
  });
  await page.waitForSelector('#username', { timeout: 10000 });
  await sleep(4000);

  await humanType(page, '#username', 'helix_user');
  await sleep(500);
  await humanType(page, '#password', 'helix_pass');
  await sleep(2000);

  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 }),
    page.click('#kc-login')
  ]);
  // Remaining time fills naturally -- login animation + dashboard load
  await sleep(5000);

  // ============================================================
  // SCENE 2: Authentication Flows List (28.5s voice)
  // "Here's the Authentication section... 7 built-in flows..."
  // ============================================================
  console.log('SCENE 2: Auth Flows List (28.5s voice)');
  await navigateTo(page, 'authentication');
  await sleep(sceneTime(VOICE.S2));

  // ============================================================
  // SCENE 3: Browser Flow -- MONEY SHOT (59.9s voice)
  // "The browser flow... Cookie... Kerberos... forms sub-flow..."
  // ============================================================
  console.log('SCENE 3: *** BROWSER FLOW -- MONEY SHOT *** (59.9s voice)');
  await clickFlowLink(page, 'browser');
  await sleep(sceneTime(VOICE.S3));

  // ============================================================
  // SCENE 4: Direct Grant Flow (27.8s voice)
  // "Resource Owner Password Credentials... headless..."
  // ============================================================
  console.log('SCENE 4: Direct Grant (27.8s voice)');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'direct grant');
  await sleep(sceneTime(VOICE.S4));

  // ============================================================
  // SCENE 5: Registration Flow (39.8s voice)
  // "New user signs up... Recaptcha... Terms..."
  // ============================================================
  console.log('SCENE 5: Registration (39.8s voice)');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'registration');
  await sleep(sceneTime(VOICE.S5));

  // ============================================================
  // SCENE 6: Reset Credentials Flow (34.0s voice)
  // "Password recovery pipeline... even reset respects MFA..."
  // ============================================================
  console.log('SCENE 6: Reset Credentials (34.0s voice)');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'reset credentials');
  await sleep(sceneTime(VOICE.S6));

  // ============================================================
  // SCENE 7: First Broker Login Flow (30.6s voice)
  // "Identity federation... Google, corporate SAML..."
  // ============================================================
  console.log('SCENE 7: First Broker Login (30.6s voice)');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'first broker login');
  await sleep(sceneTime(VOICE.S7));

  // ============================================================
  // SCENE 8: Docker Auth Flow (19.1s voice)
  // "Simplest flow... one step, one purpose, clean."
  // ============================================================
  console.log('SCENE 8: Docker Auth (19.1s voice)');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'docker auth');
  await sleep(sceneTime(VOICE.S8));

  // ============================================================
  // SCENE 9: Clients Flow (34.8s voice)
  // "Four auth methods... all Alternative..."
  // ============================================================
  console.log('SCENE 9: Clients Flow (34.8s voice)');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickFlowLink(page, 'clients');
  await sleep(sceneTime(VOICE.S9));

  // ============================================================
  // SCENE 10: Required Actions -- MONEY SHOT (45.0s voice)
  // "Actions forced on users... Enabled vs Default..."
  // ============================================================
  console.log('SCENE 10: *** REQUIRED ACTIONS -- MONEY SHOT *** (45.0s voice)');
  await navigateTo(page, 'authentication');
  await sleep(1500);
  await clickTab(page, 'Required actions');
  await sleep(sceneTime(VOICE.S10));

  // ============================================================
  // SCENE 11: Policies Tab (48.0s voice)
  // "Five policy types... FIDO2... do what you got to do."
  // ============================================================
  console.log('SCENE 11: Policies (48.0s voice)');
  await clickTab(page, 'Policies');
  await sleep(sceneTime(VOICE.S11));

  // ============================================================
  // SCENE 12: Final Shot -- Flows List (37.4s voice)
  // "Seven flows, each one a security pipeline..."
  // ============================================================
  console.log('SCENE 12: Final Shot -- Flows List (37.4s voice)');
  await navigateTo(page, 'authentication');
  await sleep(sceneTime(VOICE.S12));

  // ============================================================
  // END
  // ============================================================
  console.log('\n========================================');
  console.log('  RECORDING COMPLETE');
  console.log('  >>> STOP OBS NOW! <<<');
  console.log('========================================\n');

  await sleep(5000);
  await browser.close();
  console.log('Done. Voice-driven recording complete.');
  console.log('Next: stitch intro + this recording + outro, merge voice.');
})();
