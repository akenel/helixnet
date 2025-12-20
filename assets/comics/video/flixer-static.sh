#!/bin/bash
# =============================================================================
# 🎬 FLIXER-STATIC — Clean Blockhead Video (No Ken Burns)
# =============================================================================
# Usage: ./flixer-static.sh <input.png> [output.mp4] [duration]
#
# For 3-panel horizontal strips where Ken Burns zoom fights the composition.
# Respects original aspect ratio, outputs 1920x1080 landscape.
#
# Examples:
#   ./flixer-static.sh scene-001.png                    # Default 10s
#   ./flixer-static.sh scene-001.png scene-001.mp4 8   # 8 seconds
# =============================================================================

INPUT="$1"
OUTPUT="${2:-${INPUT%.png}.mp4}"
DURATION="${3:-10}"

if [ -z "$INPUT" ]; then
    echo "🍞 FLIXER-STATIC — Clean Blockhead Video"
    echo ""
    echo "Usage: ./flixer-static.sh <input.png> [output.mp4] [duration]"
    echo ""
    echo "No Ken Burns. No zoom. Just clean 3-panel glory."
    echo ""
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "❌ File not found: $INPUT"
    exit 1
fi

echo "🎬 FLIXER-STATIC Processing..."
echo "   Input:  $INPUT"
echo "   Output: $OUTPUT"
echo "   Duration: ${DURATION}s"
echo "   Mode: STATIC (no zoom)"
echo ""

# Scale to 1920x1080, pad if needed to maintain aspect ratio
ffmpeg -y -loop 1 -i "$INPUT" \
    -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,format=yuv420p" \
    -t "$DURATION" \
    -c:v libx264 \
    -pix_fmt yuv420p \
    -r 30 \
    "$OUTPUT" 2>/dev/null

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$OUTPUT" | cut -f1)
    echo "✅ Done! $OUTPUT ($SIZE)"
    echo ""
    echo "🐅 Be water, my friend."
else
    echo "❌ FFmpeg failed"
    exit 1
fi
