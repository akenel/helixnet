#!/usr/bin/env python3
"""Born Once #03 v2 — The Forty-Franc Cream. NEW pipeline:
crisp Puppeteer screens (no chrome, no upscale) + single-take VO (vo-cream-v2.wav).
Red card-bars + dark title cards, crossfaded on the VO beat map, Brotherhood Run at 6%.
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/angel/repos/helixnet"
PROJ = f"{ROOT}/videos/banco/born-once-03-forty-franc-cream"
FRAMES = f"{PROJ}/assets/frames"
SLIDES = f"{PROJ}/assets/slides2"
VO = f"{PROJ}/assets/vo-cream-v2.wav"
MUSIC = f"{ROOT}/compose/helix-media/music/angel-originals/Brotherhood Run.mp3"
OUT = f"{PROJ}/Banco-BornOnce-03-Forty-Franc-Cream-DRAFT.mp4"
os.makedirs(SLIDES, exist_ok=True)

W, H = 1080, 1920
BANCO = (139, 0, 0); CARDBG = (12, 14, 18); INK = (243, 244, 246); MUTED = (156, 163, 175); RED = (200, 40, 40)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
T = 0.6

# id, type, frame, text, window(s) — aligned to vo-cream-v2 beat map
TL = [
    ("s01", "app", "p_login",   "Half this shop has no barcode.",                     3.26),
    ("s02", "app", "p_catalog", "And a cream that costs forty francs.",               6.04),
    ("s03", "app", "p_home",    "Saturday. The new kid's on the till.",               7.04),
    ("s04", "app", "p_sale",    "She reaches for the scanner. Nothing to scan.",      8.18),
    ("s05", "card", None,       "Five tubes.\nNearly identical.",                     4.80),
    ("s06", "card", None,       "One's 40. One's 12.\nGuess wrong — the drawer\nnever balances.", 7.72),
    ("s07", "card", None,       "The old way: a price\ntyped by hand. A sticky note.", 8.84),
    ("s08", "card", None,       "Call the manager. Again.\nEvery unmarked item,\na gamble.", 9.66),
    ("s09", "app", "p_sale",    "She doesn't scan.",                                  4.06),
    ("s10", "app", "p_catalog", "She opens the catalogue — wearing its own face.",    7.08),
    ("s11", "app", "p_catalog", "She taps the picture. Right price, first try.",      8.98),
    ("s12", "card", None,       "Born once —\ngiven a face.",                         8.72),
    ("s13", "app", "p_catalog", "From now on, anyone sells it by sight.",             7.00),
    ("s14", "card", None,       "A barcode belongs\nto the factory.",                 6.84),
    ("s15", "card", None,       "A picture belongs to you.\nYour shelf. Your goods.\nYour eyes.", 7.32),
    ("s16", "card", None,       "Sell what\nyou can see.",                            7.14),
    ("s17", "outro", None,      "born once, known by heart.",                         4.20),
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
    d.text((262, H - 50), "·  #03  ·  Banco", font=font(FR, 26), fill=MUTED, anchor="lm")


def make_app(frame, text, dst):
    img = Image.open(f"{FRAMES}/{frame}.png").convert("RGB")
    if img.size != (W, H): img = img.resize((W, H))
    d = ImageDraw.Draw(img, "RGBA")
    barh = 250
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
print("rendering...")
subprocess.run(cmd, check=True)
print("DONE ->", OUT)
