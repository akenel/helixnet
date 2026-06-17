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

VOICES = {
    "en": "en_US-lessac-medium.onnx",    # English male (default), fast + clean
    "en_f": "en_US-amy-medium.onnx",     # English female
    "en_hq": "en_US-ryan-high.onnx",      # premium/most-human but SLOW (>60s on CPU) -- not for live use
    "en_gb": "en_GB-alba-medium.onnx",
    "it": "it_IT-paola-medium.onnx",
    "it_m": "it_IT-riccardo-x_low.onnx",
}

# 1080x1080 square -- the social-media default
W, H = 1080, 1080
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
    # slow the finished voice (no clip, no warble) -- atempo preserves pitch
    tempo = subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw),
         "-af", f"atempo={TEMPO}", "-ar", "22050", str(out_wav)],
        capture_output=True,
    )
    raw.unlink(missing_ok=True)
    if tempo.returncode != 0 or not out_wav.exists():
        raise RuntimeError(f"tempo failed: {tempo.stderr.decode('utf-8', 'replace')[-400:]}")


def compose_video(wav: Path, caption: str, out_mp4: Path) -> None:
    """WAV + caption -> MP4 (navy card, amber waveform, wrapped caption)."""
    # ffmpeg drawtext doesn't auto-wrap; wrap ourselves and feed via textfile.
    wrapped = "\n".join(textwrap.wrap(caption, width=22)) or " "
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
        tf.write(wrapped)
        textfile = tf.name

    # loudnorm caps the true peak at -1.5 dB so it CANNOT clip (the v2 scratch was
    # +4.4 dB clipping). aresample=48000 first -- loudnorm silently upsamples otherwise.
    filtergraph = (
        f"[0:a]showwaves=s={W}x300:mode=cline:colors={WAVE}:rate=30[wave];"
        f"color=c={BG}:s={W}x{H}:r=30[bg];"
        f"[bg][wave]overlay=0:H-h-120[withwave];"
        f"[withwave]drawtext=fontfile={FONT}:textfile={textfile}:"
        f"fontcolor=white:fontsize=64:line_spacing=16:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-100[v]"
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
    Path(textfile).unlink(missing_ok=True)
    if proc.returncode != 0 or not out_mp4.exists():
        raise RuntimeError(f"ffmpeg failed: {proc.stderr.decode('utf-8', 'replace')[-800:]}")


def render(text: str, out_mp4: Path, voice: str = "en", caption: str | None = None) -> Path:
    """Full pipeline. Returns the MP4 path."""
    out_mp4 = Path(out_mp4)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "voice.wav"
        synth_voice(text, voice, wav)
        compose_video(wav, caption if caption is not None else text, out_mp4)
    return out_mp4


if __name__ == "__main__":
    import sys
    txt = sys.argv[1] if len(sys.argv) > 1 else "Bring your own hardware. The square never sleeps."
    v = sys.argv[2] if len(sys.argv) > 2 else "en"
    dest = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("out/demo.mp4")
    print(f"rendering -> {dest} (voice={v})")
    render(txt, dest, voice=v)
    print(f"done: {dest.resolve()}")
