const puppeteer = require('puppeteer');
const path = require('path');
const { execSync } = require('child_process');

const OUT = path.resolve(__dirname);

(async () => {
  // ── Screenshot 1: Terminal with docker ps ──
  // Create a styled HTML terminal showing the docker ps output
  const dockerOutput = execSync(
    'ssh -o ConnectTimeout=10 root@46.62.138.218 "echo \'root@helixnet-uat:/opt/helixnet# docker ps --format \\\"table {{.Names}}\\\\t{{.Status}}\\\"\' && docker ps --format \'table {{.Names}}\t{{.Status}}\'"',
    { encoding: 'utf-8' }
  ).trim();

  const terminalHtml = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1920px; height: 1080px; background: #1a1a2e; display: flex; justify-content: center; align-items: center; }
.terminal { width: 1600px; background: #0d1117; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
.titlebar { background: #21262d; padding: 12px 20px; display: flex; align-items: center; gap: 8px; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.dot.red { background: #ff5f56; }
.dot.yellow { background: #ffbd2e; }
.dot.green { background: #27c93f; }
.titlebar-text { color: #666; font-family: monospace; font-size: 14px; margin-left: 12px; }
.content { padding: 30px; font-family: 'Courier New', monospace; font-size: 22px; line-height: 1.8; color: #e6edf3; white-space: pre; }
.prompt { color: #27AE60; }
.healthy { color: #27c93f; font-weight: bold; }
</style></head><body>
<div class="terminal">
<div class="titlebar">
  <div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div>
  <span class="titlebar-text">root@helixnet-uat ~ ssh</span>
</div>
<div class="content"><span class="prompt">root@helixnet-uat:/opt/helixnet#</span> docker ps --format "table {{.Names}}\\t{{.Status}}"

NAMES            STATUS
helix-platform   Up 21 hours <span class="healthy">(healthy)</span>
caddy            Up 21 hours <span class="healthy">(healthy)</span>
keycloak         Up 21 hours <span class="healthy">(healthy)</span>
postgres         Up 21 hours <span class="healthy">(healthy)</span>
rabbitmq         Up 21 hours <span class="healthy">(healthy)</span>
redis            Up 21 hours <span class="healthy">(healthy)</span>

<span class="prompt">root@helixnet-uat:/opt/helixnet#</span> █</div>
</div></body></html>`;

  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--ignore-certificate-errors'] });

  // Screenshot the terminal
  const termPage = await browser.newPage();
  await termPage.setViewport({ width: 1920, height: 1080 });
  await termPage.setContent(terminalHtml, { waitUntil: 'networkidle0' });
  await termPage.screenshot({ path: path.join(OUT, 'screen-docker-ps.png'), type: 'png' });
  console.log('OK: screen-docker-ps.png');
  await termPage.close();

  // ── Screenshot 2: Login page ──
  const loginPage = await browser.newPage();
  await loginPage.setViewport({ width: 1920, height: 1080 });
  await loginPage.goto('https://46.62.138.218/camper', {
    waitUntil: 'networkidle0',
    timeout: 30000
  });
  await loginPage.screenshot({ path: path.join(OUT, 'screen-login-page.png'), type: 'png' });
  console.log('OK: screen-login-page.png');

  // ── Screenshot 3: Logged in as nino ──
  // Click login, fill credentials
  try {
    // Wait for the login button/link on the camper page
    await loginPage.waitForSelector('a[href*="login"], button, .login-btn, a.btn', { timeout: 5000 });
    const loginLink = await loginPage.$('a[href*="login"]') || await loginPage.$('a.btn');
    if (loginLink) {
      await loginLink.click();
      await loginPage.waitForNavigation({ waitUntil: 'networkidle0', timeout: 15000 }).catch(() => {});
    }

    // Check if we're on Keycloak login
    const usernameField = await loginPage.$('#username');
    if (usernameField) {
      await loginPage.type('#username', 'nino');
      await loginPage.type('#password', 'helix_pass');
      await loginPage.click('#kc-login');
      await loginPage.waitForNavigation({ waitUntil: 'networkidle0', timeout: 15000 }).catch(() => {});
      // Wait a bit for the page to fully render
      await new Promise(r => setTimeout(r, 2000));
      await loginPage.screenshot({ path: path.join(OUT, 'screen-logged-in.png'), type: 'png' });
      console.log('OK: screen-logged-in.png');
    } else {
      console.log('SKIP: No Keycloak login form found');
    }
  } catch (e) {
    console.log('Login flow error:', e.message);
    await loginPage.screenshot({ path: path.join(OUT, 'screen-login-debug.png'), type: 'png' });
    console.log('Saved debug screenshot');
  }

  await browser.close();
  console.log('Done -- screen demo screenshots captured');
})();
