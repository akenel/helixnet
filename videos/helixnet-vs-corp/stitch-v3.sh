#!/bin/bash
# ============================================================
# ONE AFTERNOON VS 16 WEEKS -- Final Assembly v3
# Option A: Full-frame cuts, audio runs throughout
# ============================================================
# Timeline (based on Whisper transcription):
#   0:00-0:10  "Check one two..." -> TRIM (dead air)
#   0:10-0:35  Hook - what we built, EUR 7.59 -> WEBCAM
#   0:35-0:44  "Hetzner Cloud console..." -> HETZNER SCREENSHOT
#   0:44-1:12  Server specs, containers -> DOCKER PS
#   1:12-1:25  "Real login, real Keycloak" -> KEYCLOAK + DASHBOARD
#   1:25-1:33  "Not a demo, production grade" -> DASHBOARD
#   1:33-2:32  Comparison walkthrough -> COMPARISON SLIDE
#   2:32-2:42  "Decision latency" -> TEXT CARD
#   2:42-3:12  "90% building, war room" -> WEBCAM
#   3:12-3:21  "That is ownership" -> TEXT CARD
#   3:21-3:35  SAP trap -> TEXT CARD
#   3:35-3:53  HelixNet pitch -> TEXT CARD
#   3:53-4:01  "Let's talk" -> WEBCAM
#   4:01-4:11  "That's a take" -> TRIM (dead air)
# ============================================================
set -e

DIR="/home/angel/repos/helixnet/videos/helixnet-vs-corp"
WEBCAM="$DIR/RAW Audio and video webcam capture - TAKE 5 --OBS_2026-02-18 12-19-38.mp4"
OUT="$DIR/FINAL-one-afternoon-vs-16-weeks.mp4"
VENC="-c:v libx264 -preset fast -crf 18 -r 30 -pix_fmt yuv420p"
AENC="-c:a aac -b:a 128k -ar 48000 -ac 2"
SCALE="scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"

rm -f "$DIR"/seg-*.mp4 "$DIR/FINAL-one-afternoon-vs-16-weeks.mp4"

echo "=== STEP 1: Extract trimmed audio (0:10 to 4:01) ==="
ffmpeg -y -ss 10 -to 241 -i "$WEBCAM" \
  -vn -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
  $AENC \
  "$DIR/master-audio.m4a" 2>/dev/null
echo "OK: Master audio (3:51)"

echo "=== STEP 2: Create video segments ==="

# Helper: extract webcam segment (times relative to ORIGINAL file)
webcam_seg() {
  local name="$1" ss="$2" to="$3"
  ffmpeg -y -ss "$ss" -to "$to" -i "$WEBCAM" \
    -vf "fps=30" $VENC -an \
    "$DIR/seg-${name}.mp4" 2>/dev/null
  echo "OK: seg-${name} (webcam ${ss}s-${to}s)"
}

# Helper: image to video segment
img_seg() {
  local name="$1" img="$2" duration="$3"
  ffmpeg -y -loop 1 -t "$duration" -i "$img" \
    -vf "${SCALE},fps=30" $VENC -an \
    "$DIR/seg-${name}.mp4" 2>/dev/null
  echo "OK: seg-${name} (image ${duration}s)"
}

# Intro card (separate, before trimmed audio starts)
img_seg "00-intro" "$DIR/intro-card.png" 4

# 0:10-0:35 = Hook on webcam (25s)
webcam_seg "01-hook" 10 35

# 0:35-0:44 = Hetzner console (9s)
img_seg "02-hetzner" "$DIR/hetzner-console.png" 9

# 0:44-1:12 = Docker ps (28s)
img_seg "03-dockerps" "$DIR/screen-docker-ps.png" 28

# 1:12-1:19 = Keycloak login (7s)
img_seg "04-keycloak" "$DIR/screen-keycloak-login.png" 7

# 1:19-1:33 = Dashboard (14s)
img_seg "05-dashboard" "$DIR/screen-logged-in.png" 14

# 1:33-2:32 = Comparison slide (59s)
img_seg "06-comparison" "$DIR/comparison-slide.png" 59

# 2:32-2:42 = Decision latency text card (10s)
img_seg "07-latency" "$DIR/text-card-decision-latency.png" 10

