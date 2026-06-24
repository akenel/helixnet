const puppeteer = require('/home/angel/repos/helixnet/node_modules/puppeteer');
(async () => {
  const t = process.env.TOKEN;
  const b = await puppeteer.launch({ headless:'new', args:['--no-sandbox'] });
  const p = await b.newPage();
  await p.setViewport({ width: 900, height: 950 });
  await p.goto('http://localhost:9003/compute/legends#token='+t, { waitUntil:'networkidle2', timeout:30000 });
  await new Promise(r=>setTimeout(r,1500));
  await p.type('input[type=search]', 'Mar');
  await new Promise(r=>setTimeout(r,1500));
  await p.screenshot({ path:'out/legends-search.png' });
  console.log('saved');
  await b.close();
})();
