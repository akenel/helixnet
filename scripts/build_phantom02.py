#!/usr/bin/env python3
"""Born Once #02 — The Phantom Sale. Portrait Slideshow Explainer (Banco Method).

Composes slides (app screenshots with red card-bars over the browser chrome,
plus dark title cards for the abstract/hunt beats), crossfades them on the VO
beat map, and beds Brotherhood Run at 5%. One draft -> one mp4.
"""
import os
import subprocess
import textwrap as _tw
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/angel/repos/helixnet"
PROJ = f"{ROOT}/videos/banco/born-once-02-phantom-sale"
FRAMES = f"{PROJ}/assets/frames"
SLIDES = f"{PROJ}/assets/slides"
VO = f"{PROJ}/assets/vo-tight.wav"
MUSIC = f"{ROOT}/compose/helix-media/music/angel-originals/Brotherhood Run.mp3"
OUT = f"{PROJ}/Banco-BornOnce-02-Phantom-Sale-DRAFT.mp4"
os.makedirs(SLIDES, exist_ok=True)

W, H = 1080, 1920
BANCO = (139, 0, 0)
CARDBG = (12, 14, 18)
INK = (243, 244, 246)
MUTED = (156, 163, 175)
RED_ACCENT = (200, 40, 40)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

T = 0.6  # crossfade seconds

# id, type, frame, card text, window seconds
TL = [
    ("login",    "app",  "s_login",     "We sold a product that didn't exist.",                       3.3),
    ("name",     "app",  "s_name",      "It looked perfect.",                                         4.3),
    ("photo",    "app",  "s_photo",     "Names it. Prices it. Snaps a photo.",                        3.6),
    ("sale",     "app",  "s_sale",      "Sells it. The receipt prints. The points land.",             8.3),
    ("search",   "app",  "s_searchtype","Two minutes later — she searches the name.",            3.9),
    ("notfound", "app",  "s_notfound",  "Nothing. No matches.",                                       8.3),
    ("phantom",  "card", None,          "The sale was real.\nThe product never saved.\nA phantom.",  13.0),
    ("shop",     "card", None,          "Now imagine that's your shop.",                              9.3),
    ("broken",   "card", None,          "Scan once, known forever.\nSilently broken.",               11.7),
    ("twoways",  "card", None,          "Two ways to make a product.",                                6.4),
    ("twin",     "card", None,          "One seal worked.\nIts identical twin leaked.",              11.5),
    ("oneline",  "card", None,          "One line.\nThe same door the cashier\nalready had.",         9.3),
    ("reslist",  "app",  "s_reslist",   "She scans, creates, sells, searches…",                  4.2),
    ("hero",     "app",  "s_hero",      "There it is. It stuck. Forever.",                            9.3),
    ("lesson",   "card", None,          "If one seal fails,\ncheck all the seals.",                   5.1),
    ("livedin",  "card", None,          "Not tested — lived in.",                                3.5),
    ("outro",    "outro",None,          "the phantom's dead.",                                        3.8),
]


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, maxw):
    out = []
    for para in text.split("\n"):
        if not para:
            out.append("")
            continue
        words, line = para.split(" "), ""
        for w in words:
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


def draw_block(draw, lines, fnt, cx, cy, fill, lh, anchor="mm"):
    total = lh * len(lines)
    y = cy - total / 2 + lh / 2
    for ln in lines:
        draw.text((cx, y), ln, font=fnt, fill=fill, anchor=anchor)
        y += lh


def brand(draw):
    f = font(FB, 26)
    draw.text((40, H - 50), "BORN ONCE", font=f, fill=(255, 255, 255), anchor="lm")
    draw.text((262, H - 50), "·  #02  ·  Banco", font=font(FR, 26), fill=MUTED, anchor="lm")


