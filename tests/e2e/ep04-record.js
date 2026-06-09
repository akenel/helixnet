// Ep 4 — "It's Bigger Than a Garage" (Make an Event) -> MP4. Silent 1-pager, natural length, zoomed.
// A help-post can't hold a 1000-lb crane -> Mike makes an EVENT. Show date/venue/capacity/RSVP, from
// an attendee's POV (Nino). Login -> the event page -> the RSVP panel + the details.
const puppeteer = require('puppeteer');
const fs = require('fs');
const { execSync } = require('child_process');

const SQUARE = 'https://staging.lapiazza.app';
const EVENT = '/items/garage-moving-day-tool-sale-trapani';
const FRAMES = '/tmp/ep4rec';
const OUTDIR = '/home/angel/Videos/dream-weavers';
const OUT = `${OUTDIR}/ep04-playthrough.mp4`;
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  try { fs.rmSync(FRAMES, { recursive: true, force: true }); } catch (e) {}
  fs.mkdirSync(FRAMES, { recursive: true }); fs.mkdirSync(OUTDIR, { recursive: true });

  const browser = await puppeteer.launch({ headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors', '--hide-scrollbars', '--window-size=1280,720'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 2 });   // zoom in: readable

  const client = await page.target().createCDPSession();
  const frames = [];
  client.on('Page.screencastFrame', async ev => { frames.push({ t: ev.metadata.timestamp, data: ev.data }); try { await client.send('Page.screencastFrameAck', { sessionId: ev.sessionId }); } catch (e) {} });

  // login as Nino (an attendee who'd RSVP)
  await page.goto(SQUARE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.evaluate(() => fetch('/api/v1/demo/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'nino' }) }).then(r => r.text()));

  await page.goto(SQUARE + EVENT, { waitUntil: 'networkidle2', timeout: 30000 });
  await client.send('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
  await sleep(3200);                                            // the event: title + cover + the RSVP panel
  await page.evaluate(() => window.scrollTo({ top: 280, behavior: 'smooth' })); await sleep(3400);   // Start/End date+time, venue
  await page.evaluate(() => window.scrollTo({ top: 560, behavior: 'smooth' })); await sleep(3400);   // 0/12 attendees, Free, RSVP
  await page.evaluate(() => window.scrollTo({ top: 900, behavior: 'smooth' })); await sleep(3200);   // description / the story
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await sleep(2200);     // back to the top + RSVP

  await client.send('Page.stopScreencast'); await sleep(400);
  await browser.close();

  if (frames.length < 2) { console.log('NO FRAMES'); process.exit(1); }
  frames.forEach((f, k) => { f.fn = `${FRAMES}/f${String(k).padStart(6, '0')}.jpg`; fs.writeFileSync(f.fn, Buffer.from(f.data, 'base64')); });
  let concat = '';
  for (let k = 0; k < frames.length; k++) {
    const dur = k < frames.length - 1 ? Math.min(6.0, Math.max(0.033, frames[k + 1].t - frames[k].t)) : 0.5;
    concat += `file '${frames[k].fn}'\nduration ${dur.toFixed(3)}\n`;
  }
  concat += `file '${frames[frames.length - 1].fn}'\n`;
  fs.writeFileSync(`${FRAMES}/list.txt`, concat);
  console.log(`captured ${frames.length} frames over ${(frames[frames.length - 1].t - frames[0].t).toFixed(1)}s -> encoding…`);
  execSync(`ffmpeg -y -loglevel error -f concat -safe 0 -i ${FRAMES}/list.txt -vf "fps=24,format=yuv420p,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,tpad=stop_mode=clone:stop_duration=1.2" -c:v libx264 -preset medium -crf 20 -movflags +faststart "${OUT}"`, { stdio: 'inherit' });
  console.log('✅ wrote', OUT);
})();
