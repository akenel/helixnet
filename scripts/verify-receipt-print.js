// Verify a Banco POS receipt prints on ONE A4 page (CLAUDE.md: never claim a
// 1-pager without checking the PDF). Rings a real sale, renders the receipt
// headless, prints to PDF, and the caller counts pages with pdfinfo.
//
// Usage: node scripts/verify-receipt-print.js [itemCount] [outPdf]
//   API/KC default to local; override with POS_API / POS_KC env.
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
const puppeteer = require('puppeteer');

const API = process.env.POS_API || 'https://helix-platform.local';
const KC  = process.env.POS_KC  || 'https://keycloak.helix.local';
const REALM = 'kc-pos-realm-dev';
const ITEMS = parseInt(process.argv[2] || '20', 10);
const OUT = process.argv[3] || '/tmp/banco-receipt.pdf';

async function token() {
  const r = await fetch(`${KC}/realms/${REALM}/protocol/openid-connect/token`, {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ client_id: 'helix_pos_web', username: 'felix', password: 'helix_pass', grant_type: 'password' }),
  });
  return (await r.json()).access_token;
}

async function ringSale(tok) {
  const h = { 'Authorization': `Bearer ${tok}`, 'Content-Type': 'application/json' };
  const prods = await (await fetch(`${API}/api/v1/pos/products?limit=100`, { headers: h })).json();
  const inStock = prods.filter(p => p.stock_quantity > 0);
  const tx = await (await fetch(`${API}/api/v1/pos/transactions`, { method: 'POST', headers: h, body: '{}' })).json();
  for (let i = 0; i < ITEMS; i++) {
    const p = inStock[i % inStock.length];
    await fetch(`${API}/api/v1/pos/transactions/${tx.id}/items`, {
      method: 'POST', headers: h,
      body: JSON.stringify({ product_id: p.id, quantity: 1, discount_percent: '0' }),
    });
  }
  // NB: intentionally NOT checking out -- the receipt renders line items + totals
  // from the open transaction, so the print-layout/page-count check stays
  // non-destructive (no stock deduction on the shared dev DB).
  return tx.id;
}

(async () => {
  const tok = await token();
  const txId = await ringSale(tok);
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--ignore-certificate-errors'] });
  const page = await browser.newPage();
  // Seed the token so the receipt page authenticates, then load the receipt.
  await page.goto(`${API}/pos`, { waitUntil: 'domcontentloaded' });
  await page.evaluate(t => sessionStorage.setItem('pos_token', t), tok);
  await page.goto(`${API}/pos/receipt/${txId}`, { waitUntil: 'networkidle0' });
  await page.waitForFunction(() => document.querySelectorAll('table tbody tr').length > 0, { timeout: 15000 });
  await page.emulateMediaType('print');
  await page.pdf({ path: OUT, format: 'A4', printBackground: true });
  await browser.close();
  console.log(`RECEIPT_PDF=${OUT} ITEMS=${ITEMS} TX=${txId}`);
})().catch(e => { console.error(e); process.exit(1); });
