#!/bin/bash
# readme.sh -- Read any .md or .txt file aloud (neural TTS via Piper)
#
# Usage: readme.sh PLOT.md              (default: Grace -- British female, smooth neural)
#        readme.sh PLOT.md --american   (American female)
#        readme.sh PLOT.md --slow       (slower speed)
#        readme.sh PLOT.md --save       (save WAV to same directory as input file)
#        readme.sh PLOT.md --save --american
#        readme.sh --stop               (stop current reading)
#        readme.sh --test               (quick test sentence)
#        readme.sh --robot PLOT.md      (fallback to spd-say if Piper unavailable)
#
# Default voice: Grace (en_GB-alba-medium) -- smooth British female, neural TTS
# Think Grace Hopper briefing you on your own plot files.

VENV="/home/angel/repos/helixnet/.venv"
VOICES="/home/angel/.local/share/piper-voices"

# Voice presets (Piper models)
VOICE="$VOICES/en_GB-alba-medium.onnx"       # Grace -- British female (default)
VOICE_NAME="Grace"
SPEED="1.0"
SAVE=false
ROBOT=false

FILE=""
for arg in "$@"; do
    case "$arg" in
        --stop)
            killall piper aplay paplay spd-say 2>/dev/null
            echo "Stopped."
            exit 0
            ;;
        --american)
            VOICE="$VOICES/en_US-lessac-medium.onnx"
            VOICE_NAME="Lessac"
            ;;
        --slow)
            SPEED="1.3"
            ;;
        --fast)
            SPEED="0.8"
            ;;
        --save)
            SAVE=true
            ;;
        --robot)
            ROBOT=true
            ;;
        --test)
            echo "Testing voice... ($VOICE_NAME, neural TTS)"
            echo "Hello Angel. I am Grace, your reader. Give me a markdown file and I will read it to you while you eat lunch, walk around, or just close your eyes and listen. Smooth, clear, no robot. Not bad for a free tool." | \
                "$VENV/bin/piper" --model "$VOICE" --length-scale "$SPEED" --output-raw 2>/dev/null | \
                aplay -r 22050 -f S16_LE -t raw -c 1 2>/dev/null
            exit 0
            ;;
        --voices)
            echo "Voice presets (Piper neural TTS):"
            echo ""
            echo "  (default)    Grace -- British female, smooth neural (en_GB-alba-medium)"
            echo "  --american   Lessac -- American female, clear neural (en_US-lessac-medium)"
            echo ""
            echo "Options:"
            echo "  --slow       Slower reading speed"
            echo "  --fast       Faster reading speed"
            echo "  --save       Save WAV file next to the input file"
            echo "  --robot      Use spd-say fallback (no Piper needed)"
            echo ""
            echo "Stop:   --stop  or  Ctrl+C"
            exit 0
            ;;
        *)
            if [ -z "$FILE" ]; then
                FILE="$arg"
            fi
            ;;
    esac
done

if [ -z "$FILE" ]; then
    echo "readme.sh -- Read files aloud (neural TTS)"
    echo ""
    echo "Usage: readme.sh <file> [--american|--slow|--fast|--save|--robot|--stop|--test|--voices]"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "File not found: $FILE"
    exit 1
fi

# Strip markdown formatting for cleaner speech
TEXT=$(cat "$FILE" | \
    sed 's/^#\+\s*/... /g' | \
    sed 's/\*\*//g' | \
    sed 's/\*//g' | \
    sed 's/`//g' | \
    sed 's/^-\s*/. /g' | \
    sed 's/^[0-9]\+\.\s*/. /g' | \
    sed 's/|/ /g' | \
    sed 's/---*/... /g' | \
    sed 's/\[//g; s/\]//g' | \
    sed 's/(http[^)]*)//g' | \
    sed '/^```/,/^```/d' | \
    sed '/^$/d' | \
    tr '\n' ' ' | \
    sed 's/  \+/ /g')

WORDS=$(echo "$TEXT" | wc -w)

# Robot mode fallback (spd-say)
if [ "$ROBOT" = true ]; then
    echo "Reading: $FILE ($WORDS words, voice: spd-say robot)"
    echo "Ctrl+C to stop."
    echo ""
    echo "$TEXT" | spd-say -e -w -r -25 -p 50 -l en-GB-X-RP -y Annie
    echo "Done."
    exit 0
fi

# Neural TTS mode (Piper)
if [ ! -f "$VOICE" ]; then
    echo "Voice model not found: $VOICE"
    echo "Run with --robot for spd-say fallback."
    exit 1
fi

echo "Reading: $FILE ($WORDS words, voice: $VOICE_NAME)"

if [ "$SAVE" = true ]; then
    # Save to WAV file next to the input
    DIR=$(dirname "$FILE")
    BASE=$(basename "$FILE" | sed 's/\.[^.]*$//')
    OUT="$DIR/${BASE}-${VOICE_NAME,,}.wav"
    echo "Saving to: $OUT"
    echo "$TEXT" | "$VENV/bin/piper" --model "$VOICE" --length-scale "$SPEED" --output_file "$OUT" 2>/dev/null
    echo "Saved: $OUT ($(du -h "$OUT" | cut -f1))"
    echo ""
    echo "Play it anytime:  aplay \"$OUT\""
else
    echo "Ctrl+C to stop."
    echo ""
    echo "$TEXT" | "$VENV/bin/piper" --model "$VOICE" --length-scale "$SPEED" --output-raw 2>/dev/null | \
        aplay -r 22050 -f S16_LE -t raw -c 1 2>/dev/null
fi

echo "Done."
