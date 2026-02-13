#!/usr/bin/env node
/**
 * Camper & Tour -- Service Management Demo Recording Script
 *
 * HOW TO USE:
 * 1. Make sure Docker stack is running (docker compose up -d)
 * 2. Close ALL browser windows
 * 3. Open OBS, set source to Screen Capture (PipeWire)
 * 4. Hit Record in OBS
 * 5. Run: node scripts/camper-demo-record.js
 * 6. Stop OBS when the console says "RECORDING COMPLETE"
 *
 * Total runtime: ~4:00
 *
 * SCENES:
 *   1. Intro card (5s)
 *   2. Login as Nino (15s)
 *   3. Dashboard overview (25s)
 *   4. Vehicle check-in -- search MAX by plate (20s)
 *   5. Vehicle check-in -- new vehicle form (20s)
 *   6. Job board -- all active work (20s)
 *   7. Job detail -- MAX roof seal (30s)
 *   8. Quote approval -- Sophie's gas inspection (20s)
 *   9. Customer lookup -- search Angelo (15s)
 *  10. Outro card (5s)
 */

const puppeteer = require('puppeteer');
const path = require('path');
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
const API_URL = `${BASE_URL}/api/v1/camper`;

// Demo user -- Nino (manager, full access)
const DEMO_USER = 'nino';
const DEMO_PASS = 'helix_pass';

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

