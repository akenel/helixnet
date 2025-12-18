# LIVE RADIO STREAMS — The Endless Sunrise

> "When your local collection isn't enough, tune into the world."
> No ads. No algorithms. Just humans curating music with love.

---

## RECOMMENDED STATIONS (Free, No Ads, No Guilt)

### RADIO PARADISE — THE DEFAULT 🏆
**URL:** https://radioparadise.com/
**Streams:**
- Main Mix: `http://stream.radioparadise.com/aac-320`
- Mellow Mix: `http://stream.radioparadise.com/mellow-320`
- Rock Mix: `http://stream.radioparadise.com/rock-320`
- World/Eclectic: `http://stream.radioparadise.com/world-etc-320`

**Why Radio Paradise:**
- 100% listener-supported (no ads, ever)
- Human DJs, not algorithms
- Eclectic mix: classic rock to world music to electronica
- High quality streams (320kbps AAC)
- Founded by music lovers, run by music lovers
- Perfect for: Pam scrubbing floors, CTO pretending to work, Tigers dreaming

---

## MORE FREE STATIONS BY VIBE

### For the SOUL FOUNDATION mood
| Station | URL | Vibe |
|---------|-----|------|
| WFMU | https://wfmu.org | Freeform, unpredictable, legendary |
| KEXP | https://kexp.org | Seattle indie, world music |
| WWOZ | https://wwoz.org | New Orleans jazz, blues, soul |

### For the DANCE FLOOR (Pam's Floor Cleaning Playlist)
| Station | URL | Vibe |
|---------|-----|------|
| SomaFM Groove Salad | https://somafm.com/groovesalad/ | Chill electronic |
| SomaFM Secret Agent | https://somafm.com/secretagent/ | Spy music, lounge |
| SomaFM Underground 80s | https://somafm.com/u80s/ | 80s new wave, synthpop |

### For the DEEP FOCUS (Coding Sessions)
| Station | URL | Vibe |
|---------|-----|------|
| SomaFM Drone Zone | https://somafm.com/dronezone/ | Ambient, meditative |
| SomaFM Space Station | https://somafm.com/spacestation/ | Space music |
| Chillhop Radio | YouTube Live | Lo-fi hip hop beats |

### For the WORLD TOUR (Following the Sunrise)
| Station | Region | URL |
|---------|--------|-----|
| FIP (France) | Europe | https://www.fip.fr |
| NTS Radio | London | https://nts.live |
| Worldwide FM | Global | https://worldwidefm.net |
| dublab | Los Angeles | https://dublab.com |

---

## HOW TO PLAY RADIO IN HELIX

### Option 1: VLC (command line)
```bash
# Play Radio Paradise main mix
vlc http://stream.radioparadise.com/aac-320

# Play SomaFM Groove Salad
vlc https://ice4.somafm.com/groovesalad-320-mp3
```

### Option 2: Add to Swing Music (Future Feature)
```yaml
# In media-stack.yml, we could add a radio player
# This is a DREAM for now
```

### Option 3: Browser
Just go to https://radioparadise.com and hit play

---

## THE VISION: LLM-POWERED PLAYLIST GENERATION

```
┌─────────────────────────────────────────────────────────────┐
│                    PAM'S PLAYLIST GENERATOR                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pam: "I need music for cleaning the store"                 │
│                                                             │
│  LLM: "What kind of energy?"                                │
│       [ ] Chill & Easy                                      │
│       [x] Upbeat & Moving                                   │
│       [ ] Focus & Flow                                      │
│                                                             │
│  LLM: "How long?"                                           │
│       ( ) 30 minutes                                        │
│       (x) 60 minutes                                        │
│       ( ) 2 hours                                           │
│                                                             │
│  LLM: "Any artists you love?"                               │
│       [Whitney Houston, anything 80s]                       │
│                                                             │
│  [GENERATE PLAYLIST]                                        │
│                                                             │
│  ═══════════════════════════════════════════════════════   │
│  🎵 PAM'S FLOOR CLEANING MIX (58 min)                       │
│  ═══════════════════════════════════════════════════════   │
│  1. Whitney Houston - I Wanna Dance (4:52)                  │
│  2. Earth Wind & Fire - September (3:35)                    │
│  3. Sister Sledge - We Are Family (3:22)                    │
│  4. Cyndi Lauper - Girls Just Wanna Have Fun (3:58)         │
│  5. Bee Gees - Stayin Alive (4:45)                          │
│  6. Gloria Gaynor - I Will Survive (3:15)                   │
│  7. Michael Jackson - Billie Jean (4:54)                    │
│  8. Donna Summer - I Feel Love (5:53)                       │
│  9. Chic - Le Freak (5:23)                                  │
│  10. Blondie - Heart of Glass (4:15)                        │
│  11. Fleetwood Mac - Dreams Remix (3:45)                    │
│  12. Tina Turner - Satisfaction (4:32)                      │
│  + 2 surprise tracks from Soul Foundation...                │
│                                                             │
│  [PLAY NOW] [SAVE AS "Pam's Cleaning Mix"] [SHUFFLE]        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## MOOD TAGS (For Future LLM Integration)

Instead of traditional genres, we tag by FEELING:

| Tag | Description | Example Tracks |
|-----|-------------|----------------|
| `floor-scrubber` | High energy, keeps you moving | September, Stayin Alive |
| `shelf-duster` | Moderate tempo, easy groove | Dreams, Heart of Glass |
| `monday-coffee` | Gentle wake-up | Here Comes the Sun, Feeling Good |
| `friday-freedom` | Pure celebration | Girls Just Wanna, I Wanna Dance |
| `deep-focus` | Minimal lyrics, ambient | Nujabes, Sakamoto |
| `revolution` | Angry but hopeful | London Calling, Redemption Song |
| `heartbreak-hotel` | Sad but beautiful | Wish You Were Here, Fast Car |
| `sunday-soul` | Warm, spiritual | A Change Is Gonna Come, Imagine |

---

## THE DREAM ROADMAP

### Phase 1: NOW ✅
- [x] 83 tracks across 14 regions
- [x] Remixes Platinum folder
- [x] Synced lyrics (.lrc files)
- [x] MANIFEST.md (stories)
- [x] WISDOM.md (quotes)
- [x] GENRES.md (workflow)
- [x] RADIO.md (this file)

### Phase 2: SOON
- [ ] Album art for each track
- [ ] More .lrc lyrics files
- [ ] Radio Paradise integration in player
- [ ] Mood tags in filenames or metadata

### Phase 3: THE DREAM
- [ ] LLM playlist generator (Pam's scenario)
- [ ] Music videos folder
- [ ] Voice commands ("Hey Helix, play floor cleaning music")
- [ ] Auto-discover new tracks based on listening history
- [ ] Share playlists with other Helix users

---

## NO ADS. NO ALGORITHMS. NO GUILT.

Last.fm wants money.
Spotify wants $11/month.
YouTube wants your attention.

We want NOTHING except for you to enjoy the music.

Radio Paradise runs on donations because the founders believe music should be free.
We run on the same belief.

> "The best things in life are free. The sunrise. The air. The music."
> — Electric Jungle

---

*Tune in. Turn up. Dance free.*

🐅📻🎵
