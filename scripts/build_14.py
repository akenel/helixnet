#!/usr/bin/env python3
"""Born Once #14 — "Nobody's Coming" (Season 3 opener / trailer).
Cards-only (no app footage), Bauhaus-on-noir title cards crossfaded on the VO beat map
(from Whisper on VO14_final.wav), Brotherhood Run bedded at 5%. Mirrors build_cream03_v2 pipeline.
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/angel/repos/helixnet"
PROJ = f"{ROOT}/videos/banco/Season 3 - Never Alone/born-once-14-nobody-coming"
SLIDES = f"{PROJ}/assets/slides"
VO = f"{PROJ}/VO14_final.wav"
MUSIC = f"{ROOT}/compose/helix-media/music/angel-originals/Brotherhood Run.mp3"
OUT = f"{PROJ}/Banco-BornOnce-14-Nobody-Coming-DRAFT.mp4"
os.makedirs(SLIDES, exist_ok=True)

W, H = 1080, 1920
CARDBG = (12, 14, 18); INK = (243, 244, 246); MUTED = (156, 163, 175)
B_RED = (213, 43, 30); B_BLUE = (0, 78, 168); B_YEL = (247, 201, 40); B_WHT = (235, 235, 230)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
T = 0.6

# id, type, text, window(s) — start times aligned to VO14_final beat map (Whisper)
TL = [
    ("c01", "card",  "There's a word:\nhypercare.",                       10.30),
    ("c02", "card",  "A team. On call.\nWatching over your shop.",         5.00),
    ("c03", "card",  "Sounds wonderful.",                                  5.60),
    ("c04", "card",  "Hypercare is a phase.\nIt has an end date.",         5.60),
    ("c05", "card",  "You become\nticket #84,672.",                        4.50),
    ("c06", "card",  "The care was real.\nIt just never lasted.",          8.16),
    ("c07", "card",  "Felix.\nOne man. One shop.",                         6.84),
    ("c08", "card",  "First month.\nNo one to call.",                      9.20),
    ("c09", "card",  "Built for someone\nelse.",                           9.46),
    ("c10", "card",  "Is the software perfect?\nNothing is.",              8.62),
    ("c11", "card",  "The day it can't do\nthe one thing he needs…",       5.60),
    ("c12", "card",  "Who's coming?\nWith the big guys — nobody.",         6.46),
    ("c13", "card",  "But what if it\nnever ended?",                       8.04),
    ("c14", "card",  "Say what's wrong —\nand it heals.",                  5.62),
    ("c15", "card",  "Before he locks up\ntonight.",                       8.46),
    ("c16", "outro", "Season 3 · Never Alone",                            3.54),
    ("c17", "tag",   "The shop that\nhas your back.",                      3.00),
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
    d.text((262, H - 50), "·  #14  ·  Banco", font=font(FR, 26), fill=MUTED, anchor="lm")


def bauhaus(d, idx):
    """Deterministic geometric composition in the upper band y∈[150,640]; varies by idx."""
    t = idx % 6
    if t == 0:
        d.ellipse([120, 190, 360, 430], fill=B_BLUE)
        d.rectangle([620, 210, 940, 300], fill=B_RED)
    elif t == 1:
        d.rectangle([700, 180, 940, 420], fill=B_YEL)
        d.line([120, 600, 520, 200], fill=B_WHT, width=10)
    elif t == 2:
        d.ellipse([430, 170, 650, 390], fill=B_RED)
        d.rectangle([150, 470, 470, 560], fill=B_BLUE)
    elif t == 3:
        d.polygon([(150, 600), (340, 200), (530, 600)], fill=B_YEL)
        d.rectangle([640, 250, 940, 340], fill=B_RED)
    elif t == 4:
        d.ellipse([680, 200, 900, 420], fill=B_BLUE)
        d.line([140, 240, 560, 240], fill=B_RED, width=14)
    else:
        d.rectangle([150, 200, 420, 470], fill=B_RED)
        d.ellipse([600, 360, 760, 520], fill=B_YEL)


def make_card(idx, text, dst):
    img = Image.new("RGB", (W, H), CARDBG); d = ImageDraw.Draw(img, "RGBA")
    bauhaus(d, idx)
    f = font(FB, 84); lines = wrap(d, text, f, W - 170)
    while len(lines) > 4 and f.size > 52: f = font(FB, f.size - 4); lines = wrap(d, text, f, W - 170)
    block(d, lines, f, W // 2, H // 2 + 110, INK, f.size + 28)
    brand(d); img.save(dst)


def make_outro(text, dst):
    img = Image.new("RGB", (W, H), CARDBG); d = ImageDraw.Draw(img, "RGBA")
    # Bauhaus trio across the top
    d.ellipse([130, 200, 330, 400], fill=B_BLUE)
    d.rectangle([440, 220, 640, 380], fill=B_RED)
    d.polygon([(740, 400), (840, 200), (940, 400)], fill=B_YEL)
    d.text((W // 2, H // 2 - 110), "BORN", font=font(FB, 150), fill=INK, anchor="mm")
    d.text((W // 2, H // 2 + 70), "ONCE", font=font(FB, 150), fill=(252, 165, 165), anchor="mm")
    d.text((W // 2, H // 2 + 240), text, font=font(FR, 50), fill=MUTED, anchor="mm")
    brand(d); img.save(dst)


def make_tag(text, dst):
    img = Image.new("RGB", (W, H), CARDBG); d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([W // 2 - 70, 700, W // 2 + 70, 712], fill=B_RED)
    f = font(FB, 92); lines = wrap(d, text, f, W - 160)
    block(d, lines, f, W // 2, H // 2 + 20, INK, f.size + 28)
    brand(d); img.save(dst)


paths, durs = [], []
for i, (key, typ, text, win) in enumerate(TL):
    dst = f"{SLIDES}/{i:02d}_{key}.png"
    if typ == "outro": make_outro(text, dst)
    elif typ == "tag": make_tag(text, dst)
    else: make_card(i, text, dst)
    paths.append(dst); durs.append(win + T)

total = sum(durs) - (len(durs) - 1) * T
print(f"{len(paths)} slides, total {total:.1f}s (VO≈110.4s)")
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
