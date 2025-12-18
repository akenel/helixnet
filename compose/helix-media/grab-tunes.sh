#!/bin/bash
# =============================================================================
# 🎸 HELIX TUNE GRABBER — THE SUNRISE CHAIN 🌅
# =============================================================================
# "Be water, my friend." — Bruce Lee 🐉
# =============================================================================

MUSIC_DIR="./music/sunrise-chain"
SOUL_DIR="$MUSIC_DIR/soul-foundation"
ROCK_DIR="$MUSIC_DIR/europe-west"

# Create dirs if needed
mkdir -p "$SOUL_DIR" "$ROCK_DIR"

echo ""
echo "🎸 ═══════════════════════════════════════════════════════════════"
echo "   HELIX TUNE GRABBER — Let's Rock! 🦁"
echo "═══════════════════════════════════════════════════════════════ 🎸"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 🎵 THE HOLLIES — Long Cool Woman in a Black Dress (1972)
# ─────────────────────────────────────────────────────────────────────────────
echo "🎤 [1/8] The Hollies — Long Cool Woman in a Black Dress..."
yt-dlp --js-runtimes node -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/The Hollies - Long Cool Woman.%(ext)s" \
  "ytsearch1:The Hollies Long Cool Woman in a Black Dress official" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Will retry"

# ─────────────────────────────────────────────────────────────────────────────
# 🎵 BOB DYLAN — Like a Rolling Stone (1965)
# ─────────────────────────────────────────────────────────────────────────────
echo "🎤 [2/8] Bob Dylan — Like a Rolling Stone..."
yt-dlp --js-runtimes node -x --audio-format mp3 --audio-quality 0 \
  -o "$SOUL_DIR/Bob Dylan - Like a Rolling Stone.%(ext)s" \
  "ytsearch1:Bob Dylan Like a Rolling Stone original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Will retry"

# ─────────────────────────────────────────────────────────────────────────────
# 🎵 BOB DYLAN — Blowin' in the Wind (1963)
# ─────────────────────────────────────────────────────────────────────────────
echo "🎤 [3/8] Bob Dylan — Blowin' in the Wind..."
yt-dlp --js-runtimes node -x --audio-format mp3 --audio-quality 0 \
  -o "$SOUL_DIR/Bob Dylan - Blowin in the Wind.%(ext)s" \
  "ytsearch1:Bob Dylan Blowin in the Wind original 1963" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Will retry"

# ─────────────────────────────────────────────────────────────────────────────
# 🎵 PINK FLOYD — Wish You Were Here (1975)
# ─────────────────────────────────────────────────────────────────────────────
echo "🎤 [4/8] Pink Floyd — Wish You Were Here..."
yt-dlp --js-runtimes node -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Pink Floyd - Wish You Were Here.%(ext)s" \
  "ytsearch1:Pink Floyd Wish You Were Here original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Will retry"

# ─────────────────────────────────────────────────────────────────────────────
# 🎵 PINK FLOYD — Another Brick in the Wall Part 2 (1979)
# ─────────────────────────────────────────────────────────────────────────────
echo "🎤 [5/8] Pink Floyd — Another Brick in the Wall..."
yt-dlp --js-runtimes node -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Pink Floyd - Another Brick in the Wall.%(ext)s" \
  "ytsearch1:Pink Floyd Another Brick in the Wall Part 2" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Will retry"

# =============================================================================
# 🦁 LEO'S PICKS — The Tiger's Favorites
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# 🎵 CREAM — Sunshine of Your Love (1967) — Leo loves that riff 🎸
# ─────────────────────────────────────────────────────────────────────────────
echo "🦁 [6/8] Cream — Sunshine of Your Love (Leo's Pick #1)..."
yt-dlp --js-runtimes node -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Cream - Sunshine of Your Love.%(ext)s" \
  "ytsearch1:Cream Sunshine of Your Love original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Will retry"

# ─────────────────────────────────────────────────────────────────────────────
# 🎵 JIMI HENDRIX — All Along the Watchtower (1968) — Pure fire 🔥
# ─────────────────────────────────────────────────────────────────────────────
echo "🦁 [7/8] Jimi Hendrix — All Along the Watchtower (Leo's Pick #2)..."
yt-dlp --js-runtimes node -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Jimi Hendrix - All Along the Watchtower.%(ext)s" \
  "ytsearch1:Jimi Hendrix All Along the Watchtower original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Will retry"

# ─────────────────────────────────────────────────────────────────────────────
# 🎵 SAM COOKE — A Change Is Gonna Come (1964) — The soul foundation 🎷
# ─────────────────────────────────────────────────────────────────────────────
echo "🦁 [8/8] Sam Cooke — A Change Is Gonna Come (The Foundation)..."
yt-dlp --js-runtimes node -x --audio-format mp3 --audio-quality 0 \
  -o "$SOUL_DIR/Sam Cooke - A Change Is Gonna Come.%(ext)s" \
  "ytsearch1:Sam Cooke A Change Is Gonna Come original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Will retry"

echo ""
echo "🎸 ═══════════════════════════════════════════════════════════════"
echo "   DONE! Now restart Swing Music to index the new tracks:"
echo ""
echo "   docker restart helix-music"
echo ""
echo "   Then open: http://music.helix.local:1970"
echo "═══════════════════════════════════════════════════════════════ 🎸"
echo ""
echo "🐉 Be water, my friend. — Bruce Lee"
echo "🦁 No ads. No algorithm. Just music. — Leo the Lion"
echo ""
