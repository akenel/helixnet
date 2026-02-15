#!/usr/bin/env node
/**
 * CAMPER & TOUR EP3 -- "The Full Lifecycle" Demo Recording Script
 *
 * One job, three roles, eight workflow steps, zero paper.
 * Switches between Simona (counter), Nino (manager), Maximo (mechanic)
 * to show RBAC in action across a full job lifecycle.
 *
 * HOW TO USE:
 * 1. Make sure Docker stack is running (make up)
 * 2. Open OBS, set source to "Screen Capture (PipeWire)"
 * 3. Run: node videos/camper-tour/DEMO-service-management/EP3/ct-ep3-record.js
 * 4. A bright RED "OBS CHECK" card fills the screen
 * 5. Check OBS PREVIEW -- do you see the red card FULLSCREEN?
 *    - YES: Hit Record in OBS, then press ENTER in terminal
 *    - NO:  Fix OBS source first.
 * 6. Demo runs automatically (~3-4 min). Don't touch anything.
 * 7. Stop OBS when console says "RECORDING COMPLETE"
 *
 * CRITICAL: All page content is ZOOMED 200% for readability on video.
 *
 * SCENES:
 *   1. Intro card (5s)
 *   2. Simona -- Counter Check-In (30s)
 *   3. Simona -- Access Denied (15s)
 *   4. Nino -- Create Quotation (30s)
 *   5. Nino -- Approve Job (15s)
 *   6. Maximo -- Mechanic Work Log (30s)
 *   7. Maximo -- Submit for Inspection (10s)
 *   8. Nino -- Inspection & Complete (20s)
 *   9. Nino -- Generate Invoice (20s)
 *  10. Nino -- Vehicle Pickup (10s)
 *  11. Outro card (5s)
 */

const puppeteer = require('puppeteer');
const path = require('path');
const { execSync } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PAUSE = {
  SHORT: 2500,
  MEDIUM: 4000,
  LONG: 6000,
  XLONG: 8000,
  INTRO: 5000,
  OUTRO: 5000,
  TYPE: 90,
};

const BASE_URL = 'https://helix.local';
const CAMPER_URL = `${BASE_URL}/camper`;

// Demo users -- three roles
const SIMONA = { user: 'simona', pass: 'helix_pass', role: 'counter' };
const NINO = { user: 'nino', pass: 'helix_pass', role: 'manager' };
const MAXIMO = { user: 'maximo', pass: 'helix_pass', role: 'mechanic' };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function setZoom(page) {
  await page.evaluate(() => { document.body.style.zoom = '2'; });
  await sleep(300);
}

async function humanType(page, selector, text) {
  await page.waitForSelector(selector, { timeout: 5000 });
  await page.focus(selector);
  await sleep(300);
  for (const char of text) {
    await page.keyboard.type(char, { delay: PAUSE.TYPE });
  }
}

async function clearAndType(page, selector, text) {
  await page.waitForSelector(selector, { timeout: 5000 });
  await page.click(selector, { clickCount: 3 });
  await sleep(200);
  for (const char of text) {
    await page.keyboard.type(char, { delay: PAUSE.TYPE });
  }
}

async function clickButtonByText(page, ...texts) {
  return page.evaluate((searchTexts) => {
    const buttons = document.querySelectorAll('button, a.btn-primary, a.btn-secondary, a[href]');
    for (const btn of buttons) {
      const btnText = btn.textContent.toLowerCase().trim();
      for (const text of searchTexts) {
        if (btnText.includes(text.toLowerCase())) {
          btn.click();
          return true;
        }
      }
    }
    return false;
  }, texts);
}

