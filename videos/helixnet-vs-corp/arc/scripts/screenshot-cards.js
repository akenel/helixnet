const puppeteer = require('puppeteer');
const path = require('path');

const cards = [
  { file: 'intro-card.html', out: 'intro-card.png' },
  { file: 'comparison-slide.html', out: 'comparison-slide.png' },
  { file: 'outro-card.html', out: 'outro-card.png' },
];

(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  for (const card of cards) {
    const filePath = path.resolve(__dirname, card.file);
    await page.goto('file://' + filePath, { waitUntil: 'networkidle0' });
    await page.screenshot({
      path: path.resolve(__dirname, card.out),
      type: 'png',
      fullPage: false,
    });
    console.log('OK: ' + card.out);
  }

  await browser.close();
  console.log('Done -- all cards screenshotted at 1920x1080');
})();
