"""
BYOH -- the matchmaking layer (the missing wire).

A job must never land on a box that can't run it. So:

  RECIPE declares what it NEEDS   (manifest: tools, ram, gpu)
  NODE  declares what it HAS      (probe: tools present, ram, gpu)
  BROKER matches before dispatch  (preflight: needs <= has, else don't send)

This is preflight, not crash. The 8GB laptop trying to run a heavy job is
turned away at the door with a clear reason -- it never gets the job.
(The seal-inspection rule: check capability before you commit, not after.)
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field


# ---- what a NODE has (probed live on whatever machine the worker runs on) ----
def probe_node() -> dict:
    """Look at this actual machine and report what it can do."""
    return {
        "tools": {
            "ffmpeg": shutil.which("ffmpeg") is not None,
            "piper": os.path.exists(os.getenv("PIPER_BIN",
                     "/home/angel/repos/helixnet/.venv/bin/piper")),
            "puppeteer": _has_puppeteer(),
        },
        "ram_mb": _ram_mb(),
        "gpu": _has_gpu(),
    }


def _ram_mb() -> int:
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return 0


def _has_gpu() -> bool:
    return shutil.which("nvidia-smi") is not None


def _has_puppeteer() -> bool:
    node = shutil.which("node")
    if not node:
        return False
    return os.path.isdir("/home/angel/repos/helixnet/node_modules/puppeteer")


# ---- what a RECIPE needs (declared once, travels with the recipe) ----
@dataclass
class Manifest:
    name: str
    tools: list[str] = field(default_factory=list)   # e.g. ["ffmpeg", "piper"]
    min_ram_mb: int = 0
    needs_gpu: bool = False


# the recipe we just proved -- it needs only CPU tools
VOICEOVER_REEL = Manifest(name="voiceover-reel", tools=["ffmpeg", "piper"], min_ram_mb=1024)
# a future recipe that WOULD reject an 8GB box
STABLE_DIFFUSION = Manifest(name="image-gen", tools=["ffmpeg"], min_ram_mb=16384, needs_gpu=True)


# ---- the broker's decision (preflight) ----
def preflight(manifest: Manifest, caps: dict) -> tuple[bool, list[str]]:
    """Can this node run this recipe? Returns (ok, [reasons it can't])."""
    missing: list[str] = []
    for tool in manifest.tools:
        if not caps["tools"].get(tool):
            missing.append(f"missing tool: {tool}")
    if caps["ram_mb"] < manifest.min_ram_mb:
        missing.append(f"needs {manifest.min_ram_mb}MB RAM, node has {caps['ram_mb']}MB")
    if manifest.needs_gpu and not caps["gpu"]:
        missing.append("needs a GPU, node has none")
    return (len(missing) == 0, missing)


if __name__ == "__main__":
    caps = probe_node()
    print("THIS NODE:", caps)
    print()
    for m in (VOICEOVER_REEL, STABLE_DIFFUSION):
        ok, why = preflight(m, caps)
        verdict = "RUN" if ok else "REFUSE"
        print(f"[{verdict}] {m.name}" + ("" if ok else f"  -> {'; '.join(why)}"))