async function keycloakLogin(page, credentials) {
  console.log(`  Logging in as ${credentials.user} (${credentials.role})...`);

  // Navigate to camper login
  await page.goto(`${CAMPER_URL}`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);

  // Click login button
  try {
    await page.evaluate(() => {
      const links = document.querySelectorAll('a, button');
      for (const el of links) {
        if (el.textContent.toLowerCase().includes('accedi') ||
            el.textContent.toLowerCase().includes('login') ||
            el.textContent.toLowerCase().includes('sign in')) {
          el.click();
          return;
        }
      }
    });
    await sleep(2000);
  } catch (e) {
    console.log('  Login button click failed...');
  }

  // Type credentials on Keycloak page
  try {
    await page.waitForSelector('#username', { timeout: 8000 });
    await humanType(page, '#username', credentials.user);
    await sleep(300);
    await humanType(page, '#password', credentials.pass);
    await sleep(500);
    await page.click('#kc-login');
    console.log(`  Credentials submitted for ${credentials.user}, waiting for redirect...`);
    await sleep(3000);
  } catch (e) {
    console.log('  KC login form not found -- may already be authenticated');
  }
}

async function keycloakLogout(page) {
  console.log('  Logging out...');
  try {
    // Try clicking logout link in the nav
    const loggedOut = await page.evaluate(() => {
      const links = document.querySelectorAll('a[href*="logout"], button[onclick*="logout"]');
      for (const el of links) {
        el.click();
        return true;
      }
      // Try nav link
      const navLinks = document.querySelectorAll('a');
      for (const el of navLinks) {
        if (el.textContent.toLowerCase().includes('esci') ||
            el.textContent.toLowerCase().includes('logout')) {
          el.click();
          return true;
        }
      }
      return false;
    });

    if (!loggedOut) {
      // Direct Keycloak logout URL
      await page.goto(`${CAMPER_URL}/logout`, { waitUntil: 'networkidle2', timeout: 10000 });
    }
    await sleep(2000);
  } catch (e) {
    console.log('  Logout failed, navigating to login page...');
    await page.goto(`${CAMPER_URL}`, { waitUntil: 'networkidle2', timeout: 10000 });
    await sleep(1000);
  }
}

async function muteMicrophones() {
  try {
    const sources = execSync('pactl list short sources 2>/dev/null').toString();
    for (const line of sources.split('\n')) {
      if (!line.trim()) continue;
      const parts = line.split('\t');
      const sourceId = parts[0];
      const sourceName = parts[1] || '';
      if (sourceName.includes('input') || sourceName.includes('source')) {
        execSync(`pactl set-source-mute ${sourceId} 1`);
        console.log(`  Muted: ${sourceName}`);
      }
    }
    console.log('  All microphones muted.');
  } catch (e) {
    console.log('  Warning: Could not mute mics:', e.message);
  }
}

async function unmuteMicrophones() {
  try {
    const sources = execSync('pactl list short sources 2>/dev/null').toString();
    for (const line of sources.split('\n')) {
      if (!line.trim()) continue;
      const parts = line.split('\t');
      const sourceId = parts[0];
      const sourceName = parts[1] || '';
      if (sourceName.includes('input') || sourceName.includes('source')) {
        execSync(`pactl set-source-mute ${sourceId} 0`);
      }
    }
    console.log('  Microphones unmuted.');
  } catch (e) { /* silent */ }
}

// ---------------------------------------------------------------------------
// Main recording flow
// ---------------------------------------------------------------------------

