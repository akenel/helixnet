# 🎸 HELIX MEDIA PLAYER — THE SUNRISE CHAIN 🌅

> "Because music without ads is music with soul." — Leo the Lion 🦁

## 🐉 WHY THIS EXISTS

**The Problem:**
- Spotify: $12/month just to remove ads = $144/year ransom
- YouTube: Ads in the middle of songs, constant upselling
- SoundCloud: Ads every 2-3 songs, account can vanish overnight
- All platforms: Algorithm decides what you hear, not you

**The Solution:**
- **Helix Media Player**: Self-hosted, ad-free, YOURS forever
- Download once, own forever
- No monthly ransom to corporations
- Music the way it should be

## 👥 WHO IS THIS FOR

| User | Why They Need This |
|------|-------------------|
| 🏪 Shop owners | 8 hours of uninterrupted background music |
| 🌍 Global citizens | $12/month is a day's wage in many countries |
| 🦁 Freedom seekers | Refuse to be the product |
| 🔧 Builders | Rather spend 4 hours building than pay forever |

## 🚀 QUICK START

```bash
cd compose/helix-media

# Pull and run
docker compose -f media-stack.yml up -d

# Check it's running
docker ps | grep helix-music

# Open in browser
open http://localhost:1970
```

## 📁 FOLDER STRUCTURE

```
compose/helix-media/
├── media-stack.yml          # Docker Compose config
├── README.md                # You are here
├── config/                  # Swing Music settings (auto-created)
└── music/                   # YOUR MUSIC LIBRARY
    └── sunrise-chain/       # The Sunrise Chain playlists
        ├── pacific-dawn/        🇳🇿 First sunrise on Earth
        ├── australia/           🇦🇺 Down Under
        ├── japan-korea/         🇯🇵 Land of the Rising Sun
        ├── southeast-asia/      🇮🇩 Indonesia, Philippines
        ├── india-pakistan/      🇮🇳 Subcontinent
        ├── middle-east/         🇪🇬 Ancient lands
        ├── africa-east/         🇰🇪 Kenya, Ethiopia
        ├── africa-west/         🇳🇬 Nigeria, Senegal, Mali
        ├── europe-east/         🇬🇷 Balkans, Greece
        ├── europe-west/         🇫🇷 France, Spain, UK
        ├── americas-east/       🇧🇷 Brazil, Argentina
        ├── americas-west/       🇨🇦 Mexico, West Coast
        └── soul-foundation/     🎷 Blues, Gospel, Soul
```

## 🎵 ADDING MUSIC

### Option 1: Manual (Simple)
Drop MP3/FLAC files into the regional folders. Swing Music auto-indexes.

### Option 2: yt-dlp (From YouTube)
```bash
# Install yt-dlp
pip install yt-dlp

# Download a song (audio only, best quality)
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "music/sunrise-chain/japan-korea/%(title)s.%(ext)s" \
  "https://youtube.com/watch?v=VIDEO_ID"

# Download a playlist
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "music/sunrise-chain/africa-west/%(title)s.%(ext)s" \
  "https://youtube.com/playlist?list=PLAYLIST_ID"
```

### Option 3: Batch Download Script (Coming Soon)
```bash
# From the LIONS-ROAR-PLAYLIST.md song list
./scripts/download-sunrise-chain.sh
```

## 🌅 THE SUNRISE CHAIN CONCEPT

The playlist follows the sunrise around the globe:

```
TIME    ZONE              SUNRISE
────────────────────────────────────
05:00   Pacific Dawn      🇳🇿 First light hits Earth
06:00   Australia         🇦🇺 Down Under wakes
07:00   Japan-Korea       🇯🇵 Rising Sun
08:00   Southeast Asia    🇮🇩 Archipelago stirs
09:00   India-Pakistan    🇮🇳 Subcontinent awakens
10:00   Middle East       🇪🇬 Ancient lands
11:00   Africa East       🇰🇪 Safari morning
12:00   Africa West       🇳🇬 Afrobeat noon
13:00   Europe East       🇬🇷 Mediterranean sun
14:00   Europe West       🇫🇷 Celtic afternoon
15:00   Americas East     🇧🇷 Samba time
16:00   Americas West     🇨🇦 Your timezone (Ontario)
17:00   Pacific Islands   🌴 Loop closes
```

**April 1st, 2026**: The goal is 1000 songs, all regions, one global sunrise.

## ⚙️ CONFIGURATION

### With Traefik (Full Helix Stack)
Uncomment the Traefik labels in `media-stack.yml`:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.music.rule=Host(`music.helix.local`)"
```

Then access at: `https://music.helix.local`

### Standalone
Just use: `http://localhost:1970`

## 📊 STORAGE REQUIREMENTS

| Songs | Estimated Size |
|-------|---------------|
| 100   | ~500 MB |
| 448   | ~2.5 GB |
| 1000  | ~5 GB |

**That's it.** A USB stick can hold the entire Sunrise Chain.

## 🔗 RELATED DOCS

- `/docs/LIONS-ROAR-PLAYLIST.md` — The full 448 song list with metadata
- `/docs/Japan-SunRiseChain.txt` — Regional roadmap and comments
- `/docs/FREEDOM-STOP-NETWORK.md` — The bigger vision

## 🦁 PHILOSOPHY

```
Most people surrender. They pay $12/month.
They become the product. The algorithm decides.

But once this exists, it exists forever.
Clone the repo. Own your music. No ransom.

"Sing at sunrise. Be water." 🐉🎸
```

---

**Built with:** Swing Music (Python) + Docker + Love

**No ads. No algorithm. Just music.** 🌅

---

*Part of the HelixNet Freedom Stack*
*"Because you don't learn Keycloak in school."*
