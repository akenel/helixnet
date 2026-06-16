// Screenshot the Provider Console with a real token, to eyeball the capability badges.
// Usage: TOKEN=xxx node shot.js
const puppeteer = require('/home/angel/repos/helixnet/node_modules/puppeteer');

(async () => {
  const token = process.env.TOKEN;
  if (!token) { console.error('set TOKEN'); process.exit(1); }
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 900, height: 1100 });
  await page.goto('http://localhost:9003/compute/dashboard#token=' + token,
                  { waitUntil: 'networkidle2', timeout: 30000 });
  // switch to Provider view via Alpine
  await page.evaluate(() => {
    const el = document.querySelector('[x-data]');
    if (el && el.__x) el.__x.$data.view = 'provider';
    else { window.Alpine && Alpine.$data && (Alpine.$data(el).view = 'provider'); }
  });
  await new Promise(r => setTimeout(r, 2500));
  await page.screenshot({ path: 'out/provider-console.png', fullPage: false });
  console.log('saved out/provider-console.png');
  await browser.close();
})();
