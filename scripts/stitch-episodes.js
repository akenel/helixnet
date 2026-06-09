// Stitch each Dream Weavers episode: intro card + body + outro card, with smooth crossfades (xfade).
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const CARDS = path.resolve(__dirname, '../stories/dream-weavers/cards');
const VID = '/home/angel/Videos/dream-weavers';
const FINAL = VID + '/final';
fs.mkdirSync(FINAL, { recursive: true });

const INTRO = 2.8, OUTRO = 3.2, XF = 0.7;   // card holds + crossfade duration (seconds)

for (let n = 1; n <= 12; n++) {
  const nn = String(n).padStart(2, '0');
  const body = `${VID}/ep${nn}-playthrough.mp4`;
  const intro = `${CARDS}/ep${nn}-intro.png`, outro = `${CARDS}/ep${nn}-outro.png`;
  if (!fs.existsSync(body)) { console.log(`ep${nn}: no body, skip`); continue; }
  const dur = parseFloat(execSync(`ffprobe -v error -show_entries format=duration -of csv=p=0 "${body}"`).toString().trim());
  const off1 = (INTRO - XF).toFixed(2);
  const off2 = (INTRO + dur - 2 * XF).toFixed(2);
  const out = `${FINAL}/ep${nn}.mp4`;
  const fc = [
    `[0]fps=24,format=yuv420p,scale=1920:1080,setsar=1[i]`,
    `[1]fps=24,format=yuv420p,scale=1920:1080,setsar=1[b]`,
    `[2]fps=24,format=yuv420p,scale=1920:1080,setsar=1[o]`,
    `[i][b]xfade=transition=fade:duration=${XF}:offset=${off1}[ib]`,
    `[ib][o]xfade=transition=fade:duration=${XF}:offset=${off2}[v]`,
  ].join(';');
  execSync(`ffmpeg -y -loglevel error -loop 1 -t ${INTRO} -i "${intro}" -i "${body}" -loop 1 -t ${OUTRO} -i "${outro}" -filter_complex "${fc}" -map "[v]" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -movflags +faststart "${out}"`, { stdio: 'inherit' });
  const fdur = parseFloat(execSync(`ffprobe -v error -show_entries format=duration -of csv=p=0 "${out}"`).toString().trim());
  console.log(`  ep${nn}: body ${dur.toFixed(1)}s -> final ${fdur.toFixed(1)}s  (card+body+card, crossfaded)`);
}
console.log('✅ stitched ->', FINAL);
