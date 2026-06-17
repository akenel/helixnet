"""
BYOH worker -- core render pipeline (the "muscle").

text  ->  Piper (voice)  ->  ffmpeg (waveform + caption card)  ->  MP4

No web framework here on purpose: this module is just the work. The wire
(worker.py) wraps it in an HTTP endpoint so a recipe can call it by URL,
whether it runs on this laptop, on DigitalOcean, or on a gamer's GPU box.
Bring Your Own Hardware = same render(), different machine.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
from pathlib import Path

# --- where the tools live (laptop defaults; override via env on any other box) ---
# This is the whole BYOH trick: same code, the machine tells it where its tools are.
PIPER_BIN = Path(os.getenv("PIPER_BIN", "/home/angel/repos/helixnet/.venv/bin/piper"))
VOICES_DIR = Path(os.getenv("VOICES_DIR", "/home/angel/.local/share/piper-voices"))
FONT = Path(os.getenv("FONT", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

# Voice feel: synthesize CLEAN at length-scale 1.0 (stretching lessac inside Piper
# warbles, and loudnorm pumps -- that was the sentence-2 scratch). Slow the finished
# audio with ffmpeg atempo instead: a clean time-stretch, pitch preserved, no clip.
# atempo 0.85 == the ~17% slower pace Sylvie picked (== old length-scale 1.175).
LENGTH_SCALE = os.getenv("LENGTH_SCALE", "1.0")
SENTENCE_SILENCE = os.getenv("SENTENCE_SILENCE", "0.3")
TEMPO = os.getenv("TEMPO", "0.85")   # <1.0 = slower
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")   # faster-whisper model for word timings

VOICES = {
    "en": "en_US-joe-medium.onnx",       # English male (Angel's pick -- warmer than lessac)
    "en_f": "en_US-amy-medium.onnx",     # English female (the good one)
    "en_hq": "en_US-ryan-high.onnx",      # premium/most-human but SLOW (>60s on CPU) -- not for live use
    "en_gb": "en_GB-alba-medium.onnx",
    "it": "it_IT-paola-medium.onnx",
    "it_m": "it_IT-riccardo-x_low.onnx",
}

# selectable canvas: square (feeds), portrait (Shorts/Reels), landscape (full-screen)
ASPECTS = {
    "square":    (1080, 1080),
    "portrait":  (1080, 1920),
    "landscape": (1920, 1080),
}
BG = "0x0B1F3A"      # HelixNet deep navy
WAVE = "0xF5A623"    # amber


def _piper_bin() -> str:
    return str(PIPER_BIN)


def synth_voice(text: str, voice: str, out_wav: Path) -> None:
    """text -> Piper WAV (clean, length-scale 1.0) -> ffmpeg atempo (clean slow-down).
    Slowing inside Piper warbles + needs loudnorm (which pumps); time-stretching the
    finished audio is clean and keeps the pitch. Verified: flat factor 0, peak ~0."""
    model = VOICES_DIR / VOICES.get(voice, VOICES["en"])
    raw = out_wav.with_suffix(".raw.wav")
    proc = subprocess.run(
        [_piper_bin(), "-m", str(model), "-f", str(raw),
         "--length-scale", LENGTH_SCALE, "--sentence-silence", SENTENCE_SILENCE],
        input=text.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0 or not raw.exists():
        raise RuntimeError(f"piper failed: {proc.stderr.decode('utf-8', 'replace')[:500]}")
    # slow the finished voice (atempo preserves pitch) + a static -3dB trim so Piper's
    # run-to-run peak variance can NEVER reach 0dB and clip (no dynamics = no pump/warble).
    tempo = subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw),
         "-af", f"atempo={TEMPO},volume=-3dB", "-ar", "22050", str(out_wav)],
        capture_output=True,
    )
    raw.unlink(missing_ok=True)
    if tempo.returncode != 0 or not out_wav.exists():
        raise RuntimeError(f"tempo failed: {tempo.stderr.decode('utf-8', 'replace')[-400:]}")


def _ass_time(t: float) -> str:
    """seconds -> ASS time H:MM:SS.cc"""
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def word_timestamps(wav: Path) -> list[tuple[str, float, float]]:
    """Transcribe the (clean TTS) audio to word-level (word, start, end) timings."""
    from faster_whisper import WhisperModel
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(wav), word_timestamps=True, language="en")
    words: list[tuple[str, float, float]] = []
    for seg in segments:
        for w in (seg.words or []):
            t = w.word.strip()
            if t:
                words.append((t, float(w.start), float(w.end)))
    return words


def _karaoke_ass(words: list[tuple[str, float, float]], W: int, H: int, fontsize: int) -> str:
    """Build an ASS subtitle that highlights each word as it's spoken (karaoke \\k).
    Words are wrapped into lines, then grouped into multi-line BLOCKS (a sentence or two
    on screen at once) so the karaoke flows and fills the canvas instead of one short line."""
    wrap = max(14, int((W - 160) / (fontsize * 0.6)))
    lines, cur, cur_len = [], [], 0
    for w in words:
        wl = len(w[0]) + 1
        if cur and cur_len + wl > wrap:
            lines.append(cur); cur, cur_len = [], 0
        cur.append(w); cur_len += wl
    if cur:
        lines.append(cur)
    # group lines into blocks: prefer sentence ends, cap by what fits the canvas height
    max_lines = 6 if H > W else 3      # portrait fills tall; landscape/square fewer
    blocks, b = [], []
    for ln in lines:
        b.append(ln)
        ends_sentence = ln[-1][0].rstrip().endswith((".", "!", "?"))
        if len(b) >= max_lines or (ends_sentence and len(b) >= 2):
            blocks.append(b); b = []
    if b:
        blocks.append(b)
    header = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {W}\nPlayResY: {H}\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        # PrimaryColour (sung) = amber; SecondaryColour (not yet) = dim grey; black outline
        f"Style: K,DejaVu Sans,{fontsize},&H0023A6F5,&H00808080,&H00000000,&H64000000,"
        "1,0,0,0,100,100,0,0,1,3,1,5,60,60,0,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    events = []
    for block in blocks:
        flat = [w for ln in block for w in ln]
        start, end = flat[0][1], flat[-1][2]
        # \k per word = time until the next word starts (flows across all lines of the block)
        cs = []
        for i, (word, ws, we) in enumerate(flat):
            nxt = flat[i + 1][1] if i + 1 < len(flat) else we
            cs.append(max(1, int(round((nxt - ws) * 100))))
        parts, gi = [], 0
        for li, ln in enumerate(block):
            for (word, ws, we) in ln:
                parts.append(f"{{\\k{cs[gi]}}}{word} ")
                gi += 1
            if li < len(block) - 1:
                parts.append("\\N")
        text = "".join(parts).replace(" \\N", "\\N").strip()
        events.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},K,,0,0,0,,{text}")
    return header + "\n".join(events) + "\n"


def compose_video(wav: Path, caption: str, out_mp4: Path, aspect: str = "square",
                  karaoke: bool = False) -> None:
    """WAV + caption -> MP4 (navy card, amber waveform, wrapped caption) at the chosen aspect."""
    W, H = ASPECTS.get(aspect, ASPECTS["landscape"])
    fontsize = 72          # bigger = more presence / fills more of the canvas
    wave_h = int(H * 0.22)          # waveform band, proportional to the canvas
    wave_margin = int(H * 0.10)     # gap from the bottom
    cap_offset = int(H * 0.06)      # nudge the caption up from dead-center
    tmpfiles: list[str] = []

    # KARAOKE: words light up as spoken (Whisper timings -> ASS \k). Falls back to a
    # static caption if Whisper finds no words.
    words = word_timestamps(wav) if karaoke else []
    if words:
        ass = _karaoke_ass(words, W, H, fontsize)
        with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8") as af:
            af.write(ass); assfile = af.name
        tmpfiles.append(assfile)
        text_filter = f"[withwave]ass={assfile}[v]"
    else:
        wrap = max(14, int((W - 160) / (fontsize * 0.6)))
        wrapped = "\n".join(textwrap.wrap(caption, width=wrap)) or " "
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
            tf.write(wrapped); textfile = tf.name
        tmpfiles.append(textfile)
        text_filter = (f"[withwave]drawtext=fontfile={FONT}:textfile={textfile}:"
                       f"fontcolor=white:fontsize={fontsize}:line_spacing=16:"
                       f"x=(w-text_w)/2:y=(h-text_h)/2-{cap_offset}[v]")

    filtergraph = (
        f"[0:a]showwaves=s={W}x{wave_h}:mode=cline:colors={WAVE}:rate=30[wave];"
        f"color=c={BG}:s={W}x{H}:r=30[bg];"
        f"[bg][wave]overlay=0:H-h-{wave_margin}[withwave];"
        f"{text_filter}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(wav),
        "-filter_complex", filtergraph,
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        "-shortest", str(out_mp4),
    ]
    proc = subprocess.run(cmd, capture_output=True)
    for f in tmpfiles:
        Path(f).unlink(missing_ok=True)
    if proc.returncode != 0 or not out_mp4.exists():
        raise RuntimeError(f"ffmpeg failed: {proc.stderr.decode('utf-8', 'replace')[-800:]}")


def render(text: str, out_mp4: Path, voice: str = "en", caption: str | None = None,
           aspect: str = "square", karaoke: bool = False) -> Path:
    """Full pipeline. Returns the MP4 path."""
    out_mp4 = Path(out_mp4)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "voice.wav"
        synth_voice(text, voice, wav)
        compose_video(wav, caption if caption is not None else text, out_mp4,
                      aspect=aspect, karaoke=karaoke)
    return out_mp4


if __name__ == "__main__":
    import sys
    txt = sys.argv[1] if len(sys.argv) > 1 else "Bring your own hardware. The square never sleeps."
    v = sys.argv[2] if len(sys.argv) > 2 else "en"
    dest = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("out/demo.mp4")
    print(f"rendering -> {dest} (voice={v})")
    render(txt, dest, voice=v)
    print(f"done: {dest.resolve()}")
