#!/usr/bin/env python3
"""Born Once #07 — "The Drawer That Wouldn't Close". Old-way dread on cards, the My Drawer
screen (float, expected, count-out) for the Banco answer, resolution on cards."""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/angel/repos/helixnet"
PROJ = f"{ROOT}/videos/banco/born-once-07-drawer-that-wouldnt-close"
FRAMES = f"{PROJ}/assets/frames"; SLIDES = f"{PROJ}/assets/slides"
VO = f"{PROJ}/assets/vo-drawer.wav"
MUSIC = f"{ROOT}/compose/helix-media/music/angel-originals/Brotherhood Run.mp3"
OUT = f"{PROJ}/Banco-BornOnce-07-The-Drawer-That-Wouldnt-Close-DRAFT.mp4"
os.makedirs(SLIDES, exist_ok=True)
W, H = 1080, 1920
BANCO = (139, 0, 0); CARDBG = (12, 14, 18); INK = (243, 244, 246); MUTED = (156, 163, 175); RED = (200, 40, 40)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
T = 0.6

TL = [
    ("s01", "card", None,      "Midnight. You count the till.\nIt's 40 francs short.",        4.60),
    ("s02", "card", None,      "Not a disaster. But you have\nno idea where it went.",        9.38),
    ("s03", "card", None,      "A wrong change? A missed sale?\nA hand in the drawer?",        5.16),
    ("s04", "card", None,      "The old till just shrugs.\nOne drawer, every hand in it.",     5.30),
    ("s05", "card", None,      "The money is a blur.",                                        2.36),
    ("s06", "card", None,      "On a shared till you can't even\nask the right question.",     6.26),
    ("s07", "card", None,      "The shortfall has no name,\nno time, no story.",              7.42),
    ("s08", "card", None,      "You sigh. You eat the 40 francs.\nYou hope it's less tomorrow.", 6.08),
    ("s09", "app", "p_drawer", "Banco: you start by counting your float. Your drawer.",        7.26),
    ("s10", "app", "p_drawer", "Every sale, every paid-in, every payout — tied to you.",       6.66),
    ("s11", "app", "p_drawer", "Not the till. You. At close, you count the cash back.",        6.54),
    ("s12", "app", "p_drawer", "The till says what it should be — to the franc.",              6.80),
    ("s13", "card", None,      "Now the 40 francs isn't a mystery.\nIt's Maria's drawer.",     4.46),
    ("s14", "card", None,      "Tuesday, the evening shift.\nAn honest miscount? A coaching moment?", 6.76),
    ("s15", "card", None,      "Either way — you can see it.\nThat's not suspicion. That's light.", 7.18),
    ("s16", "card", None,      "You can't fix what you can't see.\nBanco doesn't accuse. It counts.", 6.34),
    ("s17", "card", None,      "A drawer that closes —\nbecause it tells the truth.",          4.94),
    ("s18", "outro", None,     "every franc accounted for.",                                  3.00),
]


def font(p, s): return ImageFont.truetype(p, s)
def wrap(d, text, fnt, maxw):
    out = []
    for para in text.split("\n"):
        if not para: out.append(""); continue
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
    for ln in lines: d.text((cx, y), ln, font=fnt, fill=fill, anchor="mm"); y += lh
def brand(d):
    d.text((40, H - 50), "BORN ONCE", font=font(FB, 26), fill=(255, 255, 255), anchor="lm")
    d.text((262, H - 50), "·  #07  ·  Banco", font=font(FR, 26), fill=MUTED, anchor="lm")
def make_app(frame, text, dst):
    img = Image.open(f"{FRAMES}/{frame}.png").convert("RGB")
    if img.size != (W, H): img = img.resize((W, H))
    d = ImageDraw.Draw(img, "RGBA"); barh = 250
    d.rectangle([0, 0, W, barh], fill=BANCO + (255,)); d.rectangle([0, barh, W, barh + 5], fill=(0, 0, 0, 90))
    f = font(FB, 60); lines = wrap(d, text, f, W - 110)
    while len(lines) > 3 and f.size > 40: f = font(FB, f.size - 4); lines = wrap(d, text, f, W - 110)
    block(d, lines, f, W // 2, barh // 2, (255, 255, 255), f.size + 16)
    d.rectangle([0, H - 86, W, H], fill=(0, 0, 0, 150)); brand(d); img.save(dst)
def make_card(text, dst, outro=False):
    img = Image.new("RGB", (W, H), CARDBG); d = ImageDraw.Draw(img, "RGBA")
    if outro:
        d.text((W // 2, H // 2 - 110), "BORN", font=font(FB, 132), fill=INK, anchor="mm")
        d.text((W // 2, H // 2 + 40), "ONCE", font=font(FB, 132), fill=(252, 165, 165), anchor="mm")
        d.text((W // 2, H // 2 + 200), text, font=font(FR, 52), fill=MUTED, anchor="mm")
    else:
        d.rectangle([W // 2 - 60, 760, W // 2 + 60, 768], fill=RED)
        f = font(FB, 86); lines = wrap(d, text, f, W - 160)
        while len(lines) > 4 and f.size > 54: f = font(FB, f.size - 4); lines = wrap(d, text, f, W - 160)
        block(d, lines, f, W // 2, H // 2 + 20, INK, f.size + 30)
    brand(d); img.save(dst)


paths, durs = [], []
for i, (key, typ, frame, text, win) in enumerate(TL):
    dst = f"{SLIDES}/{i:02d}_{key}.png"
    if typ == "app": make_app(frame, text, dst)
    elif typ == "outro": make_card(text, dst, outro=True)
    else: make_card(text, dst)
    paths.append(dst); durs.append(win + T)
total = sum(durs) - (len(durs) - 1) * T
print(f"{len(paths)} slides, total {total:.1f}s")
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
fc.append(f"[{nm}:a]volume=0.06,atrim=0:{total:.3f},asetpts=N/SR/TB,afade=t=out:st={total - 3:.3f}:d=3[mus]")
fc.append("[vo][mus]amix=inputs=2:normalize=0:duration=first[aout]")
cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT]
print("rendering..."); subprocess.run(cmd, check=True); print("DONE ->", OUT)
