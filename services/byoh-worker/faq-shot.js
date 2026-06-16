const puppeteer = require('/home/angel/repos/helixnet/node_modules/puppeteer');
(async () => {
  const b = await puppeteer.launch({ headless:'new', args:['--no-sandbox'] });
  const p = await b.newPage();
  await p.setViewport({ width: 900, height: 1400 });
  await p.goto('http://localhost:9003/compute/faq', { waitUntil:'networkidle2', timeout:30000 });
  await p.screenshot({ path:'out/faq.png' });
  console.log('saved out/faq.png');
  await b.close();
})();
