#!/usr/bin/env python3
"""LPCX remote worker -- the genie, on a leash.

A standalone, dumb worker that lends a machine to the square. It does NOT decide
what to run: it pulls a fully-resolved job from the broker (system + prompt already
filled in), runs it through a brain, and posts the result back. It holds only two
secrets -- a revocable node token and a scoped brain key -- and talks to nobody but
the broker (out) and the model. No inbound ports. No DB. No app code.

Loop:  GET  {BROKER}/api/v1/compute/worker/next?node={NODE}   (X-Node-Token)
       -> call the brain with the handed-down system+prompt
       POST {BROKER}/api/v1/compute/worker/result             (X-Node-Token)

Run (env-configured):
  BROKER_URL=https://bottega.lapiazza.app \
  LPCX_NODE=do-staging-0 \
  LPCX_NODE_TOKEN=*** \
  LPCX_BRAIN_KEY=***          # the worker's OWN scoped Ollama Turbo key
  python3 lpcx_worker.py

CLAUDE.md rule 11: Python-first, asyncio + httpx.
"""
import asyncio
import logging
import os
import sys

import httpx

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s lpcx.worker: %(message)s")
log = logging.getLogger("lpcx.worker")

BROKER = os.getenv("BROKER_URL", "https://bottega.lapiazza.app").rstrip("/")
NODE = os.getenv("LPCX_NODE", "do-staging-0")
NODE_TOKEN = os.getenv("LPCX_NODE_TOKEN", "")
BRAIN_KEY = os.getenv("LPCX_BRAIN_KEY", "")                      # worker's own scoped key
BRAIN_URL = os.getenv("LPCX_BRAIN_URL", "https://ollama.com").rstrip("/")
BRAIN_MODEL = os.getenv("LPCX_BRAIN_MODEL", "gpt-oss:120b")
POLL_SECONDS = float(os.getenv("LPCX_POLL_SECONDS", "4"))
VERIFY_TLS = os.getenv("LPCX_VERIFY_TLS", "1") != "0"           # broker uses real LE cert


async def run_brain(client: httpx.AsyncClient, system: str, prompt: str,
                    json_mode: bool) -> tuple[str, int]:
    """Call the brain. Returns (output_text, tokens_used)."""
    body = {
        "model": BRAIN_MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": prompt}],
        "stream": False,
    }
    if json_mode:
        body["format"] = "json"
    r = await client.post(f"{BRAIN_URL}/api/chat", json=body,
                          headers={"Authorization": f"Bearer {BRAIN_KEY}"}, timeout=180.0)
    r.raise_for_status()
    data = r.json()
    out = data.get("message", {}).get("content", "")
    tokens = int(data.get("eval_count", 0)) + int(data.get("prompt_eval_count", 0))
    return out, tokens


async def tick(client: httpx.AsyncClient) -> bool:
    """One pull-run-report cycle. Returns True if a job was handled."""
    hdr = {"X-Node-Token": NODE_TOKEN}
    r = await client.get(f"{BROKER}/api/v1/compute/worker/next",
                         params={"node": NODE}, headers=hdr, timeout=30.0)
    r.raise_for_status()
    job = r.json().get("job")
    if not job:
        return False

    jid = job["job_id"]
    log.info(f"picked up {job.get('template')} (CJ-{job.get('job_number')}) id={jid[:8]}")
    try:
        out, tokens = await run_brain(client, job["system"], job["prompt"],
                                      job.get("json_mode", False))
        await client.post(f"{BROKER}/api/v1/compute/worker/result", headers=hdr,
                          json={"job_id": jid, "output": out, "tokens": tokens}, timeout=30.0)
        log.info(f"done {jid[:8]} -- {tokens} tok, {len(out)} chars returned")
    except Exception as e:  # noqa: BLE001
        log.exception("job failed; reporting error to broker")
        await client.post(f"{BROKER}/api/v1/compute/worker/result", headers=hdr,
                          json={"job_id": jid, "error": str(e)[:200]}, timeout=30.0)
    return True


async def main():
    if not NODE_TOKEN or not BRAIN_KEY:
        log.error("LPCX_NODE_TOKEN and LPCX_BRAIN_KEY are required")
        sys.exit(1)
    log.info(f"worker up: node={NODE} broker={BROKER} model={BRAIN_MODEL} poll={POLL_SECONDS}s")
    async with httpx.AsyncClient(verify=VERIFY_TLS) as client:
        while True:
            try:
                handled = await tick(client)
            except Exception as e:  # noqa: BLE001 -- never die on a transient broker/network blip
                log.warning(f"tick error (will retry): {e}")
                handled = False
            await asyncio.sleep(0 if handled else POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
