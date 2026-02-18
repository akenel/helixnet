const puppeteer = require('puppeteer');
const path = require('path');
const OUT = path.resolve(__dirname);

const cards = [
  'text-card-decision-latency.html',
  'text-card-ownership.html',
  'text-card-trap.html',
  'text-card-helixnet.html',
];

(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  for (const card of cards) {
    const png = card.replace('.html', '.png');
    await page.goto('file://' + path.join(OUT, card), { waitUntil: 'networkidle0' });
    await page.screenshot({ path: path.join(OUT, png), type: 'png' });
    console.log('OK: ' + png);
  }
  await browser.close();
})();
