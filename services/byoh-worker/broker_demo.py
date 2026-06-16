"""
BYOH demo broker -- the dispatcher (stand-in for the Bottega compute broker).

Mirrors the LPCX pull contract (scripts/lpcx_worker.py) but for RENDER jobs that
return a FILE instead of text. Everything here is in-memory and dumb on purpose:
it exists to prove the loop runs on ONE laptop, end to end, with nobody outside.

Contract (same shape as the real broker, so the worker ports over unchanged):
  POST /api/v1/compute/nodes/enroll   {node, recipe, caps}   -> preflight, accept/refuse
  POST /api/v1/compute/jobs           {recipe, text, voice}  -> enqueue, returns job_id
  GET  /api/v1/compute/worker/next?node=N   (X-Node-Token)   -> next eligible job | null
  POST /api/v1/compute/worker/result  (multipart: job_id + artifact file | error)
  GET  /api/v1/compute/jobs/{id}                              -> status + artifact path

Auth: shared node token (X-Node-Token), exactly like lpcx_worker.py. The real
broker swaps this for a per-node revocable token issued at enrollment.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel

import capabilities as caps_mod

NODE_TOKEN = os.getenv("BYOH_NODE_TOKEN", "demo-token")
RESULTS = Path(os.getenv("BYOH_RESULTS", "out/results"))
RESULTS.mkdir(parents=True, exist_ok=True)

# the recipes this broker knows how to dispatch (the fixed parts-lists)
RECIPES = {m.name: m for m in (caps_mod.VOICEOVER_REEL, caps_mod.STABLE_DIFFUSION)}

app = FastAPI(title="BYOH demo broker", version="0.1")

JOBS: dict[str, dict] = {}        # job_id -> job
QUEUE: list[str] = []             # job_ids waiting
NODES: dict[str, dict] = {}       # node -> {caps, recipes:set}


def _auth(token: str | None) -> None:
    if token != NODE_TOKEN:
        raise HTTPException(status_code=401, detail="bad node token")


class Enroll(BaseModel):
    node: str
    recipe: str
    caps: dict


class JobIn(BaseModel):
    recipe: str = "voiceover-reel"
    text: str
    voice: str = "en"
    caption: str | None = None


@app.get("/health")
def health() -> dict:
    return {"ok": True, "queued": len(QUEUE), "nodes": list(NODES), "recipes": list(RECIPES)}


@app.post("/api/v1/compute/nodes/enroll")
def enroll(body: Enroll, x_node_token: str = Header(None)) -> dict:
    """A box offers itself for a recipe. Broker preflights BEFORE accepting."""
    _auth(x_node_token)
    manifest = RECIPES.get(body.recipe)
    if not manifest:
        raise HTTPException(404, f"unknown recipe {body.recipe}")
    ok, missing = caps_mod.preflight(manifest, body.caps)
    if not ok:
        return {"accepted": False, "recipe": body.recipe, "reasons": missing}
    node = NODES.setdefault(body.node, {"caps": body.caps, "recipes": set()})
    node["caps"] = body.caps
    node["recipes"].add(body.recipe)
    return {"accepted": True, "recipe": body.recipe}


@app.post("/api/v1/compute/jobs")
def submit(body: JobIn) -> dict:
    if body.recipe not in RECIPES:
        raise HTTPException(404, f"unknown recipe {body.recipe}")
    jid = uuid.uuid4().hex
    JOBS[jid] = {"job_id": jid, "status": "queued", "artifact": None, **body.model_dump()}
    QUEUE.append(jid)
    return {"job_id": jid}


@app.get("/api/v1/compute/worker/next")
def next_job(node: str, x_node_token: str = Header(None)) -> dict:
    """Hand out the next job this node is ENROLLED (=capable) for. Else null."""
    _auth(x_node_token)
    eligible = NODES.get(node, {}).get("recipes", set())
    for i, jid in enumerate(QUEUE):
        if JOBS[jid]["recipe"] in eligible:
            QUEUE.pop(i)
            JOBS[jid]["status"] = "running"
            j = JOBS[jid]
            return {"job": {"job_id": jid, "recipe": j["recipe"],
                            "text": j["text"], "voice": j["voice"], "caption": j["caption"]}}
    return {"job": None}


@app.post("/api/v1/compute/worker/result")
async def result(
    job_id: str = Form(...),
    error: str | None = Form(None),
    artifact: UploadFile | None = File(None),
    x_node_token: str = Header(None),
) -> dict:
    _auth(x_node_token)
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "unknown job")
    if error:
        job["status"] = "error"
        job["error"] = error
        return {"ok": True}
    dest = RESULTS / f"{job_id}.mp4"
    dest.write_bytes(await artifact.read())
    job["status"] = "done"
    job["artifact"] = str(dest)
    return {"ok": True, "artifact": str(dest)}


@app.get("/api/v1/compute/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "unknown job")
    return {"job_id": job_id, "status": job["status"],
            "artifact": job.get("artifact"), "error": job.get("error")}
