const puppeteer = require('/home/angel/repos/helixnet/node_modules/puppeteer');
(async () => {
  const t = process.env.TOKEN;
  const b = await puppeteer.launch({ headless:'new', args:['--no-sandbox'] });
  const p = await b.newPage(); await p.setViewport({ width: 900, height: 800 });
  await p.goto('http://localhost:9003/compute/bottega#token='+t, { waitUntil:'networkidle2', timeout:30000 });
  await new Promise(r=>setTimeout(r,2000));
  // open the voiceover-reel recipe
  await p.evaluate(()=>{ const el=document.querySelector('[x-data]'); const d=el._x_dataStack[0]; const r=d.recipes.find(x=>x.slug==='voiceover-reel'); if(r) d.pick(r); });
  await new Promise(r=>setTimeout(r,800));
  await p.screenshot({ path:'out/form.png' });
  console.log('saved'); await b.close();
})();
