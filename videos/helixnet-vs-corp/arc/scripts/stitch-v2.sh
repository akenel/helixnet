#!/bin/bash
# ============================================================
# ONE AFTERNOON VS 16 WEEKS -- Video Assembly v2
# All clips re-encoded to identical: 1920x1080, 30fps, h264, aac 48kHz stereo
# ============================================================
set -e

DIR="/home/angel/repos/helixnet/videos/helixnet-vs-corp"
WEBCAM="$DIR/RAW Audio and video webcam capture - TAKE 5 --OBS_2026-02-18 12-19-38.mp4"
OUT="$DIR/FINAL-one-afternoon-vs-16-weeks.mp4"
VENC="-c:v libx264 -preset fast -crf 18 -r 30 -pix_fmt yuv420p"
AENC="-c:a aac -b:a 128k -ar 48000 -ac 2"

# Common filter for scaling images to exactly 1920x1080
SCALE="scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"

echo "=== STEP 1: Re-encode webcam with normalized audio ==="
ffmpeg -y -i "$WEBCAM" \
  -vf "fps=30" \
  $VENC \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
  $AENC \
  "$DIR/p3-webcam.mp4" 2>/dev/null
echo "OK: Webcam normalized"

echo "=== STEP 2: Create image clips (with silent audio) ==="

# Function: image to video clip with silent audio
make_clip() {
  local input="$1" output="$2" duration="$3" fadein="$4" fadeout="$5"
  ffmpeg -y \
    -loop 1 -t "$duration" -i "$input" \
    -f lavfi -t "$duration" -i "anullsrc=channel_layout=stereo:sample_rate=48000" \
    -vf "${SCALE},fade=t=in:st=0:d=${fadein},fade=t=out:st=$(echo "$duration - $fadeout" | bc):d=${fadeout},fps=30" \
    $VENC $AENC \
    -shortest \
    "$output" 2>/dev/null
  echo "OK: $(basename $output)"
}

make_clip "$DIR/intro-card.png"          "$DIR/p1-intro.mp4"       4 1 1
make_clip "$DIR/hetzner-console.png"     "$DIR/p2a-hetzner.mp4"    3 0.5 0.5
make_clip "$DIR/screen-docker-ps.png"    "$DIR/p2b-dockerps.mp4"   4 0.5 0.5
make_clip "$DIR/screen-login-page.png"   "$DIR/p2c-loginpage.mp4"  2 0.3 0.3
make_clip "$DIR/screen-keycloak-login.png" "$DIR/p2d-keycloak.mp4" 2 0.3 0.3
make_clip "$DIR/screen-logged-in.png"    "$DIR/p2e-dashboard.mp4"  4 0.5 0.5
make_clip "$DIR/comparison-slide.png"    "$DIR/p4-comparison.mp4"  6 0.5 0.5
make_clip "$DIR/outro-card.png"          "$DIR/p5-outro.mp4"       5 1 1

echo "=== STEP 3: Verify all clips ==="
for f in p1-intro p2a-hetzner p2b-dockerps p2c-loginpage p2d-keycloak p2e-dashboard p3-webcam p4-comparison p5-outro; do
  DUR=$(ffprobe -v quiet -print_format json -show_format "$DIR/$f.mp4" | python3 -c "import json,sys; print(f'{float(json.load(sys.stdin)[\"format\"][\"duration\"]):.1f}s')")
  echo "  $f: $DUR"
done

echo "=== STEP 4: Concatenate ==="
cat > "$DIR/concat.txt" << CONCAT
file 'p1-intro.mp4'
file 'p2a-hetzner.mp4'
file 'p2b-dockerps.mp4'
file 'p2c-loginpage.mp4'
file 'p2d-keycloak.mp4'
file 'p2e-dashboard.mp4'
file 'p3-webcam.mp4'
file 'p4-comparison.mp4'
file 'p5-outro.mp4'
CONCAT

ffmpeg -y -f concat -safe 0 -i "$DIR/concat.txt" \
  -c copy \
  -movflags +faststart \
  "$OUT" 2>/dev/null

echo "=== STEP 5: Cleanup ==="
rm -f "$DIR"/p1-*.mp4 "$DIR"/p2*.mp4 "$DIR"/p3-*.mp4 "$DIR"/p4-*.mp4 "$DIR"/p5-*.mp4 "$DIR/concat.txt"

echo ""
echo "============================================"
DURATION=$(ffprobe -v quiet -print_format json -show_format "$OUT" | python3 -c "import json,sys; print(f'{float(json.load(sys.stdin)[\"format\"][\"duration\"]):.1f}')")
SIZE=$(du -h "$OUT" | cut -f1)
echo "FINAL: $OUT"
echo "Duration: ${DURATION}s ($(echo "$DURATION / 60" | bc)m$(echo "$DURATION % 60 / 1" | bc)s)"
echo "Size: $SIZE"
echo "============================================"
