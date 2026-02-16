#!/usr/bin/env node
/**
 * CAMPER & TOUR EP4 -- "The Workshop Floor" Demo Recording Script
 *
 * One manager, one morning, five bays, zero spreadsheets.
 * Nino opens the appointments board, handles arrivals, processes a walk-in,
 * assigns bays, and checks the weekly resource plan.
 *
 * HOW TO USE:
 * 1. Make sure Docker stack is running (make up)
 * 2. Open OBS, set source to "Screen Capture (PipeWire)"
 * 3. Run: node videos/camper-tour/DEMO-service-management/EP4/ct-ep4-record.js
 * 4. A bright RED "OBS CHECK" card fills the screen
 * 5. Check OBS PREVIEW -- do you see the red card FULLSCREEN?
 *    - YES: Hit Record in OBS, then press ENTER in terminal
 *    - NO:  Fix OBS source first.
 * 6. Demo runs automatically (~2-3 min). Don't touch anything.
 * 7. Stop OBS when console says "RECORDING COMPLETE"
 *
 * CRITICAL: All page content is ZOOMED 200% for readability on video.
 *
 * SCENES:
 *   1. Intro card (5s)
 *   2. Morning Appointments View (12s)
 *   3. Customer Arrives -- Sophie (10s)
 *   4. Assign Bay & Start Service (10s)
 *   5. Quick Walk-in (15s)
 *   6. Complete Tourist's Job (8s)
 *   7. Bay Timeline -- The Money Shot (20s)
 *   8. Outro card (5s)
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

// Only Nino in this episode -- one user, one perspective
const NINO = { user: 'nino', pass: 'helix_pass', role: 'manager' };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function setZoom(page) {
  await page.evaluate(() => { document.body.style.zoom = '2'; });
  await sleep(300);
}

async function humanType(page, selector, text) {
  await page.waitForSelector(selector, { visible: true, timeout: 5000 });
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

/**
 * Click a button within a specific customer's appointment card.
 * Finds the card by customer name (h4 text), then clicks the button matching buttonText.
 */
async function clickButtonOnCard(page, customerName, buttonText) {
  return page.evaluate((name, btnText) => {
    const allCards = document.querySelectorAll('.card');
    for (const card of allCards) {
      const nameEl = card.querySelector('h4');
      if (!nameEl) continue;
      if (!nameEl.textContent.toLowerCase().includes(name.toLowerCase())) continue;

      const buttons = card.querySelectorAll('button');
      for (const btn of buttons) {
        const text = btn.textContent.toLowerCase().trim();
        if (text.includes(btnText.toLowerCase())) {
          btn.click();
          return true;
        }
      }
    }
    return false;
  }, customerName, buttonText);
}

