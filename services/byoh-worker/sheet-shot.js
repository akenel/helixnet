const puppeteer = require('/home/angel/repos/helixnet/node_modules/puppeteer');
(async () => {
  const b = await puppeteer.launch({ headless:'new', args:['--no-sandbox'] });
  const p = await b.newPage();
  await p.setViewport({ width: 820, height: 1200 });
  await p.goto('file:///home/angel/repos/helixnet/docs/testing/PROD-TEST-bottega.html', { waitUntil:'load' });
  await p.screenshot({ path:'out/test-sheet.png' });
  console.log('saved'); await b.close();
})();
