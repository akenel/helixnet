# The recipe catalog — and why 3-4 warm services cover ~90%

When you sort the recipes by the *tool* they actually need, a beautiful thing falls
out: nearly all of them are just different **wirings of the same handful of CPU
services**. Keep those services warm, and you can run almost everything — no GPU.

---

## The warm services (the "images")

These run on a plain CPU machine — a 16GB laptop, a small server. Keep them warm;
the recipe just feeds them a job.

| # | Service | Tool | Does |
|---|---------|------|------|
| **A** | **Voice** | Piper | text → spoken audio (CPU, ~2s) |
| **B** | **Render** | Puppeteer / Chrome | HTML → image, PDF, or video frames |
| **C** | **Media** | ffmpeg | combine audio + visuals → video; waveforms; captions; Ken Burns |
| **D** | **Transcribe** *(optional)* | Whisper | audio/video → timed text (for captions) |

**A + B + C = the core.** D adds captions/subtitles. That's it — three or four
always-on services behind everything below.

---

## CPU recipes (Version 1 — prove it, ship it, no GPU)

Each recipe is just a wiring of the services above:

| Recipe | Wires | What you get |
|--------|-------|--------------|
| Voiceover Reel | A → C | narrated audiogram video |
| Audiogram | A → C | waveform clip for podcasts |
| Pronounce-It (IT/EN) | A → C | language flashcard video |
| Quote / Meme Card | B | a branded image |
| Postcard / Print Kit | B | print-ready PDF (your UFA pipeline) |
| Menu / Flyer | B | styled A4 PDF |
| QR-on-a-card | B | branded Google-Maps QR card |
| 3D Text Spinner | B → C | spinning 3D-text logo (CSS 3D, no GPU) |
| This or That | B → C | countdown-reveal short |
| Stat Card | B → C | animated chart short |
| Photo-folder Reel | C | Ken Burns slideshow with music |
| Listicle / Countdown | A + B → C | narrated numbered-card video |
| Greeting Video | A + B → C | personalized birthday/occasion video |
| Karaoke Captions | D → C | any clip + animated word-pop subtitles |
| Lyric Video | D → C | bouncing-word lyric video |

**15 recipes. Three or four warm services. Zero GPUs.** That's the proof that a
creative person with a normal laptop can already do a lot.

---

## GPU recipes (Version 2 — later, on rented/donated machines)

These need real horsepower. They wait for v2 — and we **rent or borrow** the GPU,
we don't buy it (see hosting below):

- Stable Diffusion / FLUX images
- Image → 3D model (the 2D→3D print pipeline)
- AI video generation, upscaling, voice cloning, photo animation

The point: **you don't need a GPU for everything.** GPUs are for the heavy stuff.
Most of what people want is CPU work wired cleverly.

---

## Hosting plan — who runs the warm services

The honest, cheap, fair version:

### Version 1 (now) — CPU, hosted by us + run-it-yourself

- **Members who can, run it themselves.** A friend in India with a 16GB CPU machine
  enrolls it as a node and runs the warm services on their own box. No cost to us,
  full independence for them. This is the target audience: capable, low-budget,
  ready.
- **For everyone else, we host the warm services.** A small **dedicated** CPU box —
  ~$5/mo — runs A/B/C/D and covers 80-90% of CPU users.

> **Don't co-locate this with the Hetzner prod box.** Prod is already the pinch
> (it shares memory with staging + Keycloak), and a warm Chrome/Puppeteer alone eats
> hundreds of MB. Put the warm services on the **DigitalOcean box** or a small
> separate droplet/CX22 — keep compute away from prod. Five or six dollars buys
> isolation *and* covers most users. That's the fair trade.

### Version 2 (later) — GPU, rented or donated, never bought

- We do **not** buy hardware. (A box in the basement is a whole other nightmare:
  power, uptime, noise, depreciation.)
- The GPU comes from a **member who offers their idle machine for credits**:
  *"I've got a gaming PC I don't use 90% of the time — wire me up, I'll take credits."*
  That's the BYOH network doing exactly what it's for.
- A rented GPU-by-the-hour is a temporary stand-in only if no member GPU is online.

---

## How this maps to the worker

A node that keeps services **A + B + C (+ D)** warm can run every CPU recipe in the
catalog. When it enrolls, it advertises those tools; the broker matches jobs to it.
The recipe names which services it wires — the broker checks the node has them —
the job runs — the file comes back. Same loop we proved on the laptop today.
