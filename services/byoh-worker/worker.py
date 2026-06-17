"""
BYOH worker -- the wire (HTTP contract).

POST /generate {text, voice?, caption?}  ->  an MP4 file
GET  /health                             ->  {"ok": true, ...}

This is the simplest way for a recipe to use the muscle: call a URL. The URL is
the only thing that changes when you move the worker laptop -> DigitalOcean ->
a gamer's GPU box. That's "bring your own hardware" in one variable.

(The queue/pull contract -- mirroring scripts/lpcx_worker.py against the RabbitMQ
broker -- is the production path. See README. This HTTP form is for the demo and
for direct point-to-point calls.)

Run:
  pip install fastapi uvicorn
  uvicorn worker:app --host 0.0.0.0 --port 8800
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import render

app = FastAPI(title="BYOH worker", version="0.1")


class Job(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    voice: str = Field("en", description="en | en_f | en_gb | it | it_m")
    caption: str | None = Field(None, description="on-screen text; defaults to spoken text")
    aspect: str = Field("square", description="square | portrait | landscape (legacy default = square)")
    karaoke: bool = Field(False, description="highlight words as spoken (Whisper-timed)")


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "skill": "text->voice->mp4",
        "voices": list(render.VOICES),
        "piper": render.PIPER_BIN.exists(),
        "font": render.FONT.exists(),
    }


@app.post("/generate")
def generate(job: Job) -> FileResponse:
    out = Path(tempfile.mkdtemp(prefix="byoh-")) / "out.mp4"
    try:
        render.render(job.text, out, voice=job.voice, caption=job.caption,
                      aspect=job.aspect, karaoke=job.karaoke)
    except Exception as e:  # noqa: BLE001 -- surface the tool error to the caller
        raise HTTPException(status_code=500, detail=str(e)[:500])
    return FileResponse(out, media_type="video/mp4", filename="byoh.mp4")
