#!/bin/bash
# ISOTTO Sport Demo -- Titled Scene Stitch Script
# Creates final video with scene title cards inserted between scenes
# Run from: videos/isotto-print-shop/DEMO/
set -e

SRC="ISOTTO-Sport-Demo.mp4"
ARC="arc"
CARD_DURATION=7   # seconds per title card

echo "=== ISOTTO Sport Demo -- Scene Title Card Stitch ==="
echo ""

# --- Step 1: Create title card video clips from PNGs ---
echo "[1/4] Creating title card video clips (${CARD_DURATION}s each)..."
for i in 1 2 3 4 5 6 7; do
  ffmpeg -y -loop 1 -i "${ARC}/scene-card-${i}.png" \
    -c:v libx264 -t ${CARD_DURATION} -pix_fmt yuv420p -r 30 -an \
    "${ARC}/card-${i}.mp4" 2>/dev/null
  echo "  card-${i}.mp4"
done

# --- Step 2: Extract scene clips from source video ---
echo ""
echo "[2/4] Extracting scene clips from ${SRC}..."

# Scene boundaries (start, end) in the source video
# Title cards hide the messy navigation frames between scenes
declare -A SCENES
SCENES[1]="4:25"      # Login + Dashboard (21s)
SCENES[2]="27:43"     # Orders list (16s)
SCENES[3]="44:70"     # Pizza Planet Order Detail (26s)
SCENES[4]="72:100"    # New Order form (28s)
SCENES[5]="104:113"   # PuntaTipa Status Workflow (9s)
SCENES[6]="115:130"   # Customer Management (15s)
SCENES[7]="132:162"   # RBAC - Giulia login (30s)

for i in 1 2 3 4 5 6 7; do
  IFS=':' read -r start end <<< "${SCENES[$i]}"
  # Re-encode to match intro/outro format (prevents concat issues)
  ffmpeg -y -ss "${start}" -to "${end}" -i "${SRC}" \
    -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -r 30 -an \
    "${ARC}/scene-${i}.mp4" 2>/dev/null
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${ARC}/scene-${i}.mp4" 2>/dev/null | cut -d. -f1)
  echo "  scene-${i}.mp4 (${dur}s)"
done

# --- Step 3: Get existing intro/outro clips ---
echo ""
echo "[3/4] Checking intro/outro clips..."

# Use the intro/outro clips already in arc/ from the original stitch
if [ ! -f "${ARC}/intro-clip.mp4" ]; then
  echo "  Creating intro clip from intro.png..."
  ffmpeg -y -loop 1 -i intro.png -c:v libx264 -t 4 -pix_fmt yuv420p -r 30 -an \
    "${ARC}/intro-clip.mp4" 2>/dev/null
fi
if [ ! -f "${ARC}/outro-clip.mp4" ]; then
  echo "  Creating outro clip from outro.png..."
  ffmpeg -y -loop 1 -i outro.png -c:v libx264 -t 5 -pix_fmt yuv420p -r 30 -an \
    "${ARC}/outro-clip.mp4" 2>/dev/null
fi
echo "  intro-clip.mp4 and outro-clip.mp4 ready"

# --- Step 4: Build concat list and stitch ---
echo ""
echo "[4/4] Stitching final titled video..."

cat > "${ARC}/concat-titled.txt" <<EOF
file 'intro-clip.mp4'
file 'card-1.mp4'
file 'scene-1.mp4'
file 'card-2.mp4'
file 'scene-2.mp4'
file 'card-3.mp4'
file 'scene-3.mp4'
file 'card-4.mp4'
file 'scene-4.mp4'
file 'card-5.mp4'
file 'scene-5.mp4'
file 'card-6.mp4'
file 'scene-6.mp4'
file 'card-7.mp4'
file 'scene-7.mp4'
file 'outro-clip.mp4'
EOF

cd "${ARC}"
ffmpeg -y -f concat -safe 0 -i concat-titled.txt -c copy ../ISOTTO-Sport-Demo-TITLED.mp4 2>/dev/null
cd ..

# --- Result ---
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 ISOTTO-Sport-Demo-TITLED.mp4 2>/dev/null | cut -d. -f1)
SIZE=$(du -h ISOTTO-Sport-Demo-TITLED.mp4 | cut -f1)
echo ""
echo "=== DONE ==="
echo "Final video: ISOTTO-Sport-Demo-TITLED.mp4"
echo "Duration:    ${DURATION}s (~$(( DURATION / 60 ))m $(( DURATION % 60 ))s)"
echo "Size:        ${SIZE}"
echo ""
echo "Structure:"
echo "  Intro (4s) -> [Card+Scene] x7 -> Outro (5s)"
echo ""
echo "Next: Add background music"
echo "  ffmpeg -i ISOTTO-Sport-Demo-TITLED.mp4 -i music.mp3 \\"
echo "    -c:v copy -c:a aac -b:a 128k -ar 48000 -shortest \\"
echo "    -filter:a 'volume=0.15' ISOTTO-Sport-Demo-FINAL.mp4"
