const puppeteer = require('/home/angel/repos/helixnet/node_modules/puppeteer');
(async () => {
  const t = process.env.TOKEN;
  const b = await puppeteer.launch({ headless:'new', args:['--no-sandbox'] });
  const p = await b.newPage(); await p.setViewport({ width: 900, height: 750 });
  await p.goto('http://localhost:9003/compute/bottega#token='+t, { waitUntil:'networkidle2', timeout:30000 });
  await new Promise(r=>setTimeout(r,2000));
  await p.evaluate(()=>{ const el=document.querySelector('[x-data]'); if(el && el._x_dataStack) el._x_dataStack[0].openCat='media'; });
  await new Promise(r=>setTimeout(r,800));
  await p.screenshot({ path:'out/voiceover-card.png' });
  console.log('saved'); await b.close();
})();
