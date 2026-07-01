"""📮 Postcard scan tracking — the trackable-QR redirect for the head-shop campaign.

GET /r/{token}  →  logs the scan (which shop/card, when, rough where) and 302-redirects
                   the prospect on to the demo/landing.

v1 is deliberately SIMPLE (per the GTM discipline): a durable append-only JSONL scan log +
a logger line — NOT a dashboard. The token identifies the shop+card (its meaning lives in the
card-generation manifest); scanning it = a warm-lead signal you read off the log. A proper
`postcard_scans` DB table + a "who's warm" view can come later; this is the smallest thing
that hands you the signal.

Privacy (GDPR): we record only the token + timestamp + coarse ip/user-agent — enough to tie
scan → (later) signup by token. No device fingerprint, no precise location. Clean metadata.
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Where a scanned card sends the prospect. Card 3 ("scann und schau") → the live demo.
# Overridable per deployment via env so the same code serves sandbox/prod without a rebuild.
SCAN_REDIRECT_URL = os.environ.get(
    "POSTCARD_REDIRECT_URL", "https://sandbox-banco.lapiazza.app/pos"
)
# Durable append-only scan log (JSONL). One line per scan; grep-able; survives restarts.
SCAN_LOG_PATH = Path(os.environ.get("POSTCARD_SCAN_LOG", "/app/data/postcard_scans.jsonl"))


@router.get("/r/{token}")
async def track_postcard_scan(token: str, request: Request):
    """Log a postcard QR scan by token, then redirect to the demo. Never fails the redirect."""
    try:
        rec = {
            "token": token,
            "at": datetime.now(timezone.utc).isoformat(),
            "ip": (request.client.host if request.client else None),
            "ua": request.headers.get("user-agent", "")[:200],
            "ref": request.headers.get("referer", "")[:200],
        }
        SCAN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with SCAN_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        logger.info("POSTCARD-SCAN token=%s ip=%s", token, rec["ip"])
    except Exception:  # tracking must NEVER break the prospect's redirect
        logger.warning("postcard scan log failed for token=%s", token, exc_info=True)
    return RedirectResponse(url=SCAN_REDIRECT_URL, status_code=302)