# 2:42-3:12 = Back to webcam (30s)
webcam_seg "08-building" 162 192

# 3:12-3:21 = Ownership text card (9s)
img_seg "09-ownership" "$DIR/text-card-ownership.png" 9

# 3:21-3:35 = SAP trap text card (14s)
img_seg "10-trap" "$DIR/text-card-trap.png" 14

# 3:35-3:53 = HelixNet pitch text card (18s)
img_seg "11-helixnet" "$DIR/text-card-helixnet.png" 18

# 3:53-4:01 = "Let's talk" on webcam (8s)
webcam_seg "12-letstalk" 233 241

# Outro card (separate, after trimmed audio ends)
img_seg "13-outro" "$DIR/outro-card.png" 5

echo ""
echo "=== STEP 3: Concat video segments ==="
cat > "$DIR/concat-v3.txt" << 'EOF'
file 'seg-00-intro.mp4'
file 'seg-01-hook.mp4'
file 'seg-02-hetzner.mp4'
file 'seg-03-dockerps.mp4'
file 'seg-04-keycloak.mp4'
file 'seg-05-dashboard.mp4'
file 'seg-06-comparison.mp4'
file 'seg-07-latency.mp4'
file 'seg-08-building.mp4'
file 'seg-09-ownership.mp4'
file 'seg-10-trap.mp4'
file 'seg-11-helixnet.mp4'
file 'seg-12-letstalk.mp4'
file 'seg-13-outro.mp4'
EOF

ffmpeg -y -f concat -safe 0 -i "$DIR/concat-v3.txt" \
  $VENC -an \
  "$DIR/video-only.mp4" 2>/dev/null
echo "OK: Video track assembled"

echo "=== STEP 4: Create full audio track (silence + voice + silence) ==="
# 4s intro silence + 231s voice + 5s outro silence = 240s
VOICE_DUR=$(ffprobe -v quiet -print_format json -show_format "$DIR/master-audio.m4a" | python3 -c "import json,sys; print(f'{float(json.load(sys.stdin)[\"format\"][\"duration\"]):.3f}')")
echo "Voice duration: ${VOICE_DUR}s"

ffmpeg -y \
  -f lavfi -t 4 -i "anullsrc=channel_layout=stereo:sample_rate=48000" \
  -i "$DIR/master-audio.m4a" \
  -f lavfi -t 5 -i "anullsrc=channel_layout=stereo:sample_rate=48000" \
  -filter_complex "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]" \
  -map "[out]" $AENC \
  "$DIR/full-audio.m4a" 2>/dev/null
echo "OK: Full audio track"

echo "=== STEP 5: Merge video + audio ==="
VIDEO_DUR=$(ffprobe -v quiet -print_format json -show_format "$DIR/video-only.mp4" | python3 -c "import json,sys; print(f'{float(json.load(sys.stdin)[\"format\"][\"duration\"]):.1f}')")
AUDIO_DUR=$(ffprobe -v quiet -print_format json -show_format "$DIR/full-audio.m4a" | python3 -c "import json,sys; print(f'{float(json.load(sys.stdin)[\"format\"][\"duration\"]):.1f}')")
echo "Video: ${VIDEO_DUR}s  Audio: ${AUDIO_DUR}s"

ffmpeg -y -i "$DIR/video-only.mp4" -i "$DIR/full-audio.m4a" \
  -c:v copy $AENC \
  -shortest \
  -movflags +faststart \
  "$OUT" 2>/dev/null

echo "=== STEP 6: Cleanup ==="
rm -f "$DIR"/seg-*.mp4 "$DIR/video-only.mp4" "$DIR/full-audio.m4a" "$DIR/master-audio.m4a" "$DIR/concat-v3.txt"

echo ""
echo "============================================"
DURATION=$(ffprobe -v quiet -print_format json -show_format "$OUT" | python3 -c "import json,sys; d=float(json.load(sys.stdin)['format']['duration']); m=int(d//60); s=int(d%60); print(f'{d:.1f}s ({m}m{s:02d}s)')")
SIZE=$(du -h "$OUT" | cut -f1)
echo "FINAL: $OUT"
echo "Duration: $DURATION"
echo "Size: $SIZE"
echo "============================================"
