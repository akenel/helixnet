#!/usr/bin/env python3
"""
test-script = done -- the BYOH worker, proven repeatably.

Covers the whole chain we built, so "it works" is a command, not a memory:
  1. MUSCLE        text -> Piper -> ffmpeg -> a valid MP4 (the keystone recipe)
  2. DOOR GUARD    capability preflight: a CPU box RUNS voiceover, REFUSES image-gen
  3. THE WIRE      HTTP worker: POST /generate -> a valid MP4 comes back

Run (CPU-only, no GPU, ~5s):
  .venv/bin/python test_byoh.py
Exit 0 = all green. Exit 1 = something's red (and it says what).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

import capabilities as caps_mod
import render

HERE = Path(__file__).resolve().parent
PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"  [{PASS if ok else FAIL}] {name}" + (f" -- {detail}" if detail else ""))


def mp4_is_valid(path: Path) -> tuple[bool, str]:
    """ffprobe: real file, has video+audio, non-zero duration."""
    if not path.exists() or path.stat().st_size < 1000:
        return False, "file missing or too small"
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_name", "-of", "default=nw=1", str(path)],
        capture_output=True, text=True,
    ).stdout
    has_v = "h264" in out
    has_a = "aac" in out
    dur = next((float(l.split("=")[1]) for l in out.splitlines()
                if l.startswith("duration=")), 0.0)
    ok = has_v and has_a and dur > 0
    return ok, f"h264={has_v} aac={has_a} dur={dur:.1f}s"


def test_muscle() -> None:
    print("1. MUSCLE -- text -> voice -> mp4")
    out = HERE / "out" / "test-muscle.mp4"
    render.render("Test script proves the muscle works.", out, voice="en")
    ok, detail = mp4_is_valid(out)
    check("render produces a valid MP4", ok, detail)


def test_door_guard() -> None:
    print("2. DOOR GUARD -- capability preflight")
    caps = caps_mod.probe_node()
    check("probe reports tools+ram+gpu",
          all(k in caps for k in ("tools", "ram_mb", "gpu")), str(caps))
    # this CPU box should RUN voiceover
    ok_run, _ = caps_mod.preflight(caps_mod.VOICEOVER_REEL, caps)
    check("CPU box RUNS voiceover-reel", ok_run)
    # a weak 8GB no-GPU box must be REFUSED image-gen
    weak = {"tools": {"ffmpeg": True}, "ram_mb": 8192, "gpu": False}
    ok_refuse, reasons = caps_mod.preflight(caps_mod.STABLE_DIFFUSION, weak)
    check("8GB no-GPU box REFUSED image-gen", (not ok_refuse) and len(reasons) > 0,
          "; ".join(reasons))


def test_wire() -> None:
    print("3. THE WIRE -- HTTP worker round trip")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "worker:app",
         "--host", "127.0.0.1", "--port", "8801", "--log-level", "warning"],
        cwd=HERE,
    )
    try:
        up = False
        for _ in range(20):
            try:
                if httpx.get("http://127.0.0.1:8801/health", timeout=1).status_code == 200:
                    up = True
                    break
            except Exception:  # noqa: BLE001
                time.sleep(0.5)
        check("worker /health is up", up)
        if up:
            out = HERE / "out" / "test-wire.mp4"
            r = httpx.post("http://127.0.0.1:8801/generate",
                           json={"text": "The wire returns a file.", "voice": "en_gb"},
                           timeout=60)
            out.write_bytes(r.content)
            ok, detail = mp4_is_valid(out)
            check("POST /generate returns a valid MP4", r.status_code == 200 and ok,
                  f"HTTP {r.status_code} · {detail}")
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def main() -> int:
    print("=== BYOH worker test-script ===")
    test_muscle()
    test_door_guard()
    test_wire()
    n_fail = sum(1 for _, ok, _ in results if not ok)
    print(f"\n=== {len(results) - n_fail}/{len(results)} green ===")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
