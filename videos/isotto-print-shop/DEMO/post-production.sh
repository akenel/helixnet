#!/bin/bash
# ISOTTO Sport Demo -- Post-Production Script
# Run from: videos/isotto-print-shop/DEMO/
#
# BEFORE RUNNING:
# 1. Copy your raw OBS recording to this folder (or set RAW_FILE path)
# 2. Set RAW_FILE below to the filename
# 3. Set TRIM_END to the timestamp where the outro card appears
# 4. VERIFY the raw recording shows the ISOTTO app (not your desktop!)

set -e

RAW_FILE="raw-recording.mp4"       # <-- CHANGE THIS to your OBS filename
TRIM_START="0"                      # Start of content (after intro card settles)
TRIM_END="270"                      # <-- CHANGE THIS (seconds) to cut point before outro

echo "=== ISOTTO Sport Demo Post-Production ==="
echo ""

# Step 0: Quick verification -- extract frame at 10s, show what we captured
echo "[0/6] Verifying raw recording content..."
ffmpeg -y -ss 10 -i "$RAW_FILE" -vframes 1 arc/verify-frame.jpg 2>/dev/null
echo "  Extracted frame at 10s -> arc/verify-frame.jpg"
echo "  CHECK: Does this show the ISOTTO app? If it shows your desktop, STOP."
echo "  Press ENTER to continue, or Ctrl+C to abort."
read -r

# Step 1: Strip audio (OBS captures ambient noise)
echo "[1/6] Stripping audio from raw recording..."
ffmpeg -y -i "$RAW_FILE" -an -c:v copy arc/silent.mp4

# Step 2: Trim main content
echo "[2/6] Trimming content to ${TRIM_START}s - ${TRIM_END}s..."
ffmpeg -y -i arc/silent.mp4 -ss "$TRIM_START" -to "$TRIM_END" -c copy arc/content-trimmed.mp4

# Step 3: Re-encode content to match intro/outro encoding (prevents timestamp issues)
echo "[3/6] Re-encoding content to match intro/outro format..."
ffmpeg -y -i arc/content-trimmed.mp4 -c:v libx264 -crf 18 -preset slow \
  -pix_fmt yuv420p -r 30 -an arc/content-fixed.mp4

# Step 4: Create intro clip from PNG (4s)
echo "[4/6] Creating intro clip (4s)..."
ffmpeg -y -loop 1 -i intro.png -c:v libx264 -t 4 -pix_fmt yuv420p -r 30 arc/intro-clip.mp4

# Step 5: Create outro clip from PNG (5s)
echo "[5/6] Creating outro clip (5s)..."
ffmpeg -y -loop 1 -i outro.png -c:v libx264 -t 5 -pix_fmt yuv420p -r 30 arc/outro-clip.mp4

# Step 6: Stitch everything together (using re-encoded content)
echo "[6/6] Stitching final video..."
cd arc
cat > concat-final.txt <<EOF
file 'intro-clip.mp4'
file 'content-fixed.mp4'
file 'outro-clip.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i concat-final.txt -c copy ../ISOTTO-Sport-Demo.mp4
cd ..

# Show result
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 ISOTTO-Sport-Demo.mp4 2>/dev/null | cut -d. -f1)
echo ""
echo "=== DONE ==="
echo "Final video: ISOTTO-Sport-Demo.mp4 (${DURATION}s)"
echo ""
echo "Next steps:"
echo "  1. Record voiceover per scene (Telegram voice messages)"
echo "  2. Transcribe with Whisper for verification"
echo "  3. Merge: ffmpeg -i ISOTTO-Sport-Demo.mp4 -i voiceover.m4a -c:v copy -c:a aac -b:a 128k -ar 48000 ISOTTO-Sport-Demo-FINAL.mp4"
