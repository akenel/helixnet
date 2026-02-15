#!/usr/bin/env node
/**
 * CAMPER & TOUR EP2 -- "Quote to Invoice" Demo Recording Script
 *
 * The money flow: Quotations, Purchase Orders, Invoices,
 * Calendar, Bay Timeline, Appointments.
 *
 * HOW TO USE:
 * 1. Make sure Docker stack is running (make up)
 * 2. Open OBS, set source to "Screen Capture (PipeWire)"
 * 3. Run: node videos/camper-tour/DEMO-service-management/EP2/ct-ep2-record.js
 *    - Script mutes your microphones automatically
 *    - Chrome opens FULLSCREEN (covers terminal + taskbar)
 * 4. A bright RED "OBS CHECK" card fills the screen
 * 5. Check OBS PREVIEW -- do you see the red card FULLSCREEN?
 *    - YES: Hit Record in OBS, then press ENTER in terminal
 *    - NO:  Click Chrome + press F11 to force fullscreen, or fix OBS source
 * 6. Demo runs automatically (~3-4 min). Don't touch anything.
 * 7. Stop OBS when console says "RECORDING COMPLETE"
 * 8. Mics are automatically unmuted when script exits
 *
 * CRITICAL: All page content is ZOOMED 200% for readability on video.
 *
 * Total runtime: ~3:30
 *
 * SCENES:
 *   1. Intro card (5s)
 *   2. Login & Quotation List (25s)
 *   3. Quotation Detail -- Line Items + IVA (35s -- MONEY SHOT)
 *   4. Purchase Orders (25s)
 *   5. Invoice Generation (25s)
 *   6. Calendar View (20s)
 *   7. Bay Timeline (25s)
 *   8. Appointments -- Booked + Walk-In (20s)
 *   9. Outro card (5s)
 */

const puppeteer = require('puppeteer');
const path = require('path');
const { execSync } = require('child_process');
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PAUSE = {
  SHORT: 2500,     // Quick view
  MEDIUM: 4000,    // Read content
  LONG: 6000,      // Study screen
  XLONG: 8000,     // Money shots -- let viewer absorb
  INTRO: 5000,     // Title card hold
  OUTRO: 5000,     // Recap card hold
  TYPE: 90,        // Per character (human typing speed)
};

const BASE_URL = 'https://helix.local';
const CAMPER_URL = `${BASE_URL}/camper`;

// Demo users
const NINO = { user: 'nino', pass: 'helix_pass' };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function setZoom(page) {
  await page.evaluate(() => { document.body.style.zoom = '2'; });
  await sleep(300); // Let reflow settle
}

async function humanType(page, selector, text) {
  await page.waitForSelector(selector, { timeout: 5000 });
  await page.focus(selector);
  await sleep(300);
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
  // Click the login button on the Camper & Tour login page
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
    console.log('  Login button click failed, trying KC directly...');
  }

  // Now on Keycloak login page -- type credentials
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
    console.log('  Warning: Could not mute mics with pactl:', e.message);
    console.log('  Please mute manually in OBS Audio Mixer.');
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
  } catch (e) {
    // Silent fail on cleanup
  }
}

