#!/bin/bash
# ============================================================
# ONE AFTERNOON VS 16 WEEKS -- Video Assembly
# ============================================================
set -e

DIR="/home/angel/repos/helixnet/videos/helixnet-vs-corp"
WEBCAM="$DIR/RAW Audio and video webcam capture - TAKE 5 --OBS_2026-02-18 12-19-38.mp4"
OUT="$DIR/FINAL-one-afternoon-vs-16-weeks.mp4"

echo "=== STEP 1: Normalize webcam audio ==="
ffmpeg -y -i "$WEBCAM" \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
  -c:v copy \
  -c:a aac -b:a 128k -ar 48000 \
  "$DIR/tmp-webcam-normalized.mp4" 2>/dev/null
echo "OK: Audio normalized"

echo "=== STEP 2: Create image clips ==="

# Intro card - 4 seconds with fade in from black
ffmpeg -y -loop 1 -i "$DIR/intro-card.png" \
  -t 4 -r 30 -pix_fmt yuv420p \
  -vf "fade=t=in:st=0:d=1,fade=t=out:st=3:d=1" \
  -c:v libx264 -preset fast -crf 18 \
  -an \
  "$DIR/tmp-intro.mp4" 2>/dev/null
echo "OK: Intro card (4s)"

# Hetzner console - 3 seconds
ffmpeg -y -loop 1 -i "$DIR/hetzner-console.png" \
  -t 3 -r 30 -pix_fmt yuv420p \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fade=t=in:st=0:d=0.5,fade=t=out:st=2.5:d=0.5" \
  -c:v libx264 -preset fast -crf 18 \
  -an \
  "$DIR/tmp-hetzner.mp4" 2>/dev/null
echo "OK: Hetzner console (3s)"

# Docker ps - 4 seconds (key proof shot, hold longer)
ffmpeg -y -loop 1 -i "$DIR/screen-docker-ps.png" \
  -t 4 -r 30 -pix_fmt yuv420p \
  -vf "fade=t=in:st=0:d=0.5,fade=t=out:st=3.5:d=0.5" \
  -c:v libx264 -preset fast -crf 18 \
  -an \
  "$DIR/tmp-dockerps.mp4" 2>/dev/null
echo "OK: Docker ps (4s)"

# Login page - 2 seconds
ffmpeg -y -loop 1 -i "$DIR/screen-login-page.png" \
  -t 2 -r 30 -pix_fmt yuv420p \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fade=t=in:st=0:d=0.3,fade=t=out:st=1.7:d=0.3" \
  -c:v libx264 -preset fast -crf 18 \
  -an \
  "$DIR/tmp-loginpage.mp4" 2>/dev/null
echo "OK: Login page (2s)"

# Keycloak login form - 2 seconds
ffmpeg -y -loop 1 -i "$DIR/screen-keycloak-login.png" \
  -t 2 -r 30 -pix_fmt yuv420p \
  -vf "fade=t=in:st=0:d=0.3,fade=t=out:st=1.7:d=0.3" \
  -c:v libx264 -preset fast -crf 18 \
  -an \
  "$DIR/tmp-keycloak.mp4" 2>/dev/null
echo "OK: Keycloak login (2s)"

# Dashboard - 4 seconds (money shot, hold it)
ffmpeg -y -loop 1 -i "$DIR/screen-logged-in.png" \
  -t 4 -r 30 -pix_fmt yuv420p \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fade=t=in:st=0:d=0.5,fade=t=out:st=3.5:d=0.5" \
  -c:v libx264 -preset fast -crf 18 \
  -an \
  "$DIR/tmp-dashboard.mp4" 2>/dev/null
echo "OK: Dashboard (4s)"

# Comparison slide - 6 seconds
ffmpeg -y -loop 1 -i "$DIR/comparison-slide.png" \
  -t 6 -r 30 -pix_fmt yuv420p \
  -vf "fade=t=in:st=0:d=0.5,fade=t=out:st=5.5:d=0.5" \
  -c:v libx264 -preset fast -crf 18 \
  -an \
  "$DIR/tmp-comparison.mp4" 2>/dev/null
echo "OK: Comparison slide (6s)"

# Outro card - 5 seconds with fade out to black
ffmpeg -y -loop 1 -i "$DIR/outro-card.png" \
  -t 5 -r 30 -pix_fmt yuv420p \
  -vf "fade=t=in:st=0:d=1,fade=t=out:st=4:d=1" \
  -c:v libx264 -preset fast -crf 18 \
  -an \
  "$DIR/tmp-outro.mp4" 2>/dev/null
echo "OK: Outro card (5s)"

echo "=== STEP 3: Add silent audio to image clips ==="
for f in tmp-intro tmp-hetzner tmp-dockerps tmp-loginpage tmp-keycloak tmp-dashboard tmp-comparison tmp-outro; do
  ffmpeg -y -i "$DIR/$f.mp4" \
    -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 \
    -c:v copy -c:a aac -b:a 128k -shortest \
    "$DIR/${f}-audio.mp4" 2>/dev/null
done
echo "OK: Silent audio tracks added"

echo "=== STEP 4: Concatenate everything ==="
cat > "$DIR/concat.txt" << 'CONCAT'
file 'tmp-intro-audio.mp4'
file 'tmp-hetzner-audio.mp4'
file 'tmp-dockerps-audio.mp4'
file 'tmp-loginpage-audio.mp4'
file 'tmp-keycloak-audio.mp4'
file 'tmp-dashboard-audio.mp4'
file 'tmp-webcam-normalized.mp4'
file 'tmp-comparison-audio.mp4'
file 'tmp-outro-audio.mp4'
CONCAT

ffmpeg -y -f concat -safe 0 -i "$DIR/concat.txt" \
  -c:v libx264 -preset fast -crf 18 \
  -c:a aac -b:a 128k -ar 48000 \
  -movflags +faststart \
  "$OUT" 2>/dev/null

echo "=== STEP 5: Cleanup temp files ==="
rm -f "$DIR"/tmp-*.mp4 "$DIR/concat.txt"

echo ""
echo "============================================"
DURATION=$(ffprobe -v quiet -print_format json -show_format "$OUT" | python3 -c "import json,sys; print(f'{float(json.load(sys.stdin)[\"format\"][\"duration\"]):.1f}')")
SIZE=$(du -h "$OUT" | cut -f1)
echo "FINAL VIDEO: $OUT"
echo "Duration: ${DURATION}s"
echo "Size: $SIZE"
echo "============================================"
