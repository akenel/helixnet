#!/bin/bash
# ISOTTO Sport Demo -- Post-Production Script
# Run from: videos/isotto-print-shop/DEMO/
#
# BEFORE RUNNING:
# 1. Copy your raw OBS recording to this folder
# 2. Set RAW_FILE below to the filename
# 3. Set TRIM_END to the timestamp where the outro card appears

set -e

RAW_FILE="raw-recording.mp4"       # <-- CHANGE THIS to your OBS filename
TRIM_START="0"                      # Start of content (after intro card settles)
TRIM_END="270"                      # <-- CHANGE THIS (seconds) to cut point before outro

echo "=== ISOTTO Sport Demo Post-Production ==="
echo ""

# Step 1: Strip audio (OBS captures ambient noise)
echo "[1/5] Stripping audio from raw recording..."
ffmpeg -y -i "$RAW_FILE" -an -c:v copy arc/silent.mp4

# Step 2: Trim main content
echo "[2/5] Trimming content to ${TRIM_START}s - ${TRIM_END}s..."
ffmpeg -y -i arc/silent.mp4 -ss "$TRIM_START" -to "$TRIM_END" -c copy arc/content-trimmed.mp4

# Step 3: Create intro clip from PNG (4s)
echo "[3/5] Creating intro clip (4s)..."
ffmpeg -y -loop 1 -i intro.png -c:v libx264 -t 4 -pix_fmt yuv420p -r 30 arc/intro-clip.mp4

# Step 4: Create outro clip from PNG (5s)
echo "[4/5] Creating outro clip (5s)..."
ffmpeg -y -loop 1 -i outro.png -c:v libx264 -t 5 -pix_fmt yuv420p -r 30 arc/outro-clip.mp4

# Step 5: Stitch everything together
echo "[5/5] Stitching final video..."
cd arc
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy ../ISOTTO-Sport-Demo.mp4
cd ..

echo ""
echo "=== DONE ==="
echo "Final video: ISOTTO-Sport-Demo.mp4"
echo ""
echo "Next steps:"
echo "  1. Record voiceover per scene (Telegram voice messages)"
echo "  2. Transcribe with Whisper for verification"
echo "  3. Merge: ffmpeg -i ISOTTO-Sport-Demo.mp4 -i voiceover.m4a -c:v copy -c:a aac -b:a 128k -ar 48000 ISOTTO-Sport-Demo-FINAL.mp4"
