#!/bin/bash
# readme.sh -- Grace Hopper reads your files aloud (neural TTS via Piper)
#
# Usage: readme.sh PLOT.md              (default: Grace Hopper -- British English)
#        readme.sh PLOT.md --italian    (Grace Hopper -- Italian)
#        readme.sh PLOT.md --american   (Grace Hopper -- American English)
#        readme.sh PLOT.md --slow       (slower speed)
#        readme.sh PLOT.md --save       (save WAV to same directory as input file)
#        readme.sh --stop               (stop current reading)
#        readme.sh --test               (quick test sentence)
#        readme.sh --test --italian     (test Italian voice)
#
# One voice. One name. 3 languages (more coming).
# Grace Hopper -- named after the Admiral who said
# "It's easier to ask forgiveness than permission."

VENV="/home/angel/repos/helixnet/.venv"
VOICES="/home/angel/.local/share/piper-voices"

# Grace Hopper -- one voice, many languages
VOICE="$VOICES/en_GB-alba-medium.onnx"
LANG="English"
SPEED="1.0"
SAVE=false
ROBOT=false

FILE=""
DO_TEST=false

# First pass: collect all flags
for arg in "$@"; do
    case "$arg" in
        --stop)
            killall piper aplay paplay spd-say 2>/dev/null
            echo "Stopped."
            exit 0
            ;;
        --italian|--it)
            VOICE="$VOICES/it_IT-paola-medium.onnx"
            LANG="Italiano"
            ;;
        --american|--us)
            VOICE="$VOICES/en_US-lessac-medium.onnx"
            LANG="American"
            ;;
        --slow)   SPEED="1.3" ;;
        --fast)   SPEED="0.8" ;;
        --save)   SAVE=true ;;
        --robot)  ROBOT=true ;;
        --test)   DO_TEST=true ;;
        --voices)
            echo "Grace Hopper -- Neural TTS Reader"
            echo ""
            echo "  Languages:"
            echo "    (default)    English (British)     en_GB-alba-medium"
            echo "    --italian    Italiano              it_IT-paola-medium"
            echo "    --american   English (American)    en_US-lessac-medium"
            echo ""
            echo "  Options:"
            echo "    --slow       Slower reading speed"
            echo "    --fast       Faster reading speed"
            echo "    --save       Save WAV file next to the input file"
            echo "    --robot      Use spd-say fallback (no Piper needed)"
            echo ""
            echo "  Stop:   --stop  or  Ctrl+C"
            echo ""
            echo "  \"It's easier to ask forgiveness than permission.\""
            echo "                                    -- Grace Hopper"
            exit 0
            ;;
        *)
            if [ -z "$FILE" ]; then
                FILE="$arg"
            fi
            ;;
    esac
done

# Handle --test after all flags are parsed (so --italian --test works)
if [ "$DO_TEST" = true ]; then
    if [ "$LANG" = "Italiano" ]; then
        TEST_TEXT="Buongiorno Angelo. Sono Grace Hopper, la tua lettrice. Dammi un file e te lo leggo io, mentre mangi, cammini, o semplicemente chiudi gli occhi e ascolti. Non male per uno strumento gratuito."
    else
        TEST_TEXT="Hello Angel. I am Grace Hopper, your reader. Give me a markdown file and I will read it to you while you eat lunch, walk around, or just close your eyes and listen. Smooth, clear, no robot. Not bad for a free tool."
    fi
    echo "Grace Hopper ($LANG)"
    echo "$TEST_TEXT" | \
        "$VENV/bin/piper" --model "$VOICE" --length-scale "$SPEED" --output-raw 2>/dev/null | \
        aplay -r 22050 -f S16_LE -t raw -c 1 2>/dev/null
    exit 0
fi

if [ -z "$FILE" ]; then
    echo "Grace Hopper -- Neural TTS Reader"
    echo ""
    echo "Usage: readme.sh <file> [--italian|--american|--slow|--fast|--save|--stop|--test|--voices]"
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
    echo "Grace Hopper ($LANG, robot fallback) -- $WORDS words"
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

echo "Grace Hopper ($LANG) -- $WORDS words"

if [ "$SAVE" = true ]; then
    DIR=$(dirname "$FILE")
    BASE=$(basename "$FILE" | sed 's/\.[^.]*$//')
    LANG_TAG=$(echo "$LANG" | tr '[:upper:]' '[:lower:]')
    OUT="$DIR/${BASE}-grace-${LANG_TAG}.wav"
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
