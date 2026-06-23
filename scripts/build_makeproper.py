#!/usr/bin/env python3
"""Born Once #04 — "Make It Proper". Crisp Puppeteer screens (Pam's sale, the dashboard,
Ralph's manager edit form) + single-take VO. Red card-bars + dark cards, crossfaded on the
beat map, Brotherhood Run at 6%."""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/angel/repos/helixnet"
PROJ = f"{ROOT}/videos/banco/born-once-04-make-it-proper"
FRAMES = f"{PROJ}/assets/frames"
SLIDES = f"{PROJ}/assets/slides"
VO = f"{PROJ}/assets/vo-make-proper.wav"
MUSIC = f"{ROOT}/compose/helix-media/music/angel-originals/Brotherhood Run.mp3"
OUT = f"{PROJ}/Banco-BornOnce-04-Make-It-Proper-DRAFT.mp4"
os.makedirs(SLIDES, exist_ok=True)
W, H = 1080, 1920
BANCO = (139, 0, 0); CARDBG = (12, 14, 18); INK = (243, 244, 246); MUTED = (156, 163, 175); RED = (200, 40, 40)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
T = 0.6

TL = [
    ("s01", "app", "p_sale",     "Friday rush — a new cream, no barcode.",                     5.16),
    ("s02", "app", "p_sale",     "Names it. Prices it. Photo. Sells it.",                      6.02),
    ("s03", "card", None,        "Born in a hurry —\nbut the line's moving.",                  6.62),
    ("s04", "app", "p_catalog",  "Then Larry buys one. Then Sally.",                           5.48),
    ("s05", "app", "p_catalog",  "Two in a day — a cream nobody knew yesterday.",              8.34),
    ("s06", "app", "p_home",     "Felix is on the road. He opens his phone.",                  7.46),
    ("s07", "app", "p_home",     "There it is — selling. He knows a hit.",                     5.76),
    ("s08", "card", None,        "He can't fix it from\nthe highway. Not his job.",            3.90),
    ("s09", "card", None,        "So he texts Ralph\none link.",                               8.54),
    ("s10", "card", None,        "The website has it all —\nbut it's not wired\nto the till.", 10.60),
    ("s11", "app", "p_edit",     "Ralph brings it across by hand — real photo, real specs.",   4.40),
    ("s12", "card", None,        "Does the barcode match?\nA human checks.\nSometimes it doesn't.", 10.82),
    ("s13", "app", "p_edit",     "He sets the cost. A reorder. The cream grew up.",            8.72),
    ("s14", "app", "p_ralphcat", "Next morning — the cream's got a face.",                     6.22),
    ("s15", "app", "p_catalog",  "A real photo. Specs. A margin. A reorder.",                  9.56),
    ("s16", "card", None,        "Nobody touched the 7,000\nthat never sell.",                 5.62),
    ("s17", "card", None,        "You don't polish\na dead shelf.",                            6.66),
    ("s18", "card", None,        "A cashier borns it.\nA manager raises it.\nThe owner notices.", 8.20),
    ("s19", "card", None,        "Effort follows velocity.",                                   3.12),
    ("s20", "outro", None,       "born rough, made proper.",                                   3.00),
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
    d.text((262, H - 50), "·  #04  ·  Banco", font=font(FR, 26), fill=MUTED, anchor="lm")
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