async function keycloakLogin(page, credentials) {
  console.log(`  Logging in as ${credentials.user} (${credentials.role})...`);

  // Navigate to camper with English language
  await page.goto(`${CAMPER_URL}?lang=en`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);

  // Click login button
  try {
    await page.evaluate(() => {
      const links = document.querySelectorAll('a, button');
      for (const el of links) {
        if (el.textContent.toLowerCase().includes('accedi') ||
            el.textContent.toLowerCase().includes('log in') ||
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
  console.log('CAMPER & TOUR EP4 -- "The Workshop Floor"');
  console.log('One Manager, One Morning, Zero Spreadsheets');
  console.log('='.repeat(60));
  console.log('');
  console.log('CHECKLIST:');
  console.log('  [ ] Docker stack running (make up)');
  console.log('  [ ] OBS open with Screen Capture (PipeWire) source');
  console.log('  [ ] All content will be ZOOMED 200%');
  console.log('');
  console.log('SINGLE USER: Nino (manager) -- no role switches');
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
          CAMPER &amp; TOUR EP4 -- The Workshop Floor (200% Zoom)
        </div>
        <div style="font-size:24px;margin-top:30px;opacity:0.7;">Single User: Nino (Manager) &mdash; Appointments + Bay Timeline</div>
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
  // SCENE 2: MORNING APPOINTMENTS VIEW (12s)
  // ================================================================
  console.log('\n--- SCENE 2: Morning Appointments View ---');
  await keycloakLogin(page, NINO);
  await sleep(PAUSE.SHORT);

  console.log('  Navigating to /camper/appointments...');
  await page.goto(`${CAMPER_URL}/appointments`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM); // Wait for Alpine to load + render data

  // PAUSE LONG on the board: Sophie scheduled left, Tourist in-service right, stats bar
  console.log('  Showing appointments board: Sophie (SCHEDULED), Tourist (IN_SERVICE + URGENT)...');
  await sleep(PAUSE.LONG);

  // ================================================================
  // Fetch IDs for later use
  // ================================================================
  console.log('  Fetching appointment and bay data via API...');
  let sophieId = null;
  let touristId = null;
  let electricalBayId = null;

  try {
    const ids = await page.evaluate(async () => {
      const token = sessionStorage.getItem('camper_token');
      const headers = { 'Authorization': 'Bearer ' + token, 'Accept': 'application/json' };

      const apptRes = await fetch('/api/v1/camper/appointments/today', { headers });
      const appointments = await apptRes.json();

      const bayRes = await fetch('/api/v1/camper/bays', { headers });
      const bays = await bayRes.json();

      const sophie = appointments.find(a =>
        a.customer_name && a.customer_name.toLowerCase().includes('sophie'));
      const tourist = appointments.find(a =>
        a.customer_name && a.customer_name.toLowerCase().includes('tourist'));
      const electrical = bays.find(b =>
        b.name && b.name.toLowerCase().includes('electrical'));

      return {
        sophieId: sophie ? sophie.id : null,
        touristId: tourist ? tourist.id : null,
        electricalBayId: electrical ? electrical.id : null,
      };
    });
    sophieId = ids.sophieId;
    touristId = ids.touristId;
    electricalBayId = ids.electricalBayId;
  } catch (e) {
    console.log('  WARN: Could not fetch IDs:', e.message);
  }

  console.log(`  Sophie: ${sophieId ? 'found' : 'NOT FOUND'}`);
  console.log(`  Tourist: ${touristId ? 'found' : 'NOT FOUND'}`);
  console.log(`  Electrical Bay: ${electricalBayId ? 'found' : 'NOT FOUND'}`);

  // ================================================================
  // SCENE 3: CUSTOMER ARRIVES -- SOPHIE (10s)
  // ================================================================
  console.log('\n--- SCENE 3: Customer Arrives -- Sophie ---');

  // Click "Arrived" button on Sophie's card
  console.log('  Clicking "Arrived" on Sophie\'s card...');
  let clicked = await clickButtonOnCard(page, 'Sophie', 'arrived');
  if (!clicked) clicked = await clickButtonOnCard(page, 'Sophie', 'arrivat');
  if (!clicked && sophieId) {
    console.log('  Button click failed, using API fallback...');
    await page.evaluate(async (id) => {
      const token = sessionStorage.getItem('camper_token');
      await fetch('/api/v1/camper/appointments/' + id + '/status', {
        method: 'PATCH',
        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'waiting' })
      });
    }, sophieId);
    await page.reload({ waitUntil: 'networkidle2' });
    await setZoom(page);
  }

  await sleep(PAUSE.SHORT);
  console.log('  Sophie status: SCHEDULED -> WAITING (arrival time populated)');
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 4: ASSIGN BAY & START SERVICE (10s)
  // ================================================================
  console.log('\n--- SCENE 4: Assign Bay & Start Service ---');

  // Select "Electrical Bay" from dropdown on Sophie's card
  if (electricalBayId) {
    console.log('  Selecting Electrical Bay from dropdown...');
    try {
      // Use page.select on the visible bay dropdown
      await page.select('[x-model="selectedBayId"]', electricalBayId);
    } catch (e) {
      console.log('  page.select failed, using evaluate fallback...');
      await page.evaluate((bayId) => {
        const sel = document.querySelector('select[x-model="selectedBayId"]');
        if (sel) {
          sel.value = bayId;
          sel.dispatchEvent(new Event('change', { bubbles: true }));
          sel.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }, electricalBayId);
    }
    await sleep(800);
  }

  // Click "Start Service" on Sophie's card
  console.log('  Clicking "Start Service" on Sophie\'s card...');
  clicked = await clickButtonOnCard(page, 'Sophie', 'start service');
  if (!clicked) clicked = await clickButtonOnCard(page, 'Sophie', 'inizio servizio');
  if (!clicked && sophieId) {
    console.log('  Button click failed, using API fallback...');
    await page.evaluate(async (id, bayId) => {
      const token = sessionStorage.getItem('camper_token');
      const body = { status: 'in_service' };
      if (bayId) body.bay_id = bayId;
      await fetch('/api/v1/camper/appointments/' + id + '/status', {
        method: 'PATCH',
        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
    }, sophieId, electricalBayId);
    await page.reload({ waitUntil: 'networkidle2' });
    await setZoom(page);
  }

  await sleep(PAUSE.SHORT);
  console.log('  Sophie status: WAITING -> IN_SERVICE (Electrical Bay assigned)');
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 5: QUICK WALK-IN (15s)
  // ================================================================
  console.log('\n--- SCENE 5: Quick Walk-in ---');

  // Click "+ Quick Walk-in" button
  console.log('  Opening Quick Walk-in modal...');
  await clickButtonByText(page, 'quick walk-in', 'walk-in rapido', '+ walk-in');
  await sleep(1500); // Wait for modal to appear

  // Type customer info at human speed
  try {
    console.log('  Typing customer name: Franco Rossi...');
    await humanType(page, '[x-model="quickWalkIn.customer_name"]', 'Franco Rossi');
    await sleep(500);

    console.log('  Typing description: Water leak in rear window...');
    await humanType(page, '[x-model="quickWalkIn.description"]', 'Water leak in rear window');
    await sleep(500);

    console.log('  Typing plate: PA 789 BC...');
    await humanType(page, '[x-model="quickWalkIn.vehicle_plate"]', 'PA 789 BC');
    await sleep(800);
  } catch (e) {
    console.log('  WARN: Modal typing failed:', e.message);
    // Fallback: create via API
    await page.evaluate(async () => {
      const token = sessionStorage.getItem('camper_token');
      await fetch('/api/v1/camper/appointments', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appointment_type: 'walk_in',
          customer_name: 'Franco Rossi',
          vehicle_plate: 'PA 789 BC',
          description: 'Water leak in rear window',
          scheduled_date: new Date().toISOString().split('T')[0],
          estimated_duration_minutes: 60,
          priority: 'normal'
        })
      });
    });
    await page.keyboard.press('Escape'); // Close modal if open
    await sleep(500);
    await page.reload({ waitUntil: 'networkidle2' });
    await setZoom(page);
  }

  // Submit the form
  console.log('  Submitting walk-in...');
  await clickButtonByText(page, 'add to queue', 'aggiungi alla coda', 'aggiungi');
  await sleep(PAUSE.SHORT); // Wait for modal close + data reload

  console.log('  Franco Rossi added to walk-in queue with position #1');
  await sleep(PAUSE.LONG);

  // ================================================================
  // SCENE 6: COMPLETE TOURIST'S JOB (8s)
  // ================================================================
  console.log('\n--- SCENE 6: Complete Tourist\'s Job ---');

  // Click "Completed" on Tourist's card (customer_name = "Tourist (walk-in)")
  console.log('  Clicking "Completed" on Tourist\'s card...');
  clicked = await clickButtonOnCard(page, 'Tourist', 'completed');
  if (!clicked) clicked = await clickButtonOnCard(page, 'Tourist', 'completat');
  if (!clicked && touristId) {
    console.log('  Button click failed, using API fallback...');
    await page.evaluate(async (id) => {
      const token = sessionStorage.getItem('camper_token');
      await fetch('/api/v1/camper/appointments/' + id + '/status', {
        method: 'PATCH',
        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'completed' })
      });
    }, touristId);
    await page.reload({ waitUntil: 'networkidle2' });
    await setZoom(page);
  }

  await sleep(PAUSE.SHORT);
  console.log('  Tourist job completed -- stats updated: 1 completed');
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 7: BAY TIMELINE -- THE MONEY SHOT (20s)
  // ================================================================
  console.log('\n--- SCENE 7: Bay Timeline -- The Money Shot ---');

  // Sync token to localStorage (bay_timeline.html reads from localStorage)
  await page.evaluate(() => {
    const token = sessionStorage.getItem('camper_token');
    if (token) localStorage.setItem('camper_token', token);
  });

  console.log('  Navigating to /camper/bay-timeline...');
  await page.goto(`${CAMPER_URL}/bay-timeline`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM); // Wait for grid render

  // PAUSE LONG on the weekly resource grid
  console.log('  Showing weekly resource grid: bays x days, color-coded job bars...');
  await sleep(PAUSE.LONG);

  // Navigate to next week
  console.log('  Clicking next week...');
  await clickButtonByText(page, 'next week', 'settimana succ');
  await sleep(PAUSE.MEDIUM);

  // Navigate back to this week
  console.log('  Clicking back to today...');
  await clickButtonByText(page, 'today', 'oggi');
  await sleep(PAUSE.MEDIUM);

  // Hover over a job bar to show tooltip
  console.log('  Hovering over a job bar for tooltip...');
  try {
    await page.waitForSelector('.job-bar', { timeout: 3000 });
    const jobBar = await page.$('.job-bar');
    if (jobBar) {
      await jobBar.hover();
      console.log('  Tooltip visible -- holding...');
      await sleep(PAUSE.XLONG);
    } else {
      console.log('  No job bars found on timeline');
      await sleep(PAUSE.LONG);
    }
  } catch (e) {
    console.log('  No job bars to hover:', e.message);
    await sleep(PAUSE.LONG);
  }

  // ================================================================
  // SCENE 8: OUTRO CARD (5s)
  // ================================================================
  console.log('\n--- SCENE 8: Outro Card ---');
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
  console.log('  2. Trim OBS CHECK card (use -c:v libx264 for precision, NOT -c:v copy)');
  console.log('  3. Stitch: intro-clip.mp4 + silent-trimmed.mp4 + outro-clip.mp4');
  console.log('  4. Add music: wholesome-kevin-macleod.mp3 at 12% volume');
  console.log('  5. MANDATORY: Play 10 seconds of raw recording to verify browser content');
  console.log('');
}

main().catch(async err => {
  console.error('Demo recording failed:', err);
  await unmuteMicrophones();
  process.exit(1);
});
