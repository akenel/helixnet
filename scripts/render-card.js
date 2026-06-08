// Screenshot a 1920x1080 HTML card -> PNG (intro/outro cards for the video pipeline).
// Usage: node render-card.js <card.html> <out.png>
const puppeteer = require('puppeteer');
(async () => {
  const [, , htmlPath, outPath] = process.argv;
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await page.goto('file://' + require('path').resolve(htmlPath), { waitUntil: 'networkidle0' });
  await page.screenshot({ path: outPath, type: 'png' });
  await browser.close();
  console.log('wrote', outPath);
})();
