// console-sweep — load every key page in a real browser, capture console errors,
// uncaught exceptions, and failed/5xx requests. Anon pass + (on staging) a logged-in persona pass.
// Usage: node tests/e2e/console-sweep.js [staging|prod|local]   (default: staging)
// Exits non-zero if any page throws a console error / pageerror / 5xx — a pre-UAT gate.
const puppeteer = require('puppeteer');

const TARGET = process.argv[2] || 'staging';
const ENVS = {
  staging: { square: 'https://staging.lapiazza.app', bottega: 'https://staging-bottega.lapiazza.app', demo: true },
  prod:    { square: 'https://lapiazza.app',         bottega: 'https://bottega.lapiazza.app',         demo: false },
  local:   { square: 'https://helix.local',          bottega: 'https://helix.local',                  demo: true },
};
const E = ENVS[TARGET];
if (!E) { console.error('unknown target', TARGET); process.exit(2); }

// pages to sweep (anon-safe). {b:true} = on the Bottega host.
const PAGES = [
  { p: '/' }, { p: '/browse' }, { p: '/helpboard' }, { p: '/calendar' }, { p: '/raffles' },
  { p: '/compute/bottega', b: true }, { p: '/get-started', b: true },
  { p: '/compute/legends', b: true }, { p: '/compute/me', b: true }, { p: '/compute/concierge', b: true },
];
// ignore known-noisy third-party / non-actionable console lines
// ignore: third-party noise + EXTERNAL image CDNs (flaky, not our code — broken item images are a
// separate data/UX follow-up, not an app-error gate failure).
const IGNORE = /favicon|net::ERR_|Failed to load resource: the server responded with a status of 4|web-share|ResizeObserver|Download the React|googletagmanager|stripe\.com|gstatic|unsplash\.com|picsum|cloudinary|images\.weserv|pollinations/i;

let totalIssues = 0;
const report = [];

async function sweep(browser, label, beforeGoto) {
  for (const pg of PAGES) {
    const base = pg.b ? E.bottega : E.square;
    const url = base + pg.p;
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 900 });
    const issues = [];
    page.on('console', m => { if (m.type() === 'error' && !IGNORE.test(m.text())) issues.push('console: ' + m.text().slice(0, 140)); });
    page.on('pageerror', e => issues.push('JS-THROW: ' + String(e).slice(0, 140)));
    page.on('requestfailed', r => { const u = r.url(); if (!IGNORE.test(u)) issues.push('req-failed: ' + u.slice(0, 100)); });
    page.on('response', r => { if (r.status() >= 500) issues.push(`HTTP ${r.status()}: ${r.url().slice(0, 90)}`); });
    try {
      if (beforeGoto) await beforeGoto(page);
      const resp = await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
      await new Promise(r => setTimeout(r, 1200));   // let JS settle
      const status = resp ? resp.status() : 0;
      if (status >= 400) issues.push(`page status ${status}`);
    } catch (e) { issues.push('goto-failed: ' + String(e.message).slice(0, 100)); }
    await page.close();
    const tag = issues.length ? `❌ ${issues.length}` : '✅ clean';
    console.log(`  [${label}] ${tag}  ${pg.p}`);
    issues.forEach(i => console.log(`        • ${i}`));
    totalIssues += issues.length;
    if (issues.length) report.push({ label, page: pg.p, issues });
  }
}

(async () => {
  console.log(`\n════ CONSOLE SWEEP — ${TARGET} (${E.square}) ════\n`);
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors'] });
  console.log('— ANONYMOUS —');
  await sweep(browser, 'anon', async (page) => { await page.evaluateOnNewDocument(() => { try { localStorage.setItem('cookie_consent', 'accepted'); localStorage.setItem('pwa_install_dismissed', '1'); } catch (e) {} }); });
  if (E.demo) {
    console.log('— LOGGED IN (mike) —');
    await sweep(browser, 'mike', async (page) => {
      await page.evaluateOnNewDocument(() => { try { localStorage.setItem('cookie_consent', 'accepted'); localStorage.setItem('pwa_install_dismissed', '1'); } catch (e) {} });
      await page.goto(E.square + '/', { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
      await page.evaluate(() => fetch('/api/v1/demo/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'mike' }) }).then(r => r.text())).catch(() => {});
    });
  }
  await browser.close();
  console.log(`\n════ ${totalIssues} issue(s) across all pages ════`);
  if (totalIssues) { console.log('🔴 console sweep found problems'); process.exit(1); }
  console.log('🟢 all pages clean (no console errors / JS throws / 5xx)');
})();
