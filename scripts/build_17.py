#!/usr/bin/env python3
"""Born Once #17 — "The Snag" (Season 3). App frames (the BEFORE Transaction History,
no export) with red caption bars + Bauhaus-on-noir title cards, crossfaded on the
VO17_final beat map (Whisper), Brotherhood Run at 5%. Mirrors build_cream03_v2 + build_14."""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/angel/repos/helixnet"
PROJ = f"{ROOT}/videos/banco/Season 3 - Never Alone/born-once-17-the-brain-sorts-it"
SHOTS = f"{PROJ}/assets/shots"
SLIDES = f"{PROJ}/assets/slides"
VO = f"{PROJ}/VO17_final.wav"
MUSIC = f"{ROOT}/compose/helix-media/music/angel-originals/Brotherhood Run.mp3"
OUT = f"{PROJ}/Banco-BornOnce-17-The-Brain-DRAFT.mp4"
os.makedirs(SLIDES, exist_ok=True)

W, H = 1080, 1920
BANCO = (139, 0, 0); CARDBG = (12, 14, 18); INK = (243, 244, 246); MUTED = (156, 163, 175)
B_RED = (213, 43, 30); B_BLUE = (0, 78, 168); B_YEL = (247, 201, 40); B_WHT = (235, 235, 230)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
T = 0.6

# id, type, frame, text, window(s) — aligned to VO17_final beat map (Whisper segments)
TL = [
    ("s01", "card", None,                "He hit send.\nThen what?",                   5.70),
    ("s02", "app",  "ck-01-cockpit-top", "His words — buried\nin machine gibberish.", 10.96),
    ("s03", "card", None,                "A human reads it all.\nAnd sighs.",          8.28),
    ("s04", "card", None,                "Twenty minutes,\nby hand.",                  6.10),
    ("s05", "card", None,                "Banco does it\nin seconds.",                 9.44),
    ("s06", "app",  "ck-03-clean",       "The mess becomes\na clean ticket.",          5.92),
    ("s07", "app",  "ck-03-clean",       "It understood it —\nfeature, not a bug.",    7.86),
    ("s08", "app",  "ck-03-clean",       "The right screen.\n96% sure.",               7.40),
    ("s09", "card", None,                "It never changes\nwhat he wrote.",           6.16),
    ("s10", "card", None,                "The raw sits next\nto the clean.",           5.36),
    ("s11", "card", None,                "It translates. No words\nput in his mouth.", 8.34),
    ("s12", "app",  "ck-04-scorecard",   "He never has to\nspeak robot.",              7.48),
    ("s13", "app",  "ck-04-scorecard",   "One clean board.\nAll sorted.",              6.50),
    ("s14", "card", None,                "The mess\nbecame a map.",                    4.22),
    ("s15", "card", None,                "Now — how fast\ncan it heal?",               7.82),
    ("s16", "outro", None,               "#17 · The Brain Sorts It",                   3.46),
]


def font(p, s): return ImageFont.truetype(p, s)


def wrap(d, text, fnt, maxw):
    out = []
    for para in text.split("\n"):
        if not para:
            out.append(""); continue
        line = ""
        for w in para.split(" "):
            t = (line + " " + w).strip()
            if d.textlength(t, font=fnt) <= maxw: line = t
            else:
                if line: out.append(line)
                line = w
        if line: out.append(line)
    return out


def block(d, lines, fnt, cx, cy, fill, lh):
    y = cy - lh * len(lines) / 2 + lh / 2
    for ln in lines:
        d.text((cx, y), ln, font=fnt, fill=fill, anchor="mm"); y += lh


def brand(d):
    d.text((40, H - 50), "BORN ONCE", font=font(FB, 26), fill=(255, 255, 255), anchor="lm")
    d.text((262, H - 50), "·  #17  ·  Banco", font=font(FR, 26), fill=MUTED, anchor="lm")


