// Ep 1 — record the clean playthrough to MP4 (Phase 2). CDP screencast -> timestamped frames ->
// ffmpeg concat (faithful pacing). No OBS, no extra npm. Paced for video. Output: an MP4 the Wolf
// verifies + voices over. Usage: node tests/e2e/ep01-record.js
const puppeteer = require('puppeteer');
const fs = require('fs');
const { execSync } = require('child_process');

const SQUARE = 'https://staging.lapiazza.app';
const BOTTEGA = 'https://staging-bottega.lapiazza.app';
const STAMP = Date.now();
const EMAIL = `angel.kenel+rec${STAMP}@gmail.com`;
const NAME = 'Newcomer ' + String(STAMP).slice(-5);   // unique per run -> no slug collision
const PASS = 'helix_pass';
const ABOUT = "I fix old motorbikes and love to cook - and I just got a link to my neighbour Mike's garage move.";
const FRAMES = '/tmp/ep1rec';
const OUTDIR = '/home/angel/Videos/dream-weavers';
const OUT = `${OUTDIR}/ep01-playthrough.mp4`;
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  try { fs.rmSync(FRAMES, { recursive: true, force: true }); } catch (e) {}
  fs.mkdirSync(FRAMES, { recursive: true });
  fs.mkdirSync(OUTDIR, { recursive: true });

  const browser = await puppeteer.launch({ headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors', '--hide-scrollbars', '--window-size=1920,1080'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 768, deviceScaleFactor: 2 });   // zoom in: content fills the frame, larger/readable text
  page.on('requestfailed', r => { if (r.url().includes('get-started')) console.log('REQ-FAILED', r.url(), r.failure() && r.failure().errorText); });
  page.on('response', r => { if (r.url().includes('get-started') && r.request().method() === 'POST') console.log('POST get-started ->', r.status()); });
  // hold the 🎉 Welcome readable: delay the post-submit redirect navigation by ~5s (no page-JS patch)
  let holdWorkshop = false;
  await page.setRequestInterception(true);
  page.on('request', req => {
    if (holdWorkshop && req.isNavigationRequest() && req.url().includes('/compute/bottega')) {
      holdWorkshop = false; setTimeout(() => req.continue().catch(() => {}), 5000);
    } else req.continue().catch(() => {});
  });

  // --- CDP screencast: collect frames + their real timestamps ---
  const client = await page.target().createCDPSession();
  const frames = [];                       // buffer in memory (no sync I/O in the hot path)
  client.on('Page.screencastFrame', async ev => {
    frames.push({ t: ev.metadata.timestamp, data: ev.data });
    try { await client.send('Page.screencastFrameAck', { sessionId: ev.sessionId }); } catch (e) {}
  });
  const rec = () => client.send('Page.startScreencast', { format: 'jpeg', quality: 80, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
  const stop = () => client.send('Page.stopScreencast');

  // ---- THE PACED PLAYTHROUGH (the Ep 1 beats) ----
  await page.goto(SQUARE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
  await rec();
  await sleep(2500);                                   // dwell: the square
  await page.evaluate(() => window.scrollTo({ top: 700, behavior: 'smooth' })); await sleep(2500);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await sleep(1500);

  await page.goto(BOTTEGA + '/get-started', { waitUntil: 'networkidle2', timeout: 30000 }); await sleep(1800);
  await page.type('input[placeholder="Flora Ferrara"]', NAME, { delay: 70 }); await sleep(500);
  await page.type('input[placeholder="you@example.com"]', EMAIL, { delay: 45 }); await sleep(500);
  await page.type('input[placeholder="at least 6 characters"]', PASS, { delay: 70 }); await sleep(500);
  await page.type('textarea[placeholder*="cook with"]', ABOUT, { delay: 28 }); await sleep(1200);
  await page.waitForFunction(() => { const b = [...document.querySelectorAll('button')].find(x => /build my bottega/i.test(x.textContent)); return b && !b.disabled; }, { timeout: 8000 }).catch(() => {});
  holdWorkshop = true;   // arm the redirect delay so the 🎉 Welcome lingers
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => /build my bottega/i.test(x.textContent)); if (b) b.click(); });
  // dwell on the "building your Bottega" beat + the welcome
  try {
    await page.waitForFunction(() => location.pathname.includes('/compute/bottega') || /Welcome,/.test(document.body.innerText), { timeout: 45000 });
  } catch (e) {
    await page.screenshot({ path: '/tmp/ep1rec-fail.png' });
    const info = await page.evaluate(() => ({ url: location.href, body: document.body.innerText.replace(/\s+/g, ' ').slice(0, 300) }));
    console.log('SUBMIT-FAIL', JSON.stringify(info));
    await stop().catch(() => {}); await browser.close(); process.exit(1);
  }
  await sleep(3000);
  await page.waitForFunction(() => location.pathname.includes('/compute/bottega'), { timeout: 30000 }).catch(() => {});
  // dwell on the workshop + the menu loading
  await page.waitForFunction(() => { try { return /Find Your Edge/i.test(document.body.innerText) && !/loading menu/i.test(document.body.innerText); } catch (e) { return false; } }, { timeout: 25000, polling: 400 }).catch(() => {});
  await sleep(2800);
  for (const y of [250, 500, 750, 950, 600, 300]) {   // pan the recipe cards SLOWLY
    await page.evaluate(yy => window.scrollTo({ top: yy, behavior: 'smooth' }), y); await sleep(1500);
  }
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await sleep(1800);

  await stop();
  await sleep(400);
  await browser.close();

  // ---- assemble frames -> MP4 with faithful per-frame durations ----
  if (frames.length < 2) { console.log('NO FRAMES captured — screencast failed'); process.exit(1); }
  frames.forEach((f, k) => { f.fn = `${FRAMES}/f${String(k).padStart(6, '0')}.jpg`; fs.writeFileSync(f.fn, Buffer.from(f.data, 'base64')); });
  const t0 = frames[0].t;
  let concat = '';
  for (let k = 0; k < frames.length; k++) {
    const dur = k < frames.length - 1
      ? Math.min(6.0, Math.max(0.033, frames[k + 1].t - frames[k].t)) : 0.5;   // 6s cap: hold static dwells (Welcome!)
    concat += `file '${frames[k].fn}'\nduration ${dur.toFixed(3)}\n`;
  }
  concat += `file '${frames[frames.length - 1].fn}'\n`;   // last frame (concat quirk)
  fs.writeFileSync(`${FRAMES}/list.txt`, concat);
  console.log(`captured ${frames.length} frames over ${(frames[frames.length - 1].t - t0).toFixed(1)}s -> encoding…`);
  const RAW = `${FRAMES}/raw.mp4`;
  execSync(`ffmpeg -y -loglevel error -f concat -safe 0 -i ${FRAMES}/list.txt -vf "fps=24,format=yuv420p,scale=1920:1080" -c:v libx264 -preset medium -crf 20 "${RAW}"`, { stdio: 'inherit' });
  // normalize to EXACTLY 60.0s: clone the last frame to pad short, hard-cut at 60 if long
  execSync(`ffmpeg -y -loglevel error -i "${RAW}" -vf "tpad=stop_mode=clone:stop_duration=25,fps=24" -t 60 -c:v libx264 -preset medium -crf 20 -movflags +faststart "${OUT}"`, { stdio: 'inherit' });
  console.log('✅ wrote', OUT, '(exactly 60s)');
})();
