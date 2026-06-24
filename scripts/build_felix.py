#!/usr/bin/env python3
"""Born Once #06 — "Felix on the Road". Felix's dashboard + active dashboard + cream +
a rendered PRD·LIVE badge card. Crossfaded on the beat map, Brotherhood Run at 6%."""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/angel/repos/helixnet"
PROJ = f"{ROOT}/videos/banco/born-once-06-felix-on-the-road"
FRAMES = f"{PROJ}/assets/frames"; SLIDES = f"{PROJ}/assets/slides"
VO = f"{PROJ}/assets/vo-felix.wav"
MUSIC = f"{ROOT}/compose/helix-media/music/angel-originals/Brotherhood Run.mp3"
OUT = f"{PROJ}/Banco-BornOnce-06-Felix-On-The-Road-DRAFT.mp4"
os.makedirs(SLIDES, exist_ok=True)
W, H = 1080, 1920
BANCO = (139, 0, 0); CARDBG = (12, 14, 18); INK = (243, 244, 246); MUTED = (156, 163, 175); RED = (200, 40, 40)
PRDGREEN = (4, 120, 87)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
T = 0.6

TL = [
    ("s01", "card", None,      "Every owner's\n3am question.",                              4.22),
    ("s02", "card", None,      "What's happening in my shop\nright now — when I'm not in it?", 5.52),
    ("s03", "app", "p_felix",  "Felix owns Artemis. Almost never behind the counter.",      7.26),
    ("s04", "card", None,      "So how does he sleep?\nHe opens his phone.",                4.24),
    ("s05", "app", "p_dash",   "Thirty seconds. Today's sales. The drawer, balanced.",      6.62),
    ("s06", "app", "p_catalog","The cream from the delivery — selling down, tube by tube.", 6.94),
    ("s07", "app", "p_dash",   "200 km away — watching his shop breathe.",                  5.98),
    ("s08", "prd", None,       "The real shop. Live.\nNot a test. Not yesterday.",          8.58),
    ("s09", "card", None,      "The numbers are now.\nHe's not guessing.",                  3.34),
    ("s10", "card", None,      "No calling in to interrupt\nPam mid-sale. He just… knows.", 6.04),
    ("s11", "card", None,      "Something off? He catches it\nfrom the highway. One text.", 4.56),
    ("s12", "card", None,      "Everything fine? He closes\nthe phone and keeps driving.",  4.80),
    ("s13", "card", None,      "The shop didn't need him\nstanding in it to be safe.",      6.06),
    ("s14", "card", None,      "The freedom nobody sells you\nwith a cash register.",       3.76),
    ("s15", "card", None,      "The freedom to not be there.",                              2.90),
    ("s16", "card", None,      "A shop that runs while you're gone —\nthe watching is built in.", 5.62),
    ("s17", "card", None,      "Felix can finally leave the shop —\nand still have it.",     4.40),
    ("s18", "outro", None,     "the shop in your pocket.",                                  3.00),
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
    d.text((262, H - 50), "·  #06  ·  Banco", font=font(FR, 26), fill=MUTED, anchor="lm")
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
def make_prd(text, dst):
    img = Image.new("RGB", (W, H), CARDBG); d = ImageDraw.Draw(img, "RGBA")
    # green PRD pill
    pf = font(FB, 130); tw = d.textlength("PRD", font=pf)
    cx, cy = W // 2, 640; padx, pady = 70, 36
    d.rounded_rectangle([cx - tw / 2 - padx, cy - 95 - pady, cx + tw / 2 + padx, cy + 35 + pady], radius=60, fill=PRDGREEN)
    d.text((cx, cy - 30), "PRD", font=pf, fill=(255, 255, 255), anchor="mm")
    d.text((cx, cy + 110), "●  LIVE", font=font(FB, 44), fill=(110, 231, 183), anchor="mm")
    f = font(FB, 78); lines = wrap(d, text, f, W - 160)
    block(d, lines, f, cx, 1080, INK, f.size + 26)
    brand(d); img.save(dst)


paths, durs = [], []
for i, (key, typ, frame, text, win) in enumerate(TL):
    dst = f"{SLIDES}/{i:02d}_{key}.png"
    if typ == "app": make_app(frame, text, dst)
    elif typ == "outro": make_card(text, dst, outro=True)
    elif typ == "prd": make_prd(text, dst)
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
