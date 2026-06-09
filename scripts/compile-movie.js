// Compile the 12 stitched episodes into one full movie, crossfaded between episodes.
const { execSync } = require('child_process');
const fs = require('fs');
const FINAL = '/home/angel/Videos/dream-weavers/final';
const OUT = '/home/angel/Videos/dream-weavers/Dream-Weavers-S1-FULL.mp4';
const XF = 0.7;

const eps = [];
for (let n = 1; n <= 12; n++) { const f = `${FINAL}/ep${String(n).padStart(2, '0')}.mp4`; if (fs.existsSync(f)) eps.push(f); }
const durs = eps.map(f => parseFloat(execSync(`ffprobe -v error -show_entries format=duration -of csv=p=0 "${f}"`).toString().trim()));

const inputs = eps.map(f => `-i "${f}"`).join(' ');
let fc = eps.map((_, i) => `[${i}]fps=24,format=yuv420p,scale=1920:1080,setsar=1[v${i}]`).join(';') + ';';
const chapters = [{ n: 1, t: 0 }];
let R = durs[0], prev = 'v0';
for (let i = 1; i < eps.length; i++) {
  const off = (R - XF);
  chapters.push({ n: i + 1, t: off });               // chapter ~ where ep i+1 fades in
  const lbl = (i === eps.length - 1) ? 'out' : `x${i}`;
  fc += `[${prev}][v${i}]xfade=transition=fade:duration=${XF}:offset=${off.toFixed(3)}[${lbl}];`;
  R = R + durs[i] - XF;
  prev = lbl;
}
fc = fc.replace(/;$/, '');

console.log(`compiling ${eps.length} episodes -> ${(R).toFixed(1)}s movie…`);
execSync(`ffmpeg -y -loglevel error ${inputs} -filter_complex "${fc}" -map "[out]" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -movflags +faststart "${OUT}"`, { stdio: 'inherit' });
const fdur = parseFloat(execSync(`ffprobe -v error -show_entries format=duration -of csv=p=0 "${OUT}"`).toString().trim());
console.log(`✅ ${OUT}  (${fdur.toFixed(1)}s)`);
console.log('\nCHAPTERS (paste into the description):');
const titles = ['Welcome to the Piazza', 'Ask the Neighbourhood', 'The Crew Rallies', 'Make an Event', 'RSVP and Open It Up', 'The Side Conversation', 'Grow the Crowd', 'The Trade', 'Spot the Scammer', "Who's Coming", 'Saturday, The Lift', 'Build Your Own Piazza'];
chapters.forEach(c => { const m = Math.floor(c.t / 60), s = Math.round(c.t % 60); console.log(`${m}:${String(s).padStart(2, '0')} Ep ${c.n} — ${titles[c.n - 1]}`); });
