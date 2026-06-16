# BYOH worker — proof of concept

**Bring Your Own Hardware.** A recipe runs on whatever box is capable of it. The
brain (Ollama Turbo, or any key) is shared; the *muscle* runs on a member's own
machine, brokered by our own platform. This is "our own Vast" — we never rent
RunPod/Vast, the GPUs come from enrolled member hardware on our rails.

Proven on one laptop (16GB, no GPU), June 16 2026, costing nothing.

## The pieces

| File | Role | Lego |
|------|------|------|
| `render.py` | the **muscle** | text → Piper voice → ffmpeg audiogram → MP4 |
| `worker.py` | the **wire** (HTTP) | `POST /generate` → MP4 back. Simplest direct call. |
| `capabilities.py` | the **door guard** | recipe-needs vs node-has; refuse mismatches |
| `broker_demo.py` | the **dispatcher** | enroll → queue → hand out → collect artifact (mirrors LPCX) |
| `render_worker.py` | the **node** (pull) | sibling of `scripts/lpcx_worker.py`, render skill |

Only **one brick needs a GPU** in the real product (Stable Diffusion). Everything
here is CPU-only and runs on the laptop today.

## Run the whole network on one machine

```bash
cd services/byoh-worker
python3 -m venv .venv && .venv/bin/pip install fastapi "uvicorn[standard]" pydantic python-multipart httpx

# 1. broker (the dispatcher)
BYOH_RESULTS=out/results .venv/bin/uvicorn broker_demo:app --host 127.0.0.1 --port 8810 &

# 2. node (pulls jobs, renders on THIS box's hardware)
BROKER_URL=http://127.0.0.1:8810 BYOH_NODE=laptop-0 BYOH_NODE_TOKEN=demo-token \
  .venv/bin/python render_worker.py &

# 3. submit a job
curl -s -X POST http://127.0.0.1:8810/api/v1/compute/jobs \
  -H "Content-Type: application/json" \
  -d '{"recipe":"voiceover-reel","text":"Hello from my own private Vast.","voice":"en"}'

# 4. poll /api/v1/compute/jobs/<id> until status=done; artifact is the MP4 path
```

Direct HTTP form (no broker):

```bash
.venv/bin/uvicorn worker:app --host 127.0.0.1 --port 8800 &
curl -X POST http://127.0.0.1:8800/generate -H "Content-Type: application/json" \
  -d '{"text":"One shot, one file.","voice":"en_gb"}' -o out.mp4
```

## Voices

`en` (US Lessac) · `en_gb` (Alba) · `it` (Paola) · `it_m` (Riccardo)

## Moving the node off the laptop (the BYOH payoff)

The node code does **not** change. Only the environment does:

- **Tools path** — set `PIPER_BIN`, `VOICES_DIR`, `FONT` for the new box (or bake
  them into a container image).
- **Broker URL** — point `BROKER_URL` at the real Bottega broker.
- **Caddy** — the broker (not the node) sits behind Caddy at an HTTPS URL. The node
  makes only *outbound* calls — no inbound ports, like `lpcx_worker.py`.
- **Auth** — `X-Node-Token` here is a shared demo token; the real broker issues a
  per-node revocable token at enrollment. Keycloak vouches for the *human*; the
  token vouches for the *box*.

## How this maps onto the real broker

`broker_demo.py` mirrors the LPCX contract (`scripts/lpcx_worker.py`):
`worker/next` + `worker/result`. The two things media adds on top of the existing
text-only brain network:

1. **Artifact return** — result is a *file*, not text (multipart upload here; an
   object-store URL in production).
2. **Hardware accounting** — credit a node for jobs/GPU-seconds run (the incentive
   that brings member GPUs online), parallel to brain-token accounting.

Both are wiring, not new invention.
```
