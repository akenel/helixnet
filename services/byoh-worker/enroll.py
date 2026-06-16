"""
Enroll THIS machine as a node on the square.

Runs on the laptop (or any box). Probes its own tools/ram/gpu and registers with
the broker, so the Provider Console can show the no-surprises "what can this box
run" window with REAL data -- not a guess typed into a form.

Auth reuses the exact bearer token the dashboard already gets when you log in:
  1. open /compute/dashboard, log in
  2. grab your token (it's in the page after login)
  3. TOKEN=<paste> python enroll.py

Env:
  BROKER_URL   default http://localhost:9003
  TOKEN        bearer token (required)
  NODE_SLUG    default 'angel-laptop'
  NODE_LABEL   default "Angel's laptop"
"""

from __future__ import annotations

import os
import sys

import httpx

import capabilities as caps_mod

BROKER = os.getenv("BROKER_URL", "http://localhost:9003").rstrip("/")
TOKEN = os.getenv("TOKEN", "")
SLUG = os.getenv("NODE_SLUG", "angel-laptop")
LABEL = os.getenv("NODE_LABEL", "Angel's laptop")


def main() -> None:
    if not TOKEN:
        print("ERROR: set TOKEN (your dashboard bearer token)")
        sys.exit(1)
    caps = caps_mod.probe_node()
    gpu_blurb = "GPU" if caps.get("gpu") else "CPU"
    print(f"probed this box: {caps}")
    body = {"slug": SLUG, "label": LABEL, "gpu": gpu_blurb, "capabilities": caps}
    r = httpx.post(f"{BROKER}/api/v1/compute/nodes", json=body,
                   headers={"Authorization": f"Bearer {TOKEN}"}, timeout=30.0)
    if r.status_code == 409:
        print(f"node '{SLUG}' already registered (that's fine)")
        return
    if r.status_code >= 300:
        print(f"ERROR {r.status_code}: {r.text[:300]}")
        sys.exit(2)
    print(f"enrolled: {r.json()}")


if __name__ == "__main__":
    main()
