#!/usr/bin/env python3
"""Born Once #08 — "Word of Mouth" (Season 1 finale + S2 teaser). Cream recap, the
question, the QR-survey concept (drawn QR motif), reviews-land-on-the-cream, Felix's velocity.
Crossfaded on the beat map, Brotherhood Run at 6%."""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/angel/repos/helixnet"
PROJ = f"{ROOT}/videos/banco/born-once-08-word-of-mouth"
FRAMES = f"{PROJ}/assets/frames"; SLIDES = f"{PROJ}/assets/slides"
VO = f"{PROJ}/assets/vo-finale.wav"
MUSIC = f"{ROOT}/compose/helix-media/music/angel-originals/Brotherhood Run.mp3"
OUT = f"{PROJ}/Banco-BornOnce-08-Word-Of-Mouth-DRAFT.mp4"
os.makedirs(SLIDES, exist_ok=True)
W, H = 1080, 1920
BANCO = (139, 0, 0); CARDBG = (12, 14, 18); INK = (243, 244, 246); MUTED = (156, 163, 175); RED = (200, 40, 40)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
T = 0.6

TL = [
    ("s01", "app", "p_catalog", "One little cream. Born on a Friday, rough and nameless.", 4.48),
    ("s02", "app", "p_catalog", "Sold. Made proper. Restocked. Watched. Counted.",        7.32),
    ("s03", "card", None,       "Banco measured all of it.\nBut one thing it couldn't:",   7.14),
    ("s04", "card", None,       "Did it actually work?\nWas it worth forty francs?",       4.82),
    ("s05", "card", None,       "Only the people who took it home can answer that.",       7.00),
    ("s06", "card", None,       "So in Season 2 —\nwe hand them the pen.",                 4.18),
    ("s07", "card", None,       "Here's how it's going to work.",                          3.90),
    ("s08", "card", None,       "No email. A first name,\nmaybe an Instagram. Enough.",    3.52),
    ("s09", "qr",   None,       "On the receipt —\na little QR code.",                     5.04),
    ("s10", "qr",   None,       "Scan it. No app.\nNo password.",                          5.46),
    ("s11", "card", None,       "Did it work? Ten seconds.\nA tap. A star. Buy again?",    5.66),
    ("s12", "card", None,       "Maybe a photo. A ten-second\nclip of it calming the bite.", 4.94),
    ("s13", "card", None,       "And for their honesty —\nreal credit toward next visit.", 6.92),
    ("s14", "app", "p_catalog", "Those words don't vanish. They land on the cream itself.", 6.14),
    ("s15", "app", "p_catalog", "The next person sees a price — and sees 'it worked.'",    8.12),
    ("s16", "card", None,       "The cream stops selling on Felix's word —\nand starts on the neighbourhood's.", 7.36),
    ("s17", "app", "p_felix",   "Felix sees the whole picture —",                          3.74),
    ("s18", "app", "p_dash",    "not just what sold, but what helped.",                    6.30),
    ("s19", "card", None,       "The loop: born once, then known —\nby the people who carried it home.", 6.54),
    ("s20", "card", None,       "We're building it right now.\nSeason 2 of Banco.",        7.68),
    ("s21", "outro", None,      "Season 2, coming soon.",                                  3.00),
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
    d.text((262, H - 50), "·  #08  ·  Banco", font=font(FR, 26), fill=MUTED, anchor="lm")
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
def make_qr(text, dst):
    img = Image.new("RGB", (W, H), CARDBG); d = ImageDraw.Draw(img, "RGBA")
    N, S = 21, 24; size = N * S; ox, oy = (W - size) // 2, 470
    d.rounded_rectangle([ox - 40, oy - 40, ox + size + 40, oy + size + 40], radius=40, fill=(255, 255, 255))

    def finder(fx, fy):
        d.rectangle([ox + fx * S, oy + fy * S, ox + (fx + 7) * S, oy + (fy + 7) * S], fill=(12, 14, 18))
        d.rectangle([ox + (fx + 1) * S, oy + (fy + 1) * S, ox + (fx + 6) * S, oy + (fy + 6) * S], fill=(255, 255, 255))
        d.rectangle([ox + (fx + 2) * S, oy + (fy + 2) * S, ox + (fx + 5) * S, oy + (fy + 5) * S], fill=(12, 14, 18))
    for i in range(N):
        for j in range(N):
            infinder = (i < 7 and j < 7) or (i < 7 and j >= N - 7) or (i >= N - 7 and j < 7)
            if infinder: continue
            if (i * 5 + j * 3 + i * j) % 7 < 3:
                d.rectangle([ox + i * S, oy + j * S, ox + (i + 1) * S, oy + (j + 1) * S], fill=(12, 14, 18))
    finder(0, 0); finder(N - 7, 0); finder(0, N - 7)
    f = font(FB, 78); lines = wrap(d, text, f, W - 160)
    block(d, lines, f, W // 2, oy + size + 200, INK, f.size + 24)
    brand(d); img.save(dst)


paths, durs = [], []
for i, (key, typ, frame, text, win) in enumerate(TL):
    dst = f"{SLIDES}/{i:02d}_{key}.png"
    if typ == "app": make_app(frame, text, dst)
    elif typ == "outro": make_card(text, dst, outro=True)
    elif typ == "qr": make_qr(text, dst)
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