// Helper: find a quotation/job/entity ID via API
async function findEntityId(page, endpoint, matchFn) {
  return page.evaluate(async (ep, matchStr) => {
    const token = sessionStorage.getItem('camper_token') || sessionStorage.getItem('token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
    try {
      const resp = await fetch(ep, { headers });
      if (resp.ok) {
        const items = await resp.json();
        // matchStr is evaluated as a simple field check
        if (Array.isArray(items) && items.length > 0) {
          return items[0].id;
        }
      }
    } catch (e) { /* ignore */ }
    return null;
  }, endpoint, matchFn);
}

// ---------------------------------------------------------------------------
// Main recording flow
// ---------------------------------------------------------------------------

async function main() {
  console.log('='.repeat(60));
  console.log('CAMPER & TOUR EP2 -- "Quote to Invoice"');
  console.log('The Money Flow -- Demo Recording');
  console.log('='.repeat(60));
  console.log('');
  console.log('CHECKLIST:');
  console.log('  [ ] Docker stack running (make up)');
  console.log('  [ ] OBS open with Screen Capture (PipeWire) source');
  console.log('  [ ] All content will be ZOOMED 200%');
  console.log('');

  // Mute microphones BEFORE launching browser
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
          CAMPER &amp; TOUR EP2 -- Quote to Invoice (200% Zoom)
        </div>
        <div style="font-size:24px;margin-top:30px;opacity:0.7;">Chrome should be FULLSCREEN (no taskbar, no terminal visible)</div>
        <div style="font-size:24px;margin-top:8px;opacity:0.7;">If you see a terminal behind this, press F11 on Chrome first</div>
      </div>
    </body></html>
  `);

  console.log('');
  console.log('  Chrome should now be FULLSCREEN (covering everything).');
  console.log('  If you can still see the terminal BEHIND Chrome:');
  console.log('    -> Click the Chrome window, then press F11');
  console.log('');
  console.log('  CHECK your OBS preview -- do you see the red card FULLSCREEN?');
  console.log('  If YES: Hit Record in OBS, then press ENTER here.');
  console.log('  If NO:  Fix your OBS source (use Screen Capture, not Window Capture).');
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
  console.log('  OBS confirmed. You have 15 seconds to:');
  console.log('    1. Switch to Chrome (click it or Alt+Tab)');
  console.log('    2. Verify Chrome is FULLSCREEN in OBS preview');
  console.log('    3. Sit back and relax');
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
  console.log('  Showing intro card for 5 seconds...');
  await sleep(PAUSE.INTRO);

  // ================================================================
  // SCENE 2: LOGIN & QUOTATION LIST (25s)
  // ================================================================
  console.log('\n--- SCENE 2: Login & Quotation List ---');
  console.log('  Navigating to /camper login page...');
  await page.goto(`${CAMPER_URL}`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);

  console.log('  Logging in as Nino (shop manager)...');
  await keycloakLogin(page, NINO);
  await sleep(PAUSE.SHORT);
  console.log('  Current URL:', page.url());

  // Navigate to quotations
  console.log('  Navigating to /camper/quotations...');
  await page.goto(`${CAMPER_URL}/quotations`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show the quotation list
  console.log('  Showing quotation list...');
  await sleep(PAUSE.LONG);

  // Scroll to see more quotations
  console.log('  Scrolling through quotation list...');
  await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Scroll back to top
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 3: QUOTATION DETAIL -- LINE ITEMS + IVA (35s -- MONEY SHOT)
  // ================================================================
  console.log('\n--- SCENE 3: Quotation Detail (MONEY SHOT) ---');

  // Click first quotation or navigate via API
  console.log('  Looking for a quotation to open...');
  try {
    const clicked = await page.evaluate(() => {
      const links = document.querySelectorAll('a[href*="/quotations/"], tr[onclick], tr.cursor-pointer, tr');
      for (const el of links) {
        const text = (el.textContent || '').toLowerCase();
        if (text.includes('quo-') || text.includes('seal') || text.includes('roof')) {
          const link = el.querySelector('a[href*="/quotations/"]') || el.closest('a[href*="/quotations/"]');
          if (link) { link.click(); return true; }
          el.click();
          return true;
        }
      }
      // Fallback: click first row with a quotation link
      const firstLink = document.querySelector('a[href*="/quotations/"]');
      if (firstLink) { firstLink.click(); return true; }
      return false;
    });

    if (!clicked) {
      console.log('  Click failed, navigating via API...');
      const quoteId = await findEntityId(page, '/api/v1/camper/quotations?limit=10');
      if (quoteId) {
        await page.goto(`${CAMPER_URL}/quotations/${quoteId}`, { waitUntil: 'networkidle2', timeout: 15000 });
        await setZoom(page);
      }
    } else {
      await sleep(2000);
      await setZoom(page);
    }
  } catch (e) {
    console.log('  Quotation click failed:', e.message);
  }

  // Pause on header (quote number, status, customer, date)
  console.log('  Showing quotation header...');
  await sleep(PAUSE.LONG);

  // Scroll to line items table
  console.log('  Scrolling to line items...');
  await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll to IVA calculation + totals
  console.log('  Scrolling to IVA calculation + totals...');
  await page.evaluate(() => window.scrollTo({ top: 800, behavior: 'smooth' }));
  await sleep(PAUSE.XLONG); // MONEY SHOT -- let viewer absorb the numbers

  // Scroll to deposit section
  console.log('  Scrolling to deposit section...');
  await page.evaluate(() => window.scrollTo({ top: 1200, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll to action buttons (Send, Accept, Reject)
  console.log('  Scrolling to action buttons...');
  await page.evaluate(() => window.scrollTo({ top: 1600, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 4: PURCHASE ORDERS (25s)
  // ================================================================
  console.log('\n--- SCENE 4: Purchase Orders ---');
  console.log('  Navigating to /camper/purchase-orders...');
  await page.goto(`${CAMPER_URL}/purchase-orders`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show PO list with statuses
  console.log('  Showing purchase order list...');
  await sleep(PAUSE.LONG);

  // Scroll to see more POs
  console.log('  Scrolling through PO list...');
  await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll back to top
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 5: INVOICE GENERATION (25s)
  // ================================================================
  console.log('\n--- SCENE 5: Invoices ---');
  console.log('  Navigating to /camper/invoices...');
  await page.goto(`${CAMPER_URL}/invoices`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show invoice list
  console.log('  Showing invoice list...');
  await sleep(PAUSE.LONG);

  // Scroll to see payment status and amounts
  console.log('  Scrolling to see payment details...');
  await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll back
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 6: CALENDAR VIEW (20s)
  // ================================================================
  console.log('\n--- SCENE 6: Calendar View ---');
  console.log('  Navigating to /camper/calendar...');
  await page.goto(`${CAMPER_URL}/calendar`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show the weekly calendar
  console.log('  Showing weekly calendar...');
  await sleep(PAUSE.LONG);

  // Scroll to see more days
  console.log('  Scrolling through calendar...');
  await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Scroll back
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 7: BAY TIMELINE (25s)
  // ================================================================
  console.log('\n--- SCENE 7: Bay Timeline ---');
  console.log('  Navigating to /camper/bay-timeline...');
  await page.goto(`${CAMPER_URL}/bay-timeline`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show the bay grid -- 5 bays across the week
  console.log('  Showing bay timeline grid...');
  await sleep(PAUSE.LONG);

  // Scroll right/down to see more days
  console.log('  Scrolling through bay timeline...');
  await page.evaluate(() => window.scrollTo({ top: 300, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll to show all 5 bays
  console.log('  Showing all 5 bays...');
  await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Scroll back
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 8: APPOINTMENTS -- BOOKED + WALK-IN (20s)
  // ================================================================
  console.log('\n--- SCENE 8: Appointments ---');
  console.log('  Navigating to /camper/appointments...');
  await page.goto(`${CAMPER_URL}/appointments`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM);

  // Show booked appointments section
  console.log('  Showing booked appointments...');
  await sleep(PAUSE.LONG);

  // Scroll to walk-in queue
  console.log('  Scrolling to walk-in queue...');
  await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll back
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 9: OUTRO CARD (5s)
  // ================================================================
  console.log('\n--- SCENE 9: Outro Card ---');
  const outroPath = path.resolve(__dirname, 'outro.html');
  await page.goto(`file://${outroPath}`);
  console.log('  Showing outro card for 5 seconds...');
  await sleep(PAUSE.OUTRO);

  // ================================================================
  // DONE
  // ================================================================
  console.log('\n' + '='.repeat(60));
  console.log('RECORDING COMPLETE -- Stop OBS now');
  console.log('='.repeat(60));
  console.log('');

  await browser.close();

  // Restore mic state
  await unmuteMicrophones();

  console.log('Post-production:');
  console.log('  1. Strip audio from raw recording:');
  console.log('     ffmpeg -i raw.mp4 -an -c:v copy silent.mp4');
  console.log('');
  console.log('  2. Trim OBS CHECK card from start (find the cut point):');
  console.log('     ffplay silent.mp4   # note timestamp where intro card appears');
  console.log('     ffmpeg -i silent.mp4 -ss <START> -c copy trimmed.mp4');
  console.log('');
  console.log('  3. Add background music:');
  console.log('     ffmpeg -i trimmed.mp4 -i wholesome-kevin-macleod.mp3 \\');
  console.log('       -filter_complex "[1:a]volume=0.15,afade=t=out:st=200:d=5[music]" \\');
  console.log('       -map 0:v -map "[music]" -c:v copy -c:a aac -shortest final.mp4');
  console.log('');
  console.log('  4. Add voiceover (see voiceover-script.md)');
  console.log('');
}

main().catch(async err => {
  console.error('Demo recording failed:', err);
  await unmuteMicrophones();
  process.exit(1);
});
