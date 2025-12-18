#!/bin/bash
# ADD-ARTWORK.SH — Embed YouTube thumbnails into existing MP3s
# "No blank faces in the Electric Jungle"

MUSIC_DIR="./music/sunrise-chain"

echo "🐅 ELECTRIC JUNGLE — ARTWORK EMBEDDER"
echo "════════════════════════════════════════"
echo ""

# Function to re-download a track with embedded thumbnail
embed_art() {
    local file="$1"
    local basename=$(basename "$file" .mp3)
    local dirname=$(dirname "$file")
    local search_term="$basename"

    echo "🎨 Processing: $basename"

    # Re-download with thumbnail
    yt-dlp -x --audio-format mp3 --audio-quality 0 --embed-thumbnail \
        -o "${dirname}/${basename}.%(ext)s" \
        "ytsearch1:${search_term}" --no-playlist 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "   ✅ Artwork embedded!"
    else
        echo "   ⚠️  Could not embed (using existing)"
    fi
}

# Process all MP3s or specific ones
if [ "$1" == "--all" ]; then
    echo "Processing ALL tracks (this will take a while)..."
    find "$MUSIC_DIR" -name "*.mp3" | while read file; do
        embed_art "$file"
        sleep 1  # Be nice to YouTube
    done
elif [ -n "$1" ]; then
    embed_art "$1"
else
    echo "Usage:"
    echo "  ./add-artwork.sh --all           # Process all tracks"
    echo "  ./add-artwork.sh 'path/to/file.mp3'  # Process one track"
    echo ""
    echo "Example:"
    echo "  ./add-artwork.sh 'music/sunrise-chain/soul-foundation/Aretha Franklin - Respect.mp3'"
fi

echo ""
echo "🔄 Don't forget to restart the player:"
echo "   docker compose -f media-stack.yml restart swingmusic"
echo ""
echo "🐅 The Electric Jungle has faces now!"
