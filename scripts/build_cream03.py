#!/usr/bin/env python3
"""Born Once #03 — The Forty-Franc Cream. Portrait Slideshow Explainer (Banco Method).

Source visuals: Angel's desktop OBS capture (app pane cropped to portrait). VO: 7 stitched
section takes (assets/vo-cream-tight.wav). Red card-bars over the chrome + dark title cards,
crossfaded on the VO beat map, Brotherhood Run bedded at 6%.
"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/angel/repos/helixnet"
PROJ = f"{ROOT}/videos/banco/born-once-03-forty-franc-cream"
FRAMES = f"{PROJ}/assets/frames"
SLIDES = f"{PROJ}/assets/slides"
VO = f"{PROJ}/assets/vo-cream-tight.wav"
MUSIC = f"{ROOT}/compose/helix-media/music/angel-originals/Brotherhood Run.mp3"
SRC = "/home/angel/Videos/OBS/OBS_2026-06-23 20-02-59.mp4"
OUT = f"{PROJ}/Banco-BornOnce-03-Forty-Franc-Cream-DRAFT.mp4"
CROP = "crop=580:1031:1180:44,scale=1080:1920"  # app pane -> portrait, exact 9:16
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(SLIDES, exist_ok=True)

W, H = 1080, 1920
BANCO = (139, 0, 0)
CARDBG = (12, 14, 18)
INK = (243, 244, 246)
MUTED = (156, 163, 175)
RED_ACCENT = (200, 40, 40)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
T = 0.6

# app frames to harvest from the OBS capture: name -> timestamp
GRAB = {"cream": 70, "home": 30, "find": 200, "cart": 235}

# id, type, frame, text, window(s)  — aligned to the VO beat map
TL = [
    ("s01", "app", "cream", "Half this shop has no barcode.",                       7.0),
    ("s02", "app", "home",  "A cream that costs forty francs.",                     7.36),
    ("s03", "app", "home",  "Saturday. The new kid's on the till.",                 5.9),
    ("s04", "app", "cream", "She reaches for the scanner. Nothing to scan.",        4.34),
    ("s05", "app", "cream", "Five tubes. Nearly identical.",                        7.36),
    ("s06", "card", None,   "One's 40. One's 12.\nGuess wrong — the drawer\nnever balances.", 10.48),
    ("s07", "card", None,   "The old way: a price\ntyped by hand.",                 6.68),
    ("s08", "card", None,   "A number to remember.\nOr call the manager. Again.",   6.46),
    ("s09", "card", None,   "Every unmarked item,\na gamble.",                      8.72),
    ("s10", "app", "find",  "She doesn't scan. She opens the catalogue.",           5.7),
    ("s11", "app", "cream", "There it is — wearing its own face.",                  5.82),
    ("s12", "app", "cart",  "She taps the picture. Right price, first try.",        10.48),
    ("s13", "app", "cream", "Born once — given a face.",                            7.12),
    ("s14", "app", "find",  "From now on, anyone sells it by sight.",               9.06),
    ("s15", "card", None,   "A barcode belongs\nto the factory.",                   7.7),
    ("s16", "card", None,   "A picture belongs\nto you.",                           7.66),
    ("s17", "card", None,   "Sell what\nyou can see.",                              5.3),
    ("s18", "outro", None,  "sell by sight.",                                       6.86),
]


def font(p, s):
    return ImageFont.truetype(p, s)


def wrap(draw, text, fnt, maxw):
    out = []
    for para in text.split("\n"):
        if not para:
            out.append(""); continue
        line = ""
        for w in para.split(" "):
            t = (line + " " + w).strip()
            if draw.textlength(t, font=fnt) <= maxw:
                line = t
            else:
                if line:
                    out.append(line)
                line = w
        if line:
            out.append(line)
    return out


def draw_block(draw, lines, fnt, cx, cy, fill, lh):
    y = cy - lh * len(lines) / 2 + lh / 2
    for ln in lines:
        draw.text((cx, y), ln, font=fnt, fill=fill, anchor="mm")
        y += lh


def brand(draw):
    draw.text((40, H - 50), "BORN ONCE", font=font(FB, 26), fill=(255, 255, 255), anchor="lm")
    draw.text((262, H - 50), "·  #03  ·  Banco", font=font(FR, 26), fill=MUTED, anchor="lm")


def make_app(frame, text, dst):
    img = Image.open(f"{FRAMES}/{frame}.png").convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    barh = 250
    d.rectangle([0, 0, W, barh], fill=BANCO + (255,))
    d.rectangle([0, barh, W, barh + 5], fill=(0, 0, 0, 90))
    f = font(FB, 60)
    lines = wrap(d, text, f, W - 110)
    while len(lines) > 3 and f.size > 40:
        f = font(FB, f.size - 4); lines = wrap(d, text, f, W - 110)
    draw_block(d, lines, f, W // 2, barh // 2, (255, 255, 255), f.size + 16)
    d.rectangle([0, H - 86, W, H], fill=(0, 0, 0, 150))
    brand(d)
    img.save(dst)


def make_card(text, dst, outro=False):
    img = Image.new("RGB", (W, H), CARDBG)
    d = ImageDraw.Draw(img, "RGBA")
    if outro:
        d.text((W // 2, H // 2 - 110), "BORN", font=font(FB, 132), fill=INK, anchor="mm")
        d.text((W // 2, H // 2 + 40), "ONCE", font=font(FB, 132), fill=(252, 165, 165), anchor="mm")
        d.text((W // 2, H // 2 + 200), text, font=font(FR, 52), fill=MUTED, anchor="mm")
    else:
        d.rectangle([W // 2 - 60, 760, W // 2 + 60, 768], fill=RED_ACCENT)
        f = font(FB, 86)
        lines = wrap(d, text, f, W - 160)
        while len(lines) > 4 and f.size > 54:
            f = font(FB, f.size - 4); lines = wrap(d, text, f, W - 160)
        draw_block(d, lines, f, W // 2, H // 2 + 20, INK, f.size + 30)
    brand(d)
    img.save(dst)


# 1) harvest cropped app frames
for name, ts in GRAB.items():
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(ts), "-i", SRC,
                    "-frames:v", "1", "-vf", CROP, f"{FRAMES}/{name}.png"], check=True)
    print(f"frame {name} @ {ts}s")

# 2) compose slides
paths, durs = [], []
for i, (key, typ, frame, text, win) in enumerate(TL):
    dst = f"{SLIDES}/{i:02d}_{key}.png"
    if typ == "app":
        make_app(frame, text, dst)
    elif typ == "outro":
        make_card(text, dst, outro=True)
    else:
        make_card(text, dst)
    paths.append(dst); durs.append(win + T)
print(f"{len(paths)} slides")

# 3) xfade chain + audio
total = sum(durs) - (len(durs) - 1) * T
print(f"video total = {total:.1f}s")
cmd = ["ffmpeg", "-y", "-loglevel", "error"]
for p, dur in zip(paths, durs):
    cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", p]
cmd += ["-i", VO, "-i", MUSIC]
fc = [f"[{i}:v]format=yuv420p,setsar=1[v{i}]" for i in range(len(paths))]
prev, L = "v0", durs[0]
for i in range(1, len(paths)):
    fc.append(f"[{prev}][v{i}]xfade=transition=fade:duration={T}:offset={L - T:.3f}[x{i}]")
    prev = f"x{i}"; L = L + durs[i] - T
fc.append(f"[{prev}]fade=t=in:st=0:d=0.5,fade=t=out:st={total - 1.2:.3f}:d=1.2[vout]")
na, nm = len(paths), len(paths) + 1
fc.append(f"[{na}:a]apad=whole_dur={total:.3f},atrim=0:{total:.3f}[vo]")
fc.append(f"[{nm}:a]volume=0.06,atrim=0:{total:.3f},asetpts=N/SR/TB,afade=t=out:st={total - 3:.3f}:d=3[mus]")
fc.append("[vo][mus]amix=inputs=2:normalize=0:duration=first[aout]")
cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-shortest", OUT]
print("rendering...")
subprocess.run(cmd, check=True)
print("DONE ->", OUT)