async function main() {
  console.log('='.repeat(60));
  console.log('CAMPER & TOUR -- Service Management Demo');
  console.log('='.repeat(60));
  console.log('');
  console.log('CHECKLIST:');
  console.log('  [ ] Docker stack running');
  console.log('  [ ] OBS recording (Screen Capture)');
  console.log('  [ ] All other browser windows closed');
  console.log('');
  console.log('Starting in 3 seconds...');
  await sleep(3000);

  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: [
      '--start-maximized',
      '--window-size=1920,1080',
      '--ignore-certificate-errors',
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // ================================================================
  // SCENE 1: INTRO CARD (5s)
  // ================================================================
  console.log('\n--- SCENE 1: Intro Card ---');
  const introPath = path.resolve(__dirname, '../videos/camper-tour/DEMO-service-management/intro.html');
  await page.goto(`file://${introPath}`);
  await sleep(PAUSE.INTRO);

  // ================================================================
  // SCENE 2: LOGIN (15s)
  // ================================================================
  console.log('\n--- SCENE 2: Login as Nino ---');
  await page.goto(`${CAMPER_URL}`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);

  // Click the login button -- this redirects to Keycloak
  try {
    // Look for the login button on the camper login page
    const loginBtn = await page.$('a[href*="keycloak"], button[onclick*="login"], a.login-btn, [x-on\\:click*="login"]');
    if (loginBtn) {
      await loginBtn.click();
    } else {
      // Try clicking any prominent button/link
      await page.evaluate(() => {
        const links = document.querySelectorAll('a, button');
        for (const el of links) {
          if (el.textContent.toLowerCase().includes('login') ||
              el.textContent.toLowerCase().includes('accedi')) {
            el.click();
            return;
          }
        }
      });
    }
    await sleep(2000);
  } catch (e) {
    console.log('  Login button click failed, trying direct KC URL...');
  }

  // Now on Keycloak login page -- type credentials
  try {
    await page.waitForSelector('#username', { timeout: 8000 });
    await humanType(page, '#username', DEMO_USER);
    await sleep(300);
    await humanType(page, '#password', DEMO_PASS);
    await sleep(500);
    await page.click('#kc-login');
    console.log('  Credentials submitted, waiting for redirect...');
    await sleep(3000);
  } catch (e) {
    console.log('  KC login form not found -- may already be authenticated');
  }

  // Should now be on dashboard with token in URL hash
  await sleep(PAUSE.SHORT);
  console.log('  Current URL:', page.url());

  // ================================================================
  // SCENE 3: DASHBOARD (25s)
  // ================================================================
  console.log('\n--- SCENE 3: Dashboard Overview ---');
  // Dashboard should have loaded with stats and active jobs
  await sleep(PAUSE.MEDIUM); // Let Alpine.js load data

  // Slowly scroll down to show active jobs table
  await page.evaluate(() => window.scrollTo({ top: 300, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll to quick actions
  await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Scroll back to top
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 4: VEHICLE CHECK-IN -- Search MAX (20s)
  // ================================================================
  console.log('\n--- SCENE 4: Vehicle Check-In -- Search MAX ---');
  await page.goto(`${CAMPER_URL}/checkin`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);

  // Type plate number in search
  try {
    // Find the plate search input
    const searchInput = await page.$('input[placeholder*="arga"], input[placeholder*="plate"], input[x-model*="plate"], input[x-model*="search"]');
    if (searchInput) {
      await humanType(page, 'input[placeholder*="arga"], input[placeholder*="plate"], input[x-model*="plate"], input[x-model*="search"]', 'TI 123456');
    } else {
      // Try first visible text input
      await humanType(page, 'input[type="text"]', 'TI 123456');
    }
    await sleep(500);

    // Click search button or press Enter
    await page.keyboard.press('Enter');
    await sleep(PAUSE.MEDIUM);
  } catch (e) {
    console.log('  Search input not found, trying alternative...');
  }

  // Vehicle card should now show MAX's info
  await sleep(PAUSE.LONG);

  // ================================================================
  // SCENE 5: VEHICLE CHECK-IN -- New Vehicle (20s)
  // ================================================================
  console.log('\n--- SCENE 5: New Vehicle Registration ---');
  // Clear and search for an unknown plate
  try {
    const searchInput = await page.$('input[type="text"]');
    if (searchInput) {
      await clearAndType(page, 'input[type="text"]', 'XX 999 ZZ');
      await sleep(300);
      await page.keyboard.press('Enter');
      await sleep(PAUSE.MEDIUM);
    }
  } catch (e) {
    console.log('  Could not clear search for new vehicle demo');
  }

  // Show the "not found" / registration form
  await sleep(PAUSE.LONG);

  // ================================================================
  // SCENE 6: JOB BOARD (20s)
  // ================================================================
  console.log('\n--- SCENE 6: Job Board ---');
  await page.goto(`${CAMPER_URL}/jobs`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.MEDIUM);

  // Let the job list load
  await sleep(PAUSE.LONG);

  // Scroll to see all jobs if needed
  await page.evaluate(() => window.scrollTo({ top: 300, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Scroll back
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 7: JOB DETAIL -- MAX Seal Inspection (30s -- MONEY SHOT)
  // ================================================================
  console.log('\n--- SCENE 7: Job Detail -- MAX Roof Seal ---');

  // Click the first job row (MAX seal inspection should be first or find by title)
  try {
    const clicked = await page.evaluate(() => {
      const rows = document.querySelectorAll('tr[class*="cursor"], tr[x-on\\:click], [x-on\\:click*="job"], a[href*="/jobs/"]');
      for (const row of rows) {
        const text = row.textContent || '';
        if (text.includes('seal') || text.includes('JOB-20260206') || text.includes('TI 123456')) {
          row.click();
          return true;
        }
      }
      // Fallback: click first job row
      const firstRow = document.querySelector('tr[class*="cursor"], [x-on\\:click*="job"]');
      if (firstRow) { firstRow.click(); return true; }
      return false;
    });

    if (!clicked) {
      // Navigate directly via API -- find MAX's job ID
      console.log('  Navigating to MAX seal job via URL...');
      // We'll try to get the job list and find the right ID
      const response = await page.evaluate(async () => {
        const token = sessionStorage.getItem('camper_token');
        if (!token) return null;
        const resp = await fetch('/api/v1/camper/jobs?status=IN_PROGRESS', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resp.ok) {
          const jobs = await resp.json();
          for (const job of jobs) {
            if (job.title && job.title.includes('seal')) return job.id;
          }
          if (jobs.length > 0) return jobs[0].id;
        }
        return null;
      });

      if (response) {
        await page.goto(`${CAMPER_URL}/jobs/${response}`, { waitUntil: 'networkidle2', timeout: 15000 });
      }
    }
  } catch (e) {
    console.log('  Job click failed:', e.message);
  }

  await sleep(PAUSE.MEDIUM);

  // Slowly scroll through the job detail sections
  await page.evaluate(() => window.scrollTo({ top: 300, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll to work performed / mechanic notes
  await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll to timeline / follow-up
  await page.evaluate(() => window.scrollTo({ top: 900, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Back to top
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 8: QUOTE APPROVAL -- Sophie's Gas Inspection (20s)
  // ================================================================
  console.log('\n--- SCENE 8: Quote Approval ---');

  // Go back to job board, find Sophie's QUOTED job
  await page.goto(`${CAMPER_URL}/jobs`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);

  // Click Sophie's gas inspection job
  try {
    const clicked = await page.evaluate(() => {
      const rows = document.querySelectorAll('tr[class*="cursor"], tr[x-on\\:click], [x-on\\:click*="job"], a[href*="/jobs/"]');
      for (const row of rows) {
        const text = row.textContent || '';
        if (text.includes('gas') || text.includes('Gas') || text.includes('JOB-20260213-0001') || text.includes('AB 123 CD')) {
          row.click();
          return true;
        }
      }
      return false;
    });

    if (!clicked) {
      // Find via API
      const jobId = await page.evaluate(async () => {
        const token = sessionStorage.getItem('camper_token');
        if (!token) return null;
        const resp = await fetch('/api/v1/camper/jobs?status=QUOTED', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resp.ok) {
          const jobs = await resp.json();
          for (const job of jobs) {
            if (job.title && job.title.includes('gas')) return job.id;
          }
          if (jobs.length > 0) return jobs[0].id;
        }
        return null;
      });

      if (jobId) {
        await page.goto(`${CAMPER_URL}/jobs/${jobId}`, { waitUntil: 'networkidle2', timeout: 15000 });
      }
    }
  } catch (e) {
    console.log('  Sophie job click failed:', e.message);
  }

  await sleep(PAUSE.MEDIUM);

  // Click the Approve button
  try {
    await page.evaluate(() => {
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        const text = btn.textContent.toLowerCase();
        if (text.includes('approv') || text.includes('approve')) {
          btn.click();
          return;
        }
      }
    });
    console.log('  Approve button clicked');
  } catch (e) {
    console.log('  Approve button not found');
  }

  await sleep(PAUSE.LONG);

  // ================================================================
  // SCENE 9: CUSTOMER LOOKUP (15s)
  // ================================================================
  console.log('\n--- SCENE 9: Customer Lookup ---');
  await page.goto(`${CAMPER_URL}/customers`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);

  // Search for Angelo
  try {
    const searchInput = await page.$('input[placeholder*="erca"], input[placeholder*="search"], input[type="text"]');
    if (searchInput) {
      await humanType(page, 'input[type="text"]', 'Angelo');
      await sleep(500);
      await page.keyboard.press('Enter');
    }
  } catch (e) {
    console.log('  Customer search input not found');
  }

  await sleep(PAUSE.MEDIUM);

  // Expand Angelo's profile to show vehicles + jobs
  try {
    await page.evaluate(() => {
      const cards = document.querySelectorAll('[x-on\\:click*="expand"], [x-on\\:click*="toggle"], .cursor-pointer');
      for (const card of cards) {
        const text = card.textContent || '';
        if (text.includes('Angelo') || text.includes('Kenel')) {
          card.click();
          return;
        }
      }
      // Fallback: click first expandable card
      if (cards.length > 0) cards[0].click();
    });
  } catch (e) {
    console.log('  Customer expand failed');
  }

  await sleep(PAUSE.LONG);

  // ================================================================
  // SCENE 10: OUTRO CARD (5s)
  // ================================================================
  console.log('\n--- SCENE 10: Outro Card ---');
  const outroPath = path.resolve(__dirname, '../videos/camper-tour/DEMO-service-management/outro.html');
  await page.goto(`file://${outroPath}`);
  await sleep(PAUSE.OUTRO);

  // ================================================================
  // DONE
  // ================================================================
  console.log('\n' + '='.repeat(60));
  console.log('RECORDING COMPLETE -- Stop OBS now');
  console.log('='.repeat(60));
  console.log('');
  console.log('Post-production:');
  console.log('  1. Strip audio: ffmpeg -i raw.mp4 -an -c:v copy silent.mp4');
  console.log('  2. Trim: ffmpeg -i silent.mp4 -ss 0 -to END -c copy trimmed.mp4');
  console.log('  3. Record voiceover per scene (Telegram voice messages)');
  console.log('  4. Merge: ffmpeg -i trimmed.mp4 -i voiceover.m4a -c:v copy -c:a aac final.mp4');
  console.log('');

  await browser.close();
}

main().catch(err => {
  console.error('Demo recording failed:', err);
  process.exit(1);
});