def make_app(frame, text, dst):
    src = Image.open(f"{FRAMES}/{frame}.png").convert("RGB")
    # source ~1080x2160 portrait phone -> crop a 1080x1920 window (chrome up top gets covered by the bar)
    sw, sh = src.size
    scale = W / sw
    src = src.resize((W, int(sh * scale)))
    y0 = 185
    img = src.crop((0, y0, W, y0 + H))
    d = ImageDraw.Draw(img, "RGBA")
    # red top card-bar over the browser chrome
    barh = 250
    d.rectangle([0, 0, W, barh], fill=BANCO + (255,))
    d.rectangle([0, barh, W, barh + 5], fill=(0, 0, 0, 90))
    f = font(FB, 60)
    lines = wrap(d, text, f, W - 110)
    while len(lines) > 3 and f.size > 40:
        f = font(FB, f.size - 4)
        lines = wrap(d, text, f, W - 110)
    draw_block(d, lines, f, W // 2, barh // 2, (255, 255, 255), f.size + 16)
    # subtle bottom scrim for the brand tag
    d.rectangle([0, H - 86, W, H], fill=(0, 0, 0, 150))
    brand(d)
    img.convert("RGB").save(dst)


def make_card(text, dst, outro=False):
    img = Image.new("RGB", (W, H), CARDBG)
    d = ImageDraw.Draw(img, "RGBA")
    if outro:
        fbig = font(FB, 132)
        d.text((W // 2, H // 2 - 110), "BORN", font=fbig, fill=INK, anchor="mm")
        d.text((W // 2, H // 2 + 40), "ONCE", font=fbig, fill=(252, 165, 165), anchor="mm")
        d.text((W // 2, H // 2 + 200), text, font=font(FR, 52), fill=MUTED, anchor="mm")
    else:
        # red accent tick above the line
        d.rectangle([W // 2 - 60, 760, W // 2 + 60, 768], fill=RED_ACCENT)
        f = font(FB, 86)
        lines = wrap(d, text, f, W - 160)
        while len(lines) > 4 and f.size > 54:
            f = font(FB, f.size - 4)
            lines = wrap(d, text, f, W - 160)
        draw_block(d, lines, f, W // 2, H // 2 + 20, INK, f.size + 30)
    brand(d)
    img.save(dst)


# 1) compose every slide PNG
paths, durs = [], []
for i, (key, typ, frame, text, win) in enumerate(TL):
    dst = f"{SLIDES}/{i:02d}_{key}.png"
    if typ == "app":
        make_app(frame, text, dst)
    elif typ == "outro":
        make_card(text, dst, outro=True)
    else:
        make_card(text, dst)
    paths.append(dst)
    durs.append(win + T)
    print(f"slide {i:02d} {key:9s} {typ:5s} {win}s")

# 2) build the xfade chain
total = sum(durs) - (len(durs) - 1) * T
print(f"video total = {total:.1f}s")
cmd = ["ffmpeg", "-y", "-loglevel", "error"]
for p, dur in zip(paths, durs):
    cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", p]
cmd += ["-i", VO, "-i", MUSIC]

fc = []
for i in range(len(paths)):
    fc.append(f"[{i}:v]format=yuv420p,setsar=1[v{i}]")
prev, L = "v0", durs[0]
for i in range(1, len(paths)):
    off = L - T
    out = f"x{i}"
    fc.append(f"[{prev}][v{i}]xfade=transition=fade:duration={T}:offset={off:.3f}[{out}]")
    prev = out
    L = L + durs[i] - T
fc.append(f"[{prev}]fade=t=in:st=0:d=0.5,fade=t=out:st={total-1.2:.3f}:d=1.2[vout]")

na, nm = len(paths), len(paths) + 1
fc.append(f"[{na}:a]apad=whole_dur={total:.3f},atrim=0:{total:.3f}[vo]")
fc.append(f"[{nm}:a]volume=0.05,atrim=0:{total:.3f},asetpts=N/SR/TB,afade=t=out:st={total-3:.3f}:d=3[mus]")
fc.append(f"[vo][mus]amix=inputs=2:normalize=0:duration=first[aout]")

cmd += ["-filter_complex", ";".join(fc),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-shortest", OUT]
print("rendering...")
subprocess.run(cmd, check=True)
print("DONE ->", OUT)
