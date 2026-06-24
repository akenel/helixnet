const puppeteer = require('/home/angel/repos/helixnet/node_modules/puppeteer');
(async () => {
  const token = process.env.TOKEN;
  const b = await puppeteer.launch({ headless:'new', args:['--no-sandbox'] });
  const p = await b.newPage();
  await p.setViewport({ width: 900, height: 1100 });
  await p.goto('http://localhost:9003/compute/bottega#token='+token, { waitUntil:'networkidle2', timeout:30000 });
  await new Promise(r=>setTimeout(r,2500));
  await p.screenshot({ path:'out/bottega-accordion.png' });
  console.log('saved');
  await b.close();
})();
