// Verify the Close Shift Z-report prints on ONE A4 page.
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
const puppeteer = require('puppeteer');
const API = process.env.POS_API || 'https://helix-platform.local';
const KC  = process.env.POS_KC  || 'https://keycloak.helix.local';
const OUT = process.argv[2] || '/tmp/banco-zreport.pdf';

(async () => {
  const tok = (await (await fetch(`${KC}/realms/kc-pos-realm-dev/protocol/openid-connect/token`, {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: 'helix_pos_web', username: 'felix', password: 'helix_pass', grant_type: 'password' }),
  })).json()).access_token;
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--ignore-certificate-errors'] });
  const page = await browser.newPage();
  await page.goto(`${API}/pos`, { waitUntil: 'domcontentloaded' });
  await page.evaluate(t => sessionStorage.setItem('pos_token', t), tok);
  await page.goto(`${API}/pos/closeout`, { waitUntil: 'networkidle0' });
  await page.waitForFunction(() => {
    const el = document.querySelector('#daily-print-sheet');
    return el && /TOTAL/.test(el.textContent);
  }, { timeout: 15000 });
  await page.emulateMediaType('print');
  await page.pdf({ path: OUT, format: 'A4', printBackground: true });
  await browser.close();
  console.log(`ZREPORT_PDF=${OUT}`);
})().catch(e => { console.error(e); process.exit(1); });
