#!/usr/bin/env node
/**
 * ISOTTO Sport -- Print Shop Management Demo Recording Script
 *
 * HOW TO USE:
 * 1. Make sure Docker stack is running (docker compose up -d)
 * 2. Open OBS, set source to "Screen Capture (PipeWire)"
 * 3. Run: node scripts/isotto-demo-record.js
 *    - Script mutes your microphones automatically
 *    - Chrome opens FULLSCREEN (covers terminal + taskbar)
 * 4. A bright RED "OBS CHECK" card fills the screen
 * 5. Check OBS PREVIEW -- do you see the red card FULLSCREEN?
 *    - YES: Hit Record in OBS, then press ENTER in terminal
 *    - NO:  Click Chrome + press F11 to force fullscreen, or fix OBS source
 * 6. Demo runs automatically (~4:30). Don't touch anything.
 * 7. Stop OBS when console says "RECORDING COMPLETE"
 * 8. Mics are automatically unmuted when script exits
 *
 * LESSONS LEARNED (Feb 13, 2026):
 * - Take 1: OBS captured GNOME Settings, not the browser
 * - Take 2: Terminal covered half the screen (not fullscreen)
 * - Take 2: Mic was on, captured ambient audio
 * - Fix: --start-fullscreen + pactl mute + pre-flight check
 *
 * Total runtime: ~4:30
 *
 * SCENES:
 *   1. Intro card (5s)
 *   2. Login as Famous (15s)
 *   3. Dashboard overview (25s)
 *   4. Order board -- all orders with filters (20s)
 *   5. Order detail -- Pizza Planet 4-UP postcards (30s -- MONEY SHOT)
 *   6. Create new order (30s)
 *   7. Status workflow -- advance PuntaTipa order (20s)
 *   8. Customer lookup -- search Angelo (20s)
 *   9. RBAC demo -- login as Giulia, limited access (25s)
 *  10. Outro card (5s)
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
const PRINT_URL = `${BASE_URL}/print-shop`;
const API_URL = `${BASE_URL}/api/v1/print-shop`;

// Demo users
const FAMOUS = { user: 'famousguy', pass: 'helix_pass' };
const GIULIA = { user: 'giulia_f', pass: 'helix_pass' };

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
  // Click the login button on the ISOTTO login page
  try {
    await page.evaluate(() => {
      const links = document.querySelectorAll('a, button');
      for (const el of links) {
        if (el.textContent.toLowerCase().includes('accedi') ||
            el.textContent.toLowerCase().includes('login')) {
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

async function main() {
  console.log('='.repeat(60));
  console.log('ISOTTO SPORT -- Print Shop Management Demo');
  console.log('='.repeat(60));
  console.log('');
  console.log('CHECKLIST:');
  console.log('  [ ] Docker stack running');
  console.log('  [ ] OBS open with Screen Capture (PipeWire) source');
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
        <div style="font-size:56px;margin:40px 0;background:#FBBF24;color:#000;padding:24px 80px;border-radius:16px;font-weight:bold;">
          DO YOU SEE THIS FULLSCREEN IN OBS?
        </div>
        <div style="font-size:36px;margin-top:30px;">YES &rarr; Hit Record in OBS, then press ENTER in terminal</div>
        <div style="font-size:36px;margin-top:10px;">NO &rarr; STOP. Fix OBS source first.</div>
        <div style="font-size:24px;margin-top:50px;opacity:0.7;">Chrome should be FULLSCREEN (no taskbar, no terminal visible)</div>
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

  console.log('  OBS confirmed. Starting demo in 2 seconds...');
  await sleep(2000);

  // ================================================================
  // SCENE 1: INTRO CARD (5s)
  // ================================================================
  console.log('\n--- SCENE 1: Intro Card ---');
  const introPath = path.resolve(__dirname, '../videos/isotto-print-shop/DEMO/intro.html');
  await page.goto(`file://${introPath}`);
  await sleep(PAUSE.INTRO);

  // ================================================================
  // SCENE 2: LOGIN AS FAMOUS (15s)
  // ================================================================
  console.log('\n--- SCENE 2: Login as Famous ---');
  await page.goto(`${PRINT_URL}`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);
  await keycloakLogin(page, FAMOUS);
  await sleep(PAUSE.SHORT);
  console.log('  Current URL:', page.url());

  // ================================================================
  // SCENE 3: DASHBOARD (25s)
  // ================================================================
  console.log('\n--- SCENE 3: Dashboard Overview ---');
  // Dashboard should have loaded with stats and active orders
  await sleep(PAUSE.MEDIUM); // Let Alpine.js load data

  // Slowly scroll down to show active orders table
  await page.evaluate(() => window.scrollTo({ top: 300, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Scroll to quick actions
  await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Scroll back to top
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 4: ORDER BOARD (20s)
  // ================================================================
  console.log('\n--- SCENE 4: Order Board ---');
  await page.goto(`${PRINT_URL}/orders`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.MEDIUM);

  // Let the order list load and display
  await sleep(PAUSE.LONG);

  // Scroll to see all orders
  await page.evaluate(() => window.scrollTo({ top: 300, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // Scroll back
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 5: ORDER DETAIL -- Pizza Planet 4-UP (30s -- MONEY SHOT)
  // ================================================================
  console.log('\n--- SCENE 5: Order Detail -- Pizza Planet 4-UP ---');

  // Click the Pizza Planet order row
  try {
    const clicked = await page.evaluate(() => {
      const rows = document.querySelectorAll('tr.border-b.hover\\:bg-blue-50, tr[class*="cursor"]');
      for (const row of rows) {
        const text = row.textContent || '';
        if (text.includes('Pizza Planet') || text.includes('ORD-20260203')) {
          row.click();
          return true;
        }
      }
      return false;
    });

    if (!clicked) {
      // Navigate via API -- find the Pizza Planet order ID
      console.log('  Navigating to Pizza Planet order via API...');
      const orderId = await page.evaluate(async () => {
        const token = sessionStorage.getItem('isotto_token');
        if (!token) return null;
        const resp = await fetch('/api/v1/print-shop/orders?limit=200', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resp.ok) {
          const orders = await resp.json();
          for (const o of orders) {
            if (o.title && o.title.includes('Pizza Planet')) return o.id;
          }
          if (orders.length > 0) return orders[0].id;
        }
        return null;
      });

      if (orderId) {
        await page.goto(`${PRINT_URL}/orders/${orderId}`, { waitUntil: 'networkidle2', timeout: 15000 });
      }
    }
  } catch (e) {
    console.log('  Pizza Planet click failed:', e.message);
  }

  await sleep(PAUSE.MEDIUM);

  // Slowly scroll through the order detail sections -- MONEY SHOT
  // Quote section
  await page.evaluate(() => window.scrollTo({ top: 300, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Print specifications (the unique part)
  await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'smooth' }));
  await sleep(PAUSE.XLONG);

  // Production notes / timeline
  await page.evaluate(() => window.scrollTo({ top: 900, behavior: 'smooth' }));
  await sleep(PAUSE.LONG);

  // Back to top
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(PAUSE.SHORT);

  // ================================================================
  // SCENE 6: CREATE NEW ORDER (30s)
  // ================================================================
  console.log('\n--- SCENE 6: Create New Order ---');
  await page.goto(`${PRINT_URL}/orders/new`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.MEDIUM);

  // Fill in new order form
  try {
    // Select customer (first dropdown or search)
    const customerSelect = await page.$('select[x-model*="customer"]');
    if (customerSelect) {
      // Select Angelo/UFA from dropdown
      await page.evaluate(() => {
        const sel = document.querySelector('select[x-model*="customer"]');
        if (sel) {
          // Find the option for Angelo/UFA
          for (const opt of sel.options) {
            if (opt.text.includes('Angelo') || opt.text.includes('UFA')) {
              sel.value = opt.value;
              sel.dispatchEvent(new Event('change'));
              return;
            }
          }
          // Fallback: select first non-empty option
          if (sel.options.length > 1) {
            sel.value = sel.options[1].value;
            sel.dispatchEvent(new Event('change'));
          }
        }
      });
      await sleep(500);
    }

    // Title
    const titleInput = await page.$('input[x-model*="title"]');
    if (titleInput) {
      await humanType(page, 'input[x-model*="title"]', 'Piccolo Bistratto Table Cards');
      await sleep(300);
    }

    // Product type dropdown
    await page.evaluate(() => {
      const sel = document.querySelector('select[x-model*="product_type"]');
      if (sel) {
        sel.value = 'postcard';
        sel.dispatchEvent(new Event('change'));
      }
    });
    await sleep(300);

    // Quantity
    const qtyInput = await page.$('input[x-model*="quantity"]');
    if (qtyInput) {
      await clearAndType(page, 'input[x-model*="quantity"]', '100');
      await sleep(200);
    }

    // Unit price
    const priceInput = await page.$('input[x-model*="unit_price"]');
    if (priceInput) {
      await clearAndType(page, 'input[x-model*="unit_price"]', '0.25');
      await sleep(200);
    }

    await sleep(PAUSE.SHORT);

    // Scroll down to show print spec fields
    await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
    await sleep(PAUSE.MEDIUM);

    // Paper weight
    const gsmInput = await page.$('input[x-model*="paper_weight"]');
    if (gsmInput) {
      await clearAndType(page, 'input[x-model*="paper_weight"]', '250');
      await sleep(200);
    }

    // Color mode
    await page.evaluate(() => {
      const sel = document.querySelector('select[x-model*="color_mode"]');
      if (sel) {
        sel.value = 'cmyk';
        sel.dispatchEvent(new Event('change'));
      }
    });
    await sleep(200);

    // Size description
    const sizeInput = await page.$('input[x-model*="size_description"]');
    if (sizeInput) {
      await humanType(page, 'input[x-model*="size_description"]', 'A4 portrait (4-UP, 99x142.5mm)');
      await sleep(200);
    }

    await sleep(PAUSE.MEDIUM);

    // Scroll to show more fields
    await page.evaluate(() => window.scrollTo({ top: 700, behavior: 'smooth' }));
    await sleep(PAUSE.MEDIUM);

  } catch (e) {
    console.log('  New order form fill failed:', e.message);
  }

  // Don't submit -- just show the form filled in
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 7: STATUS WORKFLOW -- Advance PuntaTipa Order (20s)
  // ================================================================
  console.log('\n--- SCENE 7: Status Workflow ---');

  // Go to orders, find the PuntaTipa QUOTED order
  await page.goto(`${PRINT_URL}/orders`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);

  // Click PuntaTipa order
  try {
    const clicked = await page.evaluate(() => {
      const rows = document.querySelectorAll('tr.border-b.hover\\:bg-blue-50, tr[class*="cursor"]');
      for (const row of rows) {
        const text = row.textContent || '';
        if (text.includes('PuntaTipa') || text.includes('ORD-20260213-0001')) {
          row.click();
          return true;
        }
      }
      return false;
    });

    if (!clicked) {
      // Find via API
      const orderId = await page.evaluate(async () => {
        const token = sessionStorage.getItem('isotto_token');
        if (!token) return null;
        const resp = await fetch('/api/v1/print-shop/orders?limit=200', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resp.ok) {
          const orders = await resp.json();
          for (const o of orders) {
            if (o.title && o.title.includes('PuntaTipa')) return o.id;
            if (o.status === 'quoted') return o.id;
          }
        }
        return null;
      });

      if (orderId) {
        await page.goto(`${PRINT_URL}/orders/${orderId}`, { waitUntil: 'networkidle2', timeout: 15000 });
      }
    }
  } catch (e) {
    console.log('  PuntaTipa click failed:', e.message);
  }

  await sleep(PAUSE.MEDIUM);

  // Click the Approve button
  try {
    const approved = await clickButtonByText(page, 'approva', 'approve');
    if (approved) {
      console.log('  Approve button clicked');
    } else {
      console.log('  Approve button not found');
    }
  } catch (e) {
    console.log('  Approve button click failed');
  }

  await sleep(PAUSE.LONG);

  // ================================================================
  // SCENE 8: CUSTOMER LOOKUP (20s)
  // ================================================================
  console.log('\n--- SCENE 8: Customer Lookup ---');
  await page.goto(`${PRINT_URL}/customers`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);

  // Search for Angelo
  try {
    await humanType(page, 'input[type="text"]', 'Angelo');
    await sleep(PAUSE.MEDIUM);
  } catch (e) {
    console.log('  Customer search input not found');
  }

  // Expand Angelo's profile to show order history
  try {
    await page.evaluate(() => {
      const cards = document.querySelectorAll('.cursor-pointer, [\\@click*="toggle"]');
      for (const card of cards) {
        const text = card.textContent || '';
        if (text.includes('Angelo') || text.includes('UFA')) {
          card.click();
          return;
        }
      }
      // Fallback: click first card
      if (cards.length > 0) cards[0].click();
    });
  } catch (e) {
    console.log('  Customer expand failed');
  }

  await sleep(PAUSE.LONG);

  // Scroll to see order history
  await page.evaluate(() => window.scrollTo({ top: 300, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 9: RBAC DEMO -- Login as Giulia (25s)
  // ================================================================
  console.log('\n--- SCENE 9: RBAC Demo -- Giulia (Counter) ---');

  // Clear ALL cookies (kills KC SSO session) + app token
  const cdpClient = await page.target().createCDPSession();
  await cdpClient.send('Network.clearBrowserCookies');
  await page.evaluate(() => sessionStorage.removeItem('isotto_token'));
  console.log('  All cookies + token cleared');

  // Go to login page
  await page.goto(`${PRINT_URL}`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.SHORT);

  // Login as Giulia
  await keycloakLogin(page, GIULIA);
  await sleep(PAUSE.SHORT);
  console.log('  Current URL:', page.url());

  // Show dashboard -- Giulia's limited view
  await sleep(PAUSE.MEDIUM);

  // Navigate to orders
  await page.goto(`${PRINT_URL}/orders`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(PAUSE.MEDIUM);

  // Click into an order to show limited actions
  try {
    const clicked = await page.evaluate(() => {
      const rows = document.querySelectorAll('tr.border-b.hover\\:bg-blue-50, tr[class*="cursor"]');
      if (rows.length > 0) {
        rows[0].click();
        return true;
      }
      return false;
    });
  } catch (e) {
    console.log('  Order click for RBAC demo failed');
  }

  await sleep(PAUSE.LONG);

  // Scroll to show that action buttons are missing/different for Giulia
  await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'smooth' }));
  await sleep(PAUSE.MEDIUM);

  // ================================================================
  // SCENE 10: OUTRO CARD (5s)
  // ================================================================
  console.log('\n--- SCENE 10: Outro Card ---');
  const outroPath = path.resolve(__dirname, '../videos/isotto-print-shop/DEMO/outro.html');
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

  // Restore mic state
  await unmuteMicrophones();

  console.log('Post-production:');
  console.log('  cd videos/isotto-print-shop/DEMO/');
  console.log('  # Set RAW_FILE and TRIM_END in post-production.sh, then:');
  console.log('  bash post-production.sh');
  console.log('');
}

main().catch(async err => {
  console.error('Demo recording failed:', err);
  await unmuteMicrophones();
  process.exit(1);
});