async function main() {
  console.log('='.repeat(60));
  console.log('CAMPER & TOUR EP3 -- "The Full Lifecycle"');
  console.log('One Job, Three Roles, Zero Paper');
  console.log('='.repeat(60));
  console.log('');
  console.log('CHECKLIST:');
  console.log('  [ ] Docker stack running (make up)');
  console.log('  [ ] OBS open with Screen Capture (PipeWire) source');
  console.log('  [ ] All content will be ZOOMED 200%');
  console.log('');
  console.log('ROLE SWITCHES:');
  console.log('  Simona (counter) -> Nino (manager) -> Maximo (mechanic) -> Nino (manager)');
  console.log('');

  console.log('[Pre-flight] Muting microphones...');
  await muteMicrophones();

  console.log('[Pre-flight] Launching Chrome in FULLSCREEN mode...');
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: [
      '--start-fullscreen',
      '--window-size=1920,1080',
      '--ignore-certificate-errors',
    ],
  });

  const pages = await browser.pages();
  const page = pages[0] || await browser.newPage();

  // ================================================================
  // OBS VERIFICATION SCREEN
  // ================================================================
  await page.setContent(`
    <html><body style="margin:0;background:#DC2626;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;">
      <div style="text-align:center;color:white;">
        <div style="font-size:140px;font-weight:900;text-shadow:4px 4px 0 #000;">OBS CHECK</div>
        <div style="font-size:56px;margin:40px 0;background:#e67e22;color:#000;padding:24px 80px;border-radius:16px;font-weight:bold;">
          DO YOU SEE THIS FULLSCREEN IN OBS?
        </div>
        <div style="font-size:36px;margin-top:30px;">YES &rarr; Hit Record in OBS, then press ENTER in terminal</div>
        <div style="font-size:36px;margin-top:10px;">NO &rarr; STOP. Fix OBS source first.</div>
        <div style="font-size:28px;margin-top:40px;background:rgba(0,0,0,0.3);padding:16px 40px;border-radius:8px;">
          CAMPER &amp; TOUR EP3 -- The Full Lifecycle (200% Zoom)
        </div>
        <div style="font-size:24px;margin-top:30px;opacity:0.7;">3 Role Switches: Simona &rarr; Nino &rarr; Maximo &rarr; Nino</div>
      </div>
    </body></html>
  `);

  console.log('');
  console.log('  CHECK your OBS preview -- do you see the red card FULLSCREEN?');
  console.log('  If YES: Hit Record in OBS, then press ENTER here.');
  console.log('  If NO:  Fix your OBS source.');
  console.log('');

  const readline = require('readline');
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  await new Promise(resolve => {
    rl.question('  >>> Press ENTER when OBS shows the red card FULLSCREEN... ', () => {
      rl.close();
      resolve();
    });
  });

  console.log('');
  for (let i = 15; i > 0; i--) {
    process.stdout.write(`\r  >>> Demo starts in ${i} seconds...  `);
    await sleep(1000);
  }
  process.stdout.write('\r  >>> GO!                              \n');
  await sleep(500);

  // ================================================================
  // SCENE 1: INTRO CARD (5s)
  // ================================================================
  console.log('\n--- SCENE 1: Intro Card ---');
  const introPath = path.resolve(__dirname, 'intro.html');
  await page.goto(`file://${introPath}`);
  await sleep(PAUSE.INTRO);

  // ================================================================
  // SCENE 2: SIMONA -- Counter Check-In (30s)
  // ================================================================
  console.log('\n--- SCENE 2: Simona -- Counter Check-In ---');
  await keycloakLogin(page, SIMONA);
  await sleep(PAUSE.SHORT);

  // Navigate to check-in
  console.log('  Navigating to /camper/checkin...');
  await page.goto(`${CAMPER_URL}/checkin`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Type a new plate
  console.log('  Typing new plate ZZ 777 AA...');
  try {
    await humanType(page, 'input[x-model="searchPlate"], input[type="text"]', 'ZZ 777 AA');
    await sleep(PAUSE.MEDIUM);
  } catch (e) {
    console.log('  Plate input not found:', e.message);
  }

  // Show "not found" state
  console.log('  Showing not found state...');
  await sleep(PAUSE.MEDIUM);

  // Click register new vehicle
  console.log('  Clicking Register New Vehicle...');
  await clickButtonByText(page, 'register', 'registra', 'new vehicle', 'nuovo');
  await sleep(PAUSE.LONG);

  // Show the registration form
  console.log('  Showing registration form...');
  await sleep(PAUSE.MEDIUM);

  // Show Simona's limited nav -- highlight what's missing
  console.log('  Showing Simona limited nav bar...');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // ================================================================
  // SCENE 3: SIMONA -- Access Denied (15s)
  // ================================================================
  console.log('\n--- SCENE 3: Simona -- Access Denied ---');
  console.log('  Trying to access /camper/quotations as counter...');
  await page.goto(`${CAMPER_URL}/quotations`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.LONG); // Show the access denied / empty / redirect

  // Try invoices too
  console.log('  Trying to access /camper/invoices as counter...');
  await page.goto(`${CAMPER_URL}/invoices`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // LOGOUT SIMONA, LOGIN NINO
  // ================================================================
  console.log('\n--- ROLE SWITCH: Simona -> Nino ---');
  await keycloakLogout(page);
  await sleep(1000);

  // ================================================================
  // SCENE 4: NINO -- Create Quotation (30s)
  // ================================================================
  console.log('\n--- SCENE 4: Nino -- Create Quotation ---');
  await keycloakLogin(page, NINO);
  await sleep(PAUSE.SHORT);

  // Show Nino's full nav -- more menu items than Simona
  console.log('  Showing Nino full nav bar (compare to Simona)...');
  await page.goto(`${CAMPER_URL}/dashboard`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.LONG);

  // Navigate to quotations
  console.log('  Navigating to /camper/quotations...');
  await page.goto(`${CAMPER_URL}/quotations`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show quotation list
  console.log('  Showing quotation list...');
  await sleep(PAUSE.LONG);

  // Open a quotation detail
  console.log('  Opening quotation detail...');
  try {
    const clicked = await page.evaluate(() => {
      const link = document.querySelector('a[href*="/quotations/"]');
      if (link) { link.click(); return true; }
      const rows = document.querySelectorAll('tr.cursor-pointer, tr[onclick]');
      if (rows.length > 0) { rows[0].click(); return true; }
      return false;
    });
    if (clicked) {
      await sleep(2000);
      await setZoom(page);
    }
  } catch (e) {
    console.log('  Quotation click failed:', e.message);
  }

  // Show line items + IVA + deposit
  console.log('  Showing line items, IVA, deposit...');
  await sleep(PAUSE.LONG);

  // Scroll to totals
  console.log('  Scrolling to totals...');
  await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'smooth' }));
  await sleep(PAUSE.XLONG);

  // ================================================================
  // SCENE 5: NINO -- Approve Job (15s)
  // ================================================================
  console.log('\n--- SCENE 5: Nino -- Approve Job ---');

  // Navigate to jobs
  console.log('  Navigating to /camper/jobs...');
  await page.goto(`${CAMPER_URL}/jobs`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show the job board
  console.log('  Showing job board...');
  await sleep(PAUSE.LONG);

  // Click on a job to show detail
  console.log('  Opening a job detail...');
  try {
    await page.evaluate(() => {
      const link = document.querySelector('a[href*="/jobs/"]');
      if (link) { link.click(); return true; }
      return false;
    });
    await sleep(2000);
    await setZoom(page);
  } catch (e) {
    console.log('  Job click failed');
  }

  // Show job detail with approve button
  console.log('  Showing job detail...');
  await sleep(PAUSE.LONG);

  // ================================================================
  // LOGOUT NINO, LOGIN MAXIMO
  // ================================================================
  console.log('\n--- ROLE SWITCH: Nino -> Maximo ---');
  await keycloakLogout(page);
  await sleep(1000);

  // ================================================================
  // SCENE 6: MAXIMO -- Mechanic Work Log (30s)
  // ================================================================
  console.log('\n--- SCENE 6: Maximo -- Mechanic Work Log ---');
  await keycloakLogin(page, MAXIMO);
  await sleep(PAUSE.SHORT);

  // Show Maximo's nav -- different from Nino and Simona
  console.log('  Showing Maximo nav bar (mechanic view)...');
  await page.goto(`${CAMPER_URL}/dashboard`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.LONG);

  // Navigate to jobs
  console.log('  Navigating to /camper/jobs (mechanic view)...');
  await page.goto(`${CAMPER_URL}/jobs`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show Maximo's job list
  console.log('  Showing Maximo job list...');
  await sleep(PAUSE.LONG);

  // Click on an assigned job
  console.log('  Opening assigned job...');
  try {
    await page.evaluate(() => {
      const link = document.querySelector('a[href*="/jobs/"]');
      if (link) { link.click(); return true; }
      return false;
    });
    await sleep(2000);
    await setZoom(page);
  } catch (e) {
    console.log('  Job click failed');
  }

  // Show job detail from mechanic perspective
  console.log('  Showing mechanic job detail...');
  await sleep(PAUSE.LONG);

  // Scroll to work log section
  console.log('  Scrolling to work log section...');
  await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll to mechanic notes
  console.log('  Scrolling to mechanic notes...');
  await page.evaluate(() => window.scrollTo({ top: 1000, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 7: MAXIMO -- Submit for Inspection (10s)
  // ================================================================
  console.log('\n--- SCENE 7: Maximo -- Submit for Inspection ---');
  // Show the submit button area
  console.log('  Showing submit for inspection button...');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // ================================================================
  // LOGOUT MAXIMO, LOGIN NINO
  // ================================================================
  console.log('\n--- ROLE SWITCH: Maximo -> Nino ---');
  await keycloakLogout(page);
  await sleep(1000);

  // ================================================================
  // SCENE 8: NINO -- Inspection & Complete (20s)
  // ================================================================
  console.log('\n--- SCENE 8: Nino -- Inspection & Complete ---');
  await keycloakLogin(page, NINO);
  await sleep(PAUSE.SHORT);

  // Navigate to jobs -- show inspection queue
  console.log('  Navigating to /camper/jobs...');
  await page.goto(`${CAMPER_URL}/jobs`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show job board with inspection items
  console.log('  Showing job board (inspection items visible)...');
  await sleep(PAUSE.LONG);

  // Open a job in inspection state
  console.log('  Opening job for inspection...');
  try {
    await page.evaluate(() => {
      const link = document.querySelector('a[href*="/jobs/"]');
      if (link) { link.click(); return true; }
      return false;
    });
    await sleep(2000);
    await setZoom(page);
  } catch (e) {
    console.log('  Job click failed');
  }

  // Show inspection detail
  console.log('  Showing inspection detail...');
  await sleep(PAUSE.LONG);

  // ================================================================
  // SCENE 9: NINO -- Generate Invoice (20s)
  // ================================================================
  console.log('\n--- SCENE 9: Nino -- Generate Invoice ---');
  console.log('  Navigating to /camper/invoices...');
  await page.goto(`${CAMPER_URL}/invoices`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show invoice list
  console.log('  Showing invoice list...');
  await sleep(PAUSE.LONG);

  // Scroll to see payment details
  console.log('  Scrolling to payment details...');
  await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // ================================================================
  // SCENE 10: NINO -- Vehicle Pickup (10s)
  // ================================================================
  console.log('\n--- SCENE 10: Nino -- Vehicle Pickup ---');
  console.log('  Navigating to /camper/checkin...');
  await page.goto(`${CAMPER_URL}/checkin`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show vehicle check-out flow
  console.log('  Showing vehicle lookup for checkout...');
  await sleep(PAUSE.LONG);

  // ================================================================
  // SCENE 11: OUTRO CARD (5s)
  // ================================================================
  console.log('\n--- SCENE 11: Outro Card ---');
  const outroPath = path.resolve(__dirname, 'outro.html');
  await page.goto(`file://${outroPath}`);
  await sleep(PAUSE.OUTRO);

  // ================================================================
  // DONE
  // ================================================================
  console.log('\n' + '='.repeat(60));
  console.log('RECORDING COMPLETE -- Stop OBS now');
  console.log('='.repeat(60));
  console.log('');

  await browser.close();
  await unmuteMicrophones();

  console.log('Post-production:');
  console.log('  1. Strip audio: ffmpeg -i raw.mp4 -an -c:v copy silent.mp4');
  console.log('  2. Trim OBS CHECK + desktop tail');
  console.log('  3. Add music: wholesome-kevin-macleod.mp3 at 12% volume');
  console.log('  4. Trim to exactly 3:00');
  console.log('');
}

main().catch(async err => {
  console.error('Demo recording failed:', err);
  await unmuteMicrophones();
  process.exit(1);
});
