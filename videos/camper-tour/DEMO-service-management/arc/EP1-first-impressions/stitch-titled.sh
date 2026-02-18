#!/bin/bash
# Camper & Tour EP1 "First Impressions" -- Titled Scene Stitch Script
# Creates final video with scene title cards inserted between scenes
# Run from: videos/camper-tour/DEMO-service-management/EP1-first-impressions/
set -e

# ============================================================================
# USER CONFIG -- FILL IN AFTER RECORDING
# ============================================================================

# Raw recording filename (set this after OBS recording)
RAW_FILE="CHANGE-ME.mp4"

# Trim the raw recording (remove OBS pre-roll / post-roll)
# FILL IN AFTER WATCHING RAW RECORDING
TRIM_START="0"       # e.g. "3" to skip first 3 seconds
TRIM_END=""          # e.g. "180" to cut at 3:00 (leave empty for no trim)

# Scene boundaries (start:end in seconds) within the TRIMMED silent video
# FILL IN AFTER WATCHING RAW RECORDING
# Watch silent.mp4, note where each scene starts and ends
declare -A SCENES
SCENES[1]="0:0"     # Scene 1: Login & Dashboard
SCENES[2]="0:0"     # Scene 2: Vehicle Check-In
SCENES[3]="0:0"     # Scene 3: Job Board
SCENES[4]="0:0"     # Scene 4: Job Detail -- MAX Roof Seal (MONEY SHOT)
SCENES[5]="0:0"     # Scene 5: Customer Intelligence

# ============================================================================
# FIXED CONFIG -- DO NOT CHANGE
# ============================================================================

ARC="arc"
OUTPUT="CT-EP1-First-Impressions.mp4"
CARD_DURATION=5      # seconds per title card (shorter -- text is huge now)
INTRO_DURATION=4
OUTRO_DURATION=5
INTRO_PNG="arc/intro.png"
OUTRO_PNG="arc/outro.png"

echo "=== Camper & Tour EP1 -- First Impressions -- Scene Title Card Stitch ==="
echo ""

# --- Preflight checks ---
if [ "$RAW_FILE" = "CHANGE-ME.mp4" ]; then
  echo "ERROR: Set RAW_FILE at top of script to your raw recording filename"
  exit 1
fi
if [ ! -f "$RAW_FILE" ]; then
  echo "ERROR: Raw file not found: $RAW_FILE"
  exit 1
fi
for i in 1 2 3 4 5; do
  if [ "${SCENES[$i]}" = "0:0" ]; then
    echo "ERROR: Scene boundaries not set. Watch silent.mp4 and fill in SCENES[1-5]"
    exit 1
  fi
done

# --- Step 1: Create title card video clips from PNGs ---
echo "[1/6] Creating title card video clips (${CARD_DURATION}s each)..."
for i in 1 2 3 4 5; do
  ffmpeg -y -loop 1 -i "${ARC}/scene-card-${i}.png" \
    -c:v libx264 -t ${CARD_DURATION} -pix_fmt yuv420p -r 30 -an \
    "${ARC}/card-${i}.mp4" 2>/dev/null
  echo "  card-${i}.mp4  (${CARD_DURATION}s)"
done

# --- Step 2: Strip audio and trim raw recording ---
echo ""
echo "[2/6] Stripping audio and trimming raw recording..."

TRIM_ARGS=""
if [ -n "$TRIM_START" ] && [ "$TRIM_START" != "0" ]; then
  TRIM_ARGS="-ss ${TRIM_START}"
fi
if [ -n "$TRIM_END" ]; then
  TRIM_ARGS="${TRIM_ARGS} -to ${TRIM_END}"
fi

ffmpeg -y ${TRIM_ARGS} -i "${RAW_FILE}" \
  -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -r 30 -an \
  silent.mp4 2>/dev/null

SILENT_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 silent.mp4 2>/dev/null | cut -d. -f1)
echo "  silent.mp4 (${SILENT_DUR}s)"

# --- Step 3: Extract scene clips from silent video ---
echo ""
echo "[3/6] Extracting scene clips from silent.mp4..."

for i in 1 2 3 4 5; do
  IFS=':' read -r start end <<< "${SCENES[$i]}"
  # Re-encode to match intro/outro format (prevents concat issues)
  ffmpeg -y -ss "${start}" -to "${end}" -i silent.mp4 \
    -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -r 30 -an \
    "${ARC}/scene-${i}.mp4" 2>/dev/null
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${ARC}/scene-${i}.mp4" 2>/dev/null | cut -d. -f1)
  echo "  scene-${i}.mp4  (${dur}s)"
done

# --- Step 4: Create intro and outro clips ---
echo ""
echo "[4/6] Creating intro/outro clips..."

ffmpeg -y -loop 1 -i "${INTRO_PNG}" \
  -c:v libx264 -t ${INTRO_DURATION} -pix_fmt yuv420p -r 30 -an \
  "${ARC}/intro-clip.mp4" 2>/dev/null
echo "  intro-clip.mp4  (${INTRO_DURATION}s)"

ffmpeg -y -loop 1 -i "${OUTRO_PNG}" \
  -c:v libx264 -t ${OUTRO_DURATION} -pix_fmt yuv420p -r 30 -an \
  "${ARC}/outro-clip.mp4" 2>/dev/null
echo "  outro-clip.mp4  (${OUTRO_DURATION}s)"

# --- Step 5: Build concat list and stitch ---
echo ""
echo "[5/6] Stitching final titled video..."

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
file 'outro-clip.mp4'
EOF

cd "${ARC}"
ffmpeg -y -f concat -safe 0 -i concat-titled.txt -c copy "../${OUTPUT}" 2>/dev/null
cd ..

# --- Step 6: Report ---
echo ""
echo "[6/6] Verifying output..."

DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${OUTPUT}" 2>/dev/null | cut -d. -f1)
SIZE=$(du -h "${OUTPUT}" | cut -f1)

echo ""
echo "=== DONE ==="
echo "Final video: ${OUTPUT}"
echo "Duration:    ${DURATION}s (~$(( DURATION / 60 ))m $(( DURATION % 60 ))s)"
echo "Size:        ${SIZE}"
echo ""
echo "Structure:"
echo "  Intro (${INTRO_DURATION}s)"
echo "    Card 1 (${CARD_DURATION}s) + Scene 1: Login & Dashboard"
echo "    Card 2 (${CARD_DURATION}s) + Scene 2: Vehicle Check-In"
echo "    Card 3 (${CARD_DURATION}s) + Scene 3: Job Board"
echo "    Card 4 (${CARD_DURATION}s) + Scene 4: Job Detail -- MAX Roof Seal"
echo "    Card 5 (${CARD_DURATION}s) + Scene 5: Customer Intelligence"
echo "  Outro (${OUTRO_DURATION}s)"
echo ""
echo "=== NEXT STEPS ==="
echo ""
echo "1. Add voiceover:"
echo "   ffmpeg -i ${OUTPUT} -i voiceover.mp3 \\"
echo "     -c:v copy -c:a aac -b:a 128k -ar 48000 \\"
echo "     CT-EP1-First-Impressions-VOICED.mp4"
echo ""
echo "2. Add background music (low volume under voice):"
echo "   ffmpeg -i CT-EP1-First-Impressions-VOICED.mp4 -i music.mp3 \\"
echo "     -filter_complex '[0:a][1:a]amerge=inputs=2,pan=stereo|c0<c0+0.15*c2|c1<c1+0.15*c3' \\"
echo "     -c:v copy -c:a aac -b:a 128k -ar 48000 -shortest \\"
echo "     CT-EP1-First-Impressions-FINAL.mp4"
