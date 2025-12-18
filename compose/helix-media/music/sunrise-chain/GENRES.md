# THE SUNRISE CHAIN — GENRE MAP

> "No secrets. No hidden algorithms. Just music, organized with love."

---

## THE PHILOSOPHY

```
SOURCE (Pure Gold)     →  The original recordings. The truth.
                          Dylan's voice. Aretha's power. The moment it happened.

REMIXES (Platinum)     →  The bridge. Makes old songs dance for new ears.
                          Pam at the register doesn't know Dylan,
                          but she'll move her hips to a Jolene remix.

BOTH MATTER.           →  Source feeds the soul. Remix feeds the dance floor.
                          We serve BOTH because music is for EVERYONE.
```

---

## FOLDER STRUCTURE

```
/sunrise-chain/
│
├── /soul-foundation/      ← THE BEDROCK (American soul, blues, civil rights anthems)
│   Sam Cooke, Aretha, Dylan, Marvin Gaye, Nina Simone, Ray Charles,
│   Stevie Wonder, Billie Holiday, Tracy Chapman, Otis Redding
│
├── /europe-west/          ← BRITISH INVASION + ROCK GODS
│   Beatles, Stones, Pink Floyd, Led Zeppelin, Queen, The Who,
│   Bowie, Hendrix, Cream, Clash, Radiohead, Deep Purple, Sabbath
│
├── /europe-east/          ← CONTINENTAL SOUL
│   Edith Piaf (France), Daft Punk (France), Viktor Tsoi (Russia)
│
├── /americas-west/        ← CALIFORNIA DREAMS + PACIFIC ROCK
│   Eagles, Fleetwood Mac, Doors, Nirvana, Prince, CCR, GNR
│
├── /americas-east/        ← LATIN SOUL + CARIBBEAN FIRE
│   Jobim (Brazil), Santana, Bob Marley (Jamaica),
│   Buena Vista Social Club (Cuba), Mercedes Sosa (Argentina),
│   Simon & Garfunkel, Talking Heads
│
├── /japan-korea/          ← CITY POP + ANIME + ELECTRONIC PIONEERS
│   Tatsuro Yamashita, Mariya Takeuchi, Nujabes, Joe Hisaishi,
│   Yellow Magic Orchestra, Ryuichi Sakamoto
│
├── /australia/            ← SUNBURNT ROCK
│   INXS, Midnight Oil, AC/DC
│
├── /africa-west/          ← MAMA AFRICA + AFROBEAT
│   Miriam Makeba, Hugh Masekela, Fela Kuti
│
├── /africa-east/          ← ETHIOPIAN JAZZ
│   Mulatu Astatke
│
├── /india-pakistan/       ← SUFI SOUL + BOLLYWOOD
│   Nusrat Fateh Ali Khan, A.R. Rahman
│
├── /middle-east/          ← THE VOICE OF LEBANON
│   Fairuz
│
├── /southeast-asia/       ← MANILA SOUND + BEYOND
│   Eraserheads (Philippines)
│
├── /pacific-dawn/         ← WHERE THE SUN RISES FIRST
│   Israel Kamakawiwo'ole (Hawaii)
│
└── /remixes-platinum/     ← THE DANCE FLOOR (bridges old to new)
    Dolly Parton (slowed), Tina Turner, Grace Jones,
    Donna Summer, Bee Gees, MJ, Whitney, Earth Wind & Fire,
    Chic, Gloria Gaynor, Sister Sledge, Blondie, Cyndi Lauper,
    The Who remix, Fleetwood Mac remix
```

---

## WORKFLOW: How to Add Music

### Adding SOURCE (Original Recordings)

```bash
# 1. Find the song on YouTube
# 2. Download to the right regional folder
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "music/sunrise-chain/[REGION]/Artist - Song.%(ext)s" \
  "ytsearch1:Artist Song Year" --no-playlist

# Example: Adding a new soul track
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "music/sunrise-chain/soul-foundation/Al Green - Lets Stay Together.%(ext)s" \
  "ytsearch1:Al Green Let's Stay Together 1972" --no-playlist
```

### Adding REMIXES

```bash
# Same process, but goes to remixes-platinum
yt-dlp -x --audio-format mp3 --audio-quality 0 \
  -o "music/sunrise-chain/remixes-platinum/Artist - Song (Remix).%(ext)s" \
  "ytsearch1:Artist Song remix" --no-playlist
```

### Adding LYRICS (.lrc files)

```bash
# Create a .lrc file with same name as .mp3
# Format:
[ti:Song Title]
[ar:Artist Name]
[00:00.00]First line of lyrics
[00:05.00]Second line...
```

### Restart Player to Index New Music

```bash
docker compose -f media-stack.yml restart swingmusic
```

---

## THE RULES

1. **SOURCE goes to regional folders** — Organized by where the artist/sound originated
2. **REMIXES go to /remixes-platinum/** — One folder, all the dance versions
3. **No DRM, no ads, no algorithms** — Just files on disk
4. **Lyrics are optional but encouraged** — .lrc files help people learn
5. **MANIFEST.md tells the stories** — Update it when you add significant tracks
6. **WISDOM.md for quotes** — Music philosophy between the songs

---

## WHO IS THIS FOR?

| Audience | What They Want | Where to Start |
|----------|----------------|----------------|
| **Elders** (us) | The source, the story | /soul-foundation/, /europe-west/ |
| **Dancers** | Rhythm, energy | /remixes-platinum/ |
| **Learners** | English practice | Any track with .lrc lyrics |
| **The CTO** | Just make it work | `docker compose up -d` |
| **Pam** | Music while working | Shuffle everything |

---

## SUGGESTED PLAYLISTS (by Mood)

### "Monday Morning Coffee"
- Sam Cooke - A Change Is Gonna Come
- Nina Simone - Feeling Good
- Beatles - Here Comes the Sun
- Israel Kamakawiwo'ole - Over the Rainbow

### "Friday Dance Party" (for Pam)
- Earth Wind & Fire - September
- Whitney Houston - I Wanna Dance
- Bee Gees - Stayin Alive
- Sister Sledge - We Are Family
- Cyndi Lauper - Girls Just Wanna Have Fun

### "Deep Focus Coding"
- Nujabes - Feather
- Ryuichi Sakamoto - Merry Christmas Mr Lawrence
- Joe Hisaishi - Merry Go Round of Life
- Pink Floyd - Wish You Were Here

### "Revolution Radio"
- Bob Dylan - Like a Rolling Stone
- The Clash - London Calling
- Marvin Gaye - What's Going On
- Bob Marley - Redemption Song
- Viktor Tsoi - Gruppa Krovi

---

*No secrets. No algorithms. Just music.*

🐅 ROAR.
