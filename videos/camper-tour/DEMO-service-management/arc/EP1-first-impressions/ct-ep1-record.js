#!/usr/bin/env node
/**
 * CAMPER & TOUR EP1 -- "First Impressions" Demo Recording Script
 *
 * Service Management for a Real Camper Service Shop in Trapani, Sicily.
 *
 * HOW TO USE:
 * 1. Make sure Docker stack is running (make up)
 * 2. Open OBS, set source to "Screen Capture (PipeWire)"
 * 3. Run: node videos/camper-tour/DEMO-service-management/EP1-first-impressions/ct-ep1-record.js
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
 *   2. Login & Dashboard (25s)
 *   3. Vehicle Check-In (25s)
 *   4. Job Board (20s)
 *   5. Job Detail -- MAX Roof Seal (35s -- MONEY SHOT)
 *   6. Customer Intelligence (20s)
 *   7. Outro card (5s)
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

async function clearAndType(page, selector, text) {
  await page.waitForSelector(selector, { timeout: 5000 });
  await page.click(selector, { clickCount: 3 }); // Select all
  await sleep(200);
  for (const char of text) {
    await page.keyboard.type(char, { delay: PAUSE.TYPE });
  }
}

async function clickButtonByText(page, ...texts) {
  return page.evaluate((searchTexts) => {
    const buttons = document.querySelectorAll('button, a.btn-primary, a.btn-secondary');
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
  // Mute ALL audio input sources so OBS records silent video
  try {
    const sources = execSync('pactl list short sources 2>/dev/null').toString();
    for (const line of sources.split('\n')) {
      if (!line.trim()) continue;
      const parts = line.split('\t');
      const sourceId = parts[0];
      const sourceName = parts[1] || '';
      // Mute input sources (microphones) -- skip monitor sources (they capture desktop audio)
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
  // Restore mic state after recording
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

// ---------------------------------------------------------------------------
// Main recording flow
// ---------------------------------------------------------------------------

async function main() {
  console.log('='.repeat(60));
  console.log('CAMPER & TOUR EP1 -- "First Impressions"');
  console.log('Service Management Demo Recording');
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
      '--start-fullscreen',           // F11 fullscreen -- covers taskbar + everything
      '--window-size=1920,1080',
      '--ignore-certificate-errors',
    ],
  });

  // Use the first page (avoids blank tab) and set viewport
  const pages = await browser.pages();
  const page = pages[0] || await browser.newPage();

  // ================================================================
  // OBS VERIFICATION SCREEN -- Confirm capture source is correct
  // Chrome is fullscreen. If OBS shows this card = you're good.
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
          CAMPER &amp; TOUR EP1 -- First Impressions (200% Zoom)
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

  // Wait for user to confirm OBS is capturing the right thing
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
  // SCENE 2: LOGIN & DASHBOARD (25s)
  // ================================================================
  console.log('\n--- SCENE 2: Login & Dashboard ---');
  console.log('  Navigating to /camper login page...');
  await page.goto(`${CAMPER_URL}`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);

  console.log('  Logging in as Nino (shop manager)...');
  await keycloakLogin(page, NINO);
  await sleep(PAUSE.SHORT);
  console.log('  Current URL:', page.url());

  // Dashboard loaded -- ZOOM 200%
  console.log('  Zooming to 200%...');
  await setZoom(page);
  await sleep(PAUSE.MEDIUM); // Let Alpine.js load data + viewer read stats

  // Show stats cards (pause LONG)
  console.log('  Showing dashboard stats cards...');
  await sleep(PAUSE.LONG);

  // Scroll down to active jobs table
  console.log('  Scrolling to active jobs table...');
  await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll back to top
  console.log('  Scrolling back to top...');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 3: VEHICLE CHECK-IN (25s)
  // ================================================================
  console.log('\n--- SCENE 3: Vehicle Check-In ---');
  console.log('  Navigating to /camper/checkin...');
  await page.goto(`${CAMPER_URL}/checkin`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.SHORT);

  // Type a known plate in the search input
  console.log('  Searching for plate TI 123456...');
  try {
    await humanType(page, 'input[x-model="searchPlate"]', 'TI 123456');
    await sleep(PAUSE.MEDIUM); // Wait for results to appear
  } catch (e) {
    console.log('  Plate search input not found, trying generic input...');
    try {
      await humanType(page, 'input[type="text"]', 'TI 123456');
      await sleep(PAUSE.MEDIUM);
    } catch (e2) {
      console.log('  No search input found:', e2.message);
    }
  }

  // Show vehicle details card
  console.log('  Showing vehicle details...');
  await sleep(PAUSE.LONG);

  // Clear search and type a fake plate
  console.log('  Clearing search, typing fake plate XX 999999...');
  try {
    const searchSelector = await page.$('input[x-model="searchPlate"]') ? 'input[x-model="searchPlate"]' : 'input[type="text"]';
    await clearAndType(page, searchSelector, 'XX 999999');
    await sleep(PAUSE.MEDIUM); // Show "not found" state
  } catch (e) {
    console.log('  Clear and retype failed:', e.message);
  }

  // Show "not found" state
  console.log('  Showing "not found" state...');
  await sleep(PAUSE.MEDIUM);

  // Click "Register New Vehicle" button to show the form
  console.log('  Clicking Register New Vehicle...');
  try {
    const clicked = await clickButtonByText(page, 'register', 'registra', 'new vehicle', 'nuovo');
    if (clicked) {
      console.log('  Register form opened');
    } else {
      console.log('  Register button not found');
    }
  } catch (e) {
    console.log('  Register button click failed:', e.message);
  }
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 4: JOB BOARD (20s)
  // ================================================================
  console.log('\n--- SCENE 4: Job Board ---');
  console.log('  Navigating to /camper/jobs...');
  await page.goto(`${CAMPER_URL}/jobs`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.MEDIUM); // Let the job list load

  // Click the Status filter dropdown, select "in_progress"
  console.log('  Filtering jobs by status: in_progress...');
  try {
    await page.evaluate(() => {
      const sel = document.querySelector('select[x-model*="status"], select[x-model*="filter"]');
      if (sel) {
        // Find in_progress option
        for (const opt of sel.options) {
          if (opt.value === 'in_progress' || opt.text.toLowerCase().includes('in progress')) {
            sel.value = opt.value;
            sel.dispatchEvent(new Event('change'));
            sel.dispatchEvent(new Event('input'));
            return true;
          }
        }
      }
      return false;
    });
    await sleep(PAUSE.MEDIUM);
  } catch (e) {
    console.log('  Status filter not found:', e.message);
  }

  // Clear filter back to all
  console.log('  Clearing status filter...');
  try {
    await page.evaluate(() => {
      const sel = document.querySelector('select[x-model*="status"], select[x-model*="filter"]');
      if (sel) {
        sel.value = '';
        sel.dispatchEvent(new Event('change'));
        sel.dispatchEvent(new Event('input'));
      }
    });
    await sleep(PAUSE.SHORT);
  } catch (e) {
    console.log('  Filter clear failed');
  }

  // Type "MAX" in the search input
  console.log('  Searching for MAX...');
  try {
    const searchInput = await page.$('input[x-model*="search"]') || await page.$('input[type="text"]');
    if (searchInput) {
      await humanType(page, 'input[x-model*="search"], input[type="text"]', 'MAX');
      await sleep(PAUSE.MEDIUM);
    }
  } catch (e) {
    console.log('  Job search input not found:', e.message);
  }

  // Clear search
  console.log('  Clearing search...');
  try {
    await page.evaluate(() => {
      const input = document.querySelector('input[x-model*="search"], input[type="text"]');
      if (input) {
        input.value = '';
        input.dispatchEvent(new Event('input'));
        input.dispatchEvent(new Event('change'));
      }
    });
    await sleep(PAUSE.SHORT);
  } catch (e) {
    console.log('  Search clear failed');
  }

  // Show the full board
  console.log('  Showing full job board...');
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 5: JOB DETAIL -- MAX ROOF SEAL (35s -- MONEY SHOT)
  // ================================================================
  console.log('\n--- SCENE 5: Job Detail -- MAX Roof Seal (MONEY SHOT) ---');

  // From the jobs page, click the MAX roof seal job row
  console.log('  Looking for MAX roof seal job...');
  try {
    const clicked = await page.evaluate(() => {
      // Try clicking a table row or link that contains the MAX/seal job
      const links = document.querySelectorAll('a[href*="/jobs/"], tr[onclick], tr.cursor-pointer, tr');
      for (const el of links) {
        const text = (el.textContent || '').toLowerCase();
        if (text.includes('seal') || text.includes('roof') || text.includes('ti 123456')) {
          // If it's a link, click it directly
          const link = el.querySelector('a[href*="/jobs/"]') || el.closest('a[href*="/jobs/"]');
          if (link) { link.click(); return true; }
          el.click();
          return true;
        }
      }
      return false;
    });

    if (!clicked) {
      // Navigate via API -- find the MAX roof seal job ID
      console.log('  Click failed, navigating via API...');
      const jobId = await page.evaluate(async () => {
        const token = sessionStorage.getItem('camper_token') || sessionStorage.getItem('token');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        try {
          const resp = await fetch('/api/v1/camper/jobs?limit=200', { headers });
          if (resp.ok) {
            const jobs = await resp.json();
            // PRIORITY 1: Look for seal/roof job (the real MAX story)
            for (const j of jobs) {
              const text = ((j.title || '') + ' ' + (j.description || '')).toLowerCase();
              if (text.includes('seal') || text.includes('roof')) return j.id;
            }
            // PRIORITY 2: Look for vehicle plate TI 123456 (MAX)
            for (const j of jobs) {
              const plate = (j.vehicle_plate || j.vehicle?.registration_plate || '').toUpperCase();
              if (plate.includes('TI 123456') || plate.includes('TI123456')) return j.id;
            }
            // PRIORITY 3: Look for "water damage" or "inspection"
            for (const j of jobs) {
              const text = ((j.title || '') + ' ' + (j.description || '')).toLowerCase();
              if (text.includes('water damage') || text.includes('inspection')) return j.id;
            }
            // NO FALLBACK -- don't grab a random job
            console.log('  WARNING: MAX job not found in API. Jobs found:', jobs.map(j => j.title));
          }
        } catch (e) { /* ignore */ }
        return null;
      });

      if (jobId) {
        console.log(`  Found job ID: ${jobId}, navigating directly...`);
        await page.goto(`${CAMPER_URL}/jobs/${jobId}`, { waitUntil: 'networkidle2', timeout: 15000 });
        await setZoom(page);
      } else {
        console.log('  WARNING: Could not find MAX job via API. Navigating to /camper/jobs/1 as fallback...');
        await page.goto(`${CAMPER_URL}/jobs/1`, { waitUntil: 'networkidle2', timeout: 15000 });
        await setZoom(page);
      }
    } else {
      // Wait for navigation after click
      await sleep(2000);
      await setZoom(page);
    }
  } catch (e) {
    console.log('  Job row click failed:', e.message);
  }

  // Pause on the header (job number, status, vehicle) -- LONG
  console.log('  Showing job header (number, status, vehicle)...');
  await sleep(PAUSE.LONG);

  // Scroll to deposit section
  console.log('  Scrolling to deposit section...');
  await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Scroll to inspection section
  console.log('  Scrolling to inspection section...');
  await page.evaluate(() => window.scrollTo({ top: 800, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Scroll to quote section showing hours and costs
  console.log('  Scrolling to quote section (hours + costs)...');
  await page.evaluate(() => window.scrollTo({ top: 1200, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll to work section
  console.log('  Scrolling to work section...');
  await page.evaluate(() => window.scrollTo({ top: 1600, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll to mechanic notes
  console.log('  Scrolling to mechanic notes...');
  await page.evaluate(() => window.scrollTo({ top: 2000, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Scroll to timeline
  console.log('  Scrolling to timeline...');
  await page.evaluate(() => window.scrollTo({ top: 2400, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Scroll to follow-up reminders
  console.log('  Scrolling to follow-up reminders...');
  await page.evaluate(() => window.scrollTo({ top: 2800, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 6: CUSTOMER INTELLIGENCE (20s)
  // ================================================================
  console.log('\n--- SCENE 6: Customer Intelligence ---');
  console.log('  Navigating to /camper/customers...');
  await page.goto(`${CAMPER_URL}/customers`, { waitUntil: 'networkidle2', timeout: 15000 });
  await setZoom(page);
  await sleep(PAUSE.SHORT);

  // Search for Angelo
  console.log('  Searching for Angelo...');
  try {
    await humanType(page, 'input[x-model="searchQuery"]', 'Angelo');
    await sleep(PAUSE.SHORT);
  } catch (e) {
    console.log('  searchQuery input not found, trying generic input...');
    try {
      await humanType(page, 'input[type="text"]', 'Angelo');
      await sleep(PAUSE.SHORT);
    } catch (e2) {
      console.log('  Customer search input not found:', e2.message);
    }
  }

  // Click the Angelo customer card to expand it
  console.log('  Expanding Angelo customer card...');
  try {
    await page.evaluate(() => {
      const cards = document.querySelectorAll('[\\@click*="toggleCustomer"], .cursor-pointer, [\\@click*="toggle"]');
      for (const card of cards) {
        const text = (card.textContent || '').toLowerCase();
        if (text.includes('angelo') || text.includes('kenel')) {
          card.click();
          return true;
        }
      }
      // Fallback: click first clickable card
      if (cards.length > 0) {
        cards[0].click();
        return true;
      }
      return false;
    });
  } catch (e) {
    console.log('  Customer card expand failed:', e.message);
  }

  // Show vehicles and recent jobs
  console.log('  Showing customer vehicles and recent jobs...');
  await sleep(PAUSE.LONG);

  // Scroll down to see full details
  console.log('  Scrolling to full customer details...');
  await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 7: OUTRO CARD (5s)
  // ================================================================
  console.log('\n--- SCENE 7: Outro Card ---');
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
  console.log('  3. Stitch with intro/outro clips:');
  console.log('     node scripts/video-stitch.js \\');
  console.log('       --intro videos/camper-tour/DEMO-service-management/intro.png \\');
  console.log('       --content trimmed.mp4 \\');
  console.log('       --outro videos/camper-tour/DEMO-service-management/outro.png');
  console.log('');
  console.log('  4. Add voiceover (see voice-recordings/ folder)');
  console.log('');
}

main().catch(async err => {
  console.error('Demo recording failed:', err);
  await unmuteMicrophones();
  process.exit(1);
});