def bauhaus(d, idx):
    t = idx % 6
    if t == 0:
        d.ellipse([120, 190, 360, 430], fill=B_BLUE); d.rectangle([620, 210, 940, 300], fill=B_RED)
    elif t == 1:
        d.rectangle([700, 180, 940, 420], fill=B_YEL); d.line([120, 600, 520, 200], fill=B_WHT, width=10)
    elif t == 2:
        d.ellipse([430, 170, 650, 390], fill=B_RED); d.rectangle([150, 470, 470, 560], fill=B_BLUE)
    elif t == 3:
        d.polygon([(150, 600), (340, 200), (530, 600)], fill=B_YEL); d.rectangle([640, 250, 940, 340], fill=B_RED)
    elif t == 4:
        d.ellipse([680, 200, 900, 420], fill=B_BLUE); d.line([140, 240, 560, 240], fill=B_RED, width=14)
    else:
        d.rectangle([150, 200, 420, 470], fill=B_RED); d.ellipse([600, 360, 760, 520], fill=B_YEL)


def make_app(frame, text, dst):
    img = Image.open(f"{SHOTS}/{frame}.png").convert("RGB")
    if img.size != (W, H): img = img.resize((W, H))
    d = ImageDraw.Draw(img, "RGBA")
    barh = 250
    d.rectangle([0, 0, W, barh], fill=BANCO + (255,)); d.rectangle([0, barh, W, barh + 5], fill=(0, 0, 0, 90))
    f = font(FB, 60); lines = wrap(d, text, f, W - 110)
    while len(lines) > 3 and f.size > 40: f = font(FB, f.size - 4); lines = wrap(d, text, f, W - 110)
    block(d, lines, f, W // 2, barh // 2, (255, 255, 255), f.size + 16)
    d.rectangle([0, H - 86, W, H], fill=(0, 0, 0, 150)); brand(d); img.save(dst)


def make_card(idx, text, dst):
    img = Image.new("RGB", (W, H), CARDBG); d = ImageDraw.Draw(img, "RGBA")
    bauhaus(d, idx)
    f = font(FB, 84); lines = wrap(d, text, f, W - 170)
    while len(lines) > 4 and f.size > 52: f = font(FB, f.size - 4); lines = wrap(d, text, f, W - 170)
    block(d, lines, f, W // 2, H // 2 + 110, INK, f.size + 28)
    brand(d); img.save(dst)


def make_outro(text, dst):
    img = Image.new("RGB", (W, H), CARDBG); d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([130, 200, 330, 400], fill=B_BLUE); d.rectangle([440, 220, 640, 380], fill=B_RED)
    d.polygon([(740, 400), (840, 200), (940, 400)], fill=B_YEL)
    d.text((W // 2, H // 2 - 110), "BORN", font=font(FB, 150), fill=INK, anchor="mm")
    d.text((W // 2, H // 2 + 70), "ONCE", font=font(FB, 150), fill=(252, 165, 165), anchor="mm")
    d.text((W // 2, H // 2 + 240), text, font=font(FR, 50), fill=MUTED, anchor="mm")
    brand(d); img.save(dst)


paths, durs = [], []
for i, (key, typ, frame, text, win) in enumerate(TL):
    dst = f"{SLIDES}/{i:02d}_{key}.png"
    if typ == "app": make_app(frame, text, dst)
    elif typ == "outro": make_outro(text, dst)
    else: make_card(i, text, dst)
    paths.append(dst); durs.append(win + T)

total = sum(durs) - (len(durs) - 1) * T
print(f"{len(paths)} slides, total {total:.1f}s (VO≈108.6s)")
cmd = ["ffmpeg", "-y", "-loglevel", "error"]
for p, dur in zip(paths, durs): cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", p]
cmd += ["-i", VO, "-i", MUSIC]
fc = [f"[{i}:v]format=yuv420p,setsar=1[v{i}]" for i in range(len(paths))]
prev, L = "v0", durs[0]
for i in range(1, len(paths)):
    fc.append(f"[{prev}][v{i}]xfade=transition=fade:duration={T}:offset={L - T:.3f}[x{i}]"); prev = f"x{i}"; L += durs[i] - T
fc.append(f"[{prev}]fade=t=in:st=0:d=0.5,fade=t=out:st={total - 1.2:.3f}:d=1.2[vout]")
na, nm = len(paths), len(paths) + 1
fc.append(f"[{na}:a]apad=whole_dur={total:.3f},atrim=0:{total:.3f}[vo]")
fc.append(f"[{nm}:a]volume=0.05,atrim=0:{total:.3f},asetpts=N/SR/TB,afade=t=out:st={total - 3:.3f}:d=3[mus]")
fc.append("[vo][mus]amix=inputs=2:normalize=0:duration=first[aout]")
cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT]
print("rendering...")
subprocess.run(cmd, check=True)
print("DONE ->", OUT)
