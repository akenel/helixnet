#!/bin/bash
# =============================================================================
# 🎬 FLIXER — The Blockhead Movie Factory
# =============================================================================
# Usage: ./flixer.sh <input.png> [output.mp4] [duration] [zoom_target]
#
# Examples:
#   ./flixer.sh scene-001.png                    # Basic Ken Burns
#   ./flixer.sh scene-001.png scene-001.mp4 10  # 10 second video
#   ./flixer.sh scene-001.png scene-001.mp4 10 bottom  # Zoom to bottom
#
# Zoom targets: center, bottom, top, left, right
# =============================================================================

INPUT="$1"
OUTPUT="${2:-${INPUT%.png}.mp4}"
DURATION="${3:-10}"
ZOOM_TARGET="${4:-bottom}"

if [ -z "$INPUT" ]; then
    echo "🍞 FLIXER — The Blockhead Movie Factory"
    echo ""
    echo "Usage: ./flixer.sh <input.png> [output.mp4] [duration] [zoom_target]"
    echo ""
    echo "Zoom targets: center, bottom, top"
    echo ""
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "❌ File not found: $INPUT"
    exit 1
fi

# Calculate frames (30fps)
FRAMES=$((DURATION * 30))

# Set zoom target coordinates
case $ZOOM_TARGET in
    bottom)
        X_EXPR="iw/2-(iw/zoom/2)"
        Y_EXPR="ih*0.75-(ih/zoom/2)"
        ;;
    top)
        X_EXPR="iw/2-(iw/zoom/2)"
        Y_EXPR="ih*0.25-(ih/zoom/2)"
        ;;
    center)
        X_EXPR="iw/2-(iw/zoom/2)"
        Y_EXPR="ih/2-(ih/zoom/2)"
        ;;
    *)
        X_EXPR="iw/2-(iw/zoom/2)"
        Y_EXPR="ih*0.75-(ih/zoom/2)"
        ;;
esac

echo "🎬 FLIXER Processing..."
echo "   Input:  $INPUT"
echo "   Output: $OUTPUT"
echo "   Duration: ${DURATION}s"
echo "   Zoom: $ZOOM_TARGET"
echo ""

ffmpeg -y -loop 1 -i "$INPUT" \
    -vf "zoompan=z='1+on/${FRAMES}*0.3':x='${X_EXPR}':y='${Y_EXPR}':d=${FRAMES}:s=1024x1024:fps=30,format=yuv420p" \
    -t "$DURATION" \
    -c:v libx264 \
    -pix_fmt yuv420p \
    "$OUTPUT" 2>/dev/null

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$OUTPUT" | cut -f1)
    echo "✅ Done! $OUTPUT ($SIZE)"
    echo ""
    echo "🐅 The kid pushed the button."
else
    echo "❌ FFmpeg failed"
    exit 1
fi
