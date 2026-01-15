#!/bin/bash
# =============================================================================
# 🎸 HELIX TUNE GRABBER v2 — TRAPANI NIGHTS EDITION 🌅
# =============================================================================
# "Be water, my friend." — Bruce Lee 🐉
# Built: Jan 14, 2026 — Trapani, Sicily
# =============================================================================

MUSIC_DIR="./music/sunrise-chain"
ROCK_DIR="$MUSIC_DIR/europe-west"
SOUL_DIR="$MUSIC_DIR/soul-foundation"
CANADA_DIR="$MUSIC_DIR/americas-east"

# Create dirs if needed
mkdir -p "$ROCK_DIR" "$SOUL_DIR" "$CANADA_DIR"

echo ""
echo "🎸 ═══════════════════════════════════════════════════════════════"
echo "   HELIX TUNE GRABBER v2 — Trapani Nights Edition 🦁"
echo "   Classic Rock + Canadian Legends"
echo "═══════════════════════════════════════════════════════════════ 🎸"
echo ""

# =============================================================================
# 🔥 CLASSIC ROCK ESSENTIALS
# =============================================================================

echo "🔥 CLASSIC ROCK ESSENTIALS"
echo "──────────────────────────────────────────────────────────────────"

echo "🎤 [1/20] AC/DC — Back in Black..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/AC-DC - Back in Black.%(ext)s" \
  "ytsearch1:AC/DC Back in Black official audio" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [2/20] Rolling Stones — Sympathy for the Devil..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Rolling Stones - Sympathy for the Devil.%(ext)s" \
  "ytsearch1:Rolling Stones Sympathy for the Devil original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [3/20] Led Zeppelin — Whole Lotta Love..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Led Zeppelin - Whole Lotta Love.%(ext)s" \
  "ytsearch1:Led Zeppelin Whole Lotta Love" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [4/20] Queen — Bohemian Rhapsody..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Queen - Bohemian Rhapsody.%(ext)s" \
  "ytsearch1:Queen Bohemian Rhapsody official video" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [5/20] The Who — Baba O'Riley..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/The Who - Baba ORiley.%(ext)s" \
  "ytsearch1:The Who Baba O'Riley teenage wasteland" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [6/20] Deep Purple — Smoke on the Water..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Deep Purple - Smoke on the Water.%(ext)s" \
  "ytsearch1:Deep Purple Smoke on the Water original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [7/20] Eagles — Hotel California..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Eagles - Hotel California.%(ext)s" \
  "ytsearch1:Eagles Hotel California original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [8/20] Fleetwood Mac — The Chain..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Fleetwood Mac - The Chain.%(ext)s" \
  "ytsearch1:Fleetwood Mac The Chain" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [9/20] Dire Straits — Sultans of Swing..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Dire Straits - Sultans of Swing.%(ext)s" \
  "ytsearch1:Dire Straits Sultans of Swing original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [10/20] CCR — Fortunate Son..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/CCR - Fortunate Son.%(ext)s" \
  "ytsearch1:Creedence Clearwater Revival Fortunate Son" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [11/20] ZZ Top — La Grange..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/ZZ Top - La Grange.%(ext)s" \
  "ytsearch1:ZZ Top La Grange" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [12/20] Free — All Right Now..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$ROCK_DIR/Free - All Right Now.%(ext)s" \
  "ytsearch1:Free All Right Now original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

# =============================================================================
# 🍁 CANADIAN LEGENDS
# =============================================================================

echo ""
echo "🍁 CANADIAN LEGENDS"
echo "──────────────────────────────────────────────────────────────────"

echo "🎤 [13/20] Tragically Hip — Bobcaygeon..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$CANADA_DIR/Tragically Hip - Bobcaygeon.%(ext)s" \
  "ytsearch1:Tragically Hip Bobcaygeon" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [14/20] Tragically Hip — Ahead by a Century..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$CANADA_DIR/Tragically Hip - Ahead by a Century.%(ext)s" \
  "ytsearch1:Tragically Hip Ahead by a Century" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [15/20] Tragically Hip — New Orleans Is Sinking..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$CANADA_DIR/Tragically Hip - New Orleans Is Sinking.%(ext)s" \
  "ytsearch1:Tragically Hip New Orleans Is Sinking" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [16/20] Sam Roberts — Brother Down..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$CANADA_DIR/Sam Roberts - Brother Down.%(ext)s" \
  "ytsearch1:Sam Roberts Brother Down" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [17/20] Sam Roberts — Hard Road..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$CANADA_DIR/Sam Roberts - Hard Road.%(ext)s" \
  "ytsearch1:Sam Roberts Hard Road" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [18/20] Neil Young — Heart of Gold..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$CANADA_DIR/Neil Young - Heart of Gold.%(ext)s" \
  "ytsearch1:Neil Young Heart of Gold original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [19/20] Rush — Tom Sawyer..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$CANADA_DIR/Rush - Tom Sawyer.%(ext)s" \
  "ytsearch1:Rush Tom Sawyer official" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo "🎤 [20/20] The Guess Who — American Woman..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "$CANADA_DIR/The Guess Who - American Woman.%(ext)s" \
  "ytsearch1:The Guess Who American Woman original" \
  --no-playlist --quiet --progress 2>/dev/null && echo "   ✅ Got it!" || echo "   ⚠️ Skip"

echo ""
echo "🎸 ═══════════════════════════════════════════════════════════════"
echo "   DONE! 20 tracks queued for the Sunrise Chain"
echo ""
echo "   Restart Swing Music to index:"
echo "   docker restart helix-music"
echo ""
echo "   Then open: http://music.helix.local:1970"
echo "═══════════════════════════════════════════════════════════════ 🎸"
echo ""
echo "🍁 From Trapani with love — Jan 14, 2026"
echo "🐉 Be water, my friend. — Bruce Lee"
echo ""
