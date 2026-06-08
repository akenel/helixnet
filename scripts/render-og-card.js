// Render an OG card HTML -> 1200x630 PNG (Puppeteer/Chrome — the project's only render tool).
// Inlines the wolf as base64 so it always loads. Usage:
//   node render-og-card.js <html> <wolf.png> <out.png> <serial>
const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const [, , htmlPath, wolfPath, outPath, serial] = process.argv;
  let html = fs.readFileSync(htmlPath, 'utf8');
  const wolf = fs.readFileSync(wolfPath).toString('base64');
  html = html.replace('{{WOLF}}', 'data:image/png;base64,' + wolf)
             .replace('{{SERIAL}}', serial || 'LP-OG-V3');
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });
  await page.setContent(html, { waitUntil: 'networkidle0' });
  await page.screenshot({ path: outPath, type: 'png' });
  await browser.close();
  console.log('wrote', outPath);
})();
