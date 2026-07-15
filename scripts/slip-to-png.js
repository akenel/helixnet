// Render a delivery-slip HTML file to a crisp PNG (what a phone photo of a real slip approximates).
// Usage: node scripts/slip-to-png.js input.html output.png
const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const [, , inFile, outFile] = process.argv;
  if (!inFile || !outFile) { console.error('usage: node slip-to-png.js input.html output.png'); process.exit(2); }
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  // A4-ish portrait at 2x for legible small print (the SLIP intake keeps 1600px).
  await page.setViewport({ width: 900, height: 1273, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(inFile), { waitUntil: 'networkidle0' });
  const el = await page.$('.slip');
  await (el || page).screenshot({ path: outFile });
  await browser.close();
  console.log('wrote', outFile);
})();
