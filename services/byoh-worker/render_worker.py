"""
BYOH render worker -- the genie, on a leash (render flavor).

A faithful sibling of scripts/lpcx_worker.py. Same loop, same leash. The ONLY
difference: where the brain worker calls an LLM and returns text, this one calls
the local muscle (render.py) and returns a FILE. That's the whole "second skill."

Loop:  enroll once (announce caps -> broker preflights)
       GET  {BROKER}/api/v1/compute/worker/next?node={NODE}   (X-Node-Token)
       -> render() locally (Piper + ffmpeg, this machine's hardware)
       POST {BROKER}/api/v1/compute/worker/result  (multipart MP4)   (X-Node-Token)

No inbound ports. No DB. No app code. It talks only to the broker (out) and its
own tools (local). Bring Your Own Hardware: this same file runs on the laptop, on
DigitalOcean, or on a gamer's box -- only BROKER_URL and the node's tools change.

Run:
  BROKER_URL=http://127.0.0.1:8810 BYOH_NODE=laptop-0 BYOH_NODE_TOKEN=demo-token \
  python render_worker.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path

import httpx

import capabilities as caps_mod
import render

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s byoh.worker: %(message)s")
log = logging.getLogger("byoh.worker")

BROKER = os.getenv("BROKER_URL", "http://127.0.0.1:8810").rstrip("/")
NODE = os.getenv("BYOH_NODE", "laptop-0")
NODE_TOKEN = os.getenv("BYOH_NODE_TOKEN", "demo-token")
RECIPE = os.getenv("BYOH_RECIPE", "voiceover-reel")
POLL_SECONDS = float(os.getenv("BYOH_POLL_SECONDS", "2"))


async def enroll(client: httpx.AsyncClient) -> bool:
    """Announce what this box has; broker decides if it's good enough."""
    caps = caps_mod.probe_node()
    r = await client.post(f"{BROKER}/api/v1/compute/nodes/enroll",
                          headers={"X-Node-Token": NODE_TOKEN},
                          json={"node": NODE, "recipe": RECIPE, "caps": caps}, timeout=30.0)
    r.raise_for_status()
    res = r.json()
    if not res.get("accepted"):
        log.error(f"REFUSED for {RECIPE}: {res.get('reasons')}")
        return False
    log.info(f"enrolled node={NODE} recipe={RECIPE} caps={caps}")
    return True


async def tick(client: httpx.AsyncClient) -> bool:
    """One pull-render-report cycle. Returns True if a job was handled."""
    hdr = {"X-Node-Token": NODE_TOKEN}
    r = await client.get(f"{BROKER}/api/v1/compute/worker/next",
                         params={"node": NODE}, headers=hdr, timeout=30.0)
    r.raise_for_status()
    job = r.json().get("job")
    if not job:
        return False

    jid = job["job_id"]
    log.info(f"picked up {job['recipe']} id={jid[:8]} text={job['text'][:40]!r}")
    try:
        out = Path(tempfile.mkdtemp(prefix="byoh-")) / "out.mp4"
        # the muscle runs HERE, on this machine's own hardware
        render.render(job["text"], out, voice=job.get("voice", "en"),
                      caption=job.get("caption"))
        with open(out, "rb") as fh:
            await client.post(f"{BROKER}/api/v1/compute/worker/result", headers=hdr,
                              data={"job_id": jid},
                              files={"artifact": ("out.mp4", fh, "video/mp4")}, timeout=120.0)
        log.info(f"done {jid[:8]} -- returned {out.stat().st_size} bytes")
    except Exception as e:  # noqa: BLE001
        log.exception("job failed; reporting error to broker")
        await client.post(f"{BROKER}/api/v1/compute/worker/result", headers=hdr,
                          data={"job_id": jid, "error": str(e)[:200]}, timeout=30.0)
    return True


async def main() -> None:
    log.info(f"worker up: node={NODE} broker={BROKER} recipe={RECIPE} poll={POLL_SECONDS}s")
    async with httpx.AsyncClient() as client:
        if not await enroll(client):
            sys.exit(2)
        while True:
            try:
                handled = await tick(client)
            except Exception as e:  # noqa: BLE001 -- never die on a transient blip
                log.warning(f"tick error (will retry): {e}")
                handled = False
            await asyncio.sleep(0 if handled else POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
