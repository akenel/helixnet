// Render all Dream Weavers intro/outro cards (1920x1080 PNGs) from the parametrized template.
const puppeteer = require('puppeteer');
const path = require('path');
const TEMPLATE = 'file://' + path.resolve(__dirname, '../stories/dream-weavers/cards/card-template.html');
const OUT = path.resolve(__dirname, '../stories/dream-weavers/cards');

const EP = [
  { n: 1, title: 'Welcome to the Piazza', tag: 'A town square with no fees, no middlemen — just your neighbours.' },
  { n: 2, title: 'Ask the Neighbourhood', tag: 'Stuck on something big? Post it. The neighbourhood answers.' },
  { n: 3, title: 'The Crew Rallies', tag: 'Five neighbours say yes — and Sally starts baking.' },
  { n: 4, title: "It's Bigger Than a Garage", tag: 'A 1,000-lb crane needs twenty hands — so Mike makes an event.' },
  { n: 5, title: 'RSVP and Open It Up', tag: 'The count climbs. Members RSVP. Everyone is welcome.' },
  { n: 6, title: 'The Side Conversation', tag: 'The cookies, arranged quietly in the messages.' },
  { n: 7, title: 'Grow the Crowd', tag: 'Share the link, scan the code — the crowd grows.' },
  { n: 8, title: 'The Trade', tag: "Bowls for muscle. You don't always pay in euros." },
  { n: 9, title: 'Spot the Scammer', tag: 'The off-platform funnel, caught — the warmth is protected.' },
  { n: 10, title: "Who's Coming?", tag: 'See who looked. Say hi. Turn lookers into the last hands.' },
  { n: 11, title: 'Saturday: The Lift', tag: 'Twenty hands. The crane rises. The cookies arrive.', climax: true },
  { n: 12, title: 'Build Your Own Piazza', tag: 'You saw it work. Now build your own.', finale: true },
];

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await b.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  const render = async (params, out) => {
    const qs = new URLSearchParams(params).toString();
    await page.goto(`${TEMPLATE}?${qs}`, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 450));   // fonts + the inject script
    await page.screenshot({ path: out });
    console.log('  ', path.basename(out));
  };
  for (const e of EP) {
    const nn = String(e.n).padStart(2, '0');
    const next = EP.find(x => x.n === e.n + 1);
    await render({ kind: 'intro', n: e.n, title: e.title, tag: e.tag, climax: e.climax ? '1' : '' }, `${OUT}/ep${nn}-intro.png`);
    await render({ kind: 'outro', n: e.n, next: next ? next.title : '', finale: e.finale ? '1' : '' }, `${OUT}/ep${nn}-outro.png`);
  }
  await b.close();
  console.log('all cards rendered ->', OUT);
})();
