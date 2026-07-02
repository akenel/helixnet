"""☕ Book-a-coffee routes — the QR destination for the head-shop handshake card.

GET  /kaffee/{token}  → personalized landing page (logs the visit; repeat = hot signal)
POST /kaffee/ja       → log the lead + notify Angel (email ecolution + Telegram), thank-you
"""
import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from src.services import coffee_service as cs

logger = logging.getLogger(__name__)
router = APIRouter()

_THANKS = (
    "<!doctype html><html lang=de><head><meta charset=utf-8>"
    "<meta name=viewport content='width=device-width,initial-scale=1'><title>Merci</title></head>"
    "<body style=\"font-family:'Helvetica Neue',Arial,sans-serif;background:#faf6f0;margin:0\">"
    "<div style='max-width:460px;margin:64px auto;padding:0 22px;text-align:center;color:#2a2a2a'>"
    "<div style='height:4px;width:44px;background:#8B5E34;border-radius:2px;margin:0 auto 22px'></div>"
    "<h1 style='font-size:27px;font-weight:800'>Merci. 🐺</h1>"
    "<p style='font-size:15px;color:#3a3a3a;margin-top:14px'>Ich meld mich bei dir &mdash; kein "
    "Verkaufsdruck, versprochen. Der Kaffee geht auf mich.</p>"
    "<p style='font-size:13px;color:#8a7c6a;margin-top:26px'>&mdash; Angel &middot; BANCO &middot; La Piazza</p>"
    "</div></body></html>"
)

_UNKNOWN = (
    "<!doctype html><html lang=de><head><meta charset=utf-8>"
    "<meta name=viewport content='width=device-width,initial-scale=1'></head>"
    "<body style=\"font-family:'Helvetica Neue',Arial,sans-serif;background:#faf6f0;margin:0\">"
    "<div style='max-width:460px;margin:64px auto;padding:0 22px;text-align:center;color:#2a2a2a'>"
    "<h1>Kaffee?</h1><p>Diese Karte kenn ich (noch) nicht &mdash; aber der Kaffee gilt trotzdem. "
    "Schreib mir: ecolution.gmbh@gmail.com</p></div></body></html>"
)


@router.get("/kaffee/{token}", response_class=HTMLResponse)
async def kaffee_page(token: str, request: Request):
    html = cs.render_landing(token)
    if html is None:
        return HTMLResponse(_UNKNOWN, status_code=404)
    cs.log_visit(token, request.client.host if request.client else None,
                 request.headers.get("user-agent", ""))
    return HTMLResponse(html)


@router.post("/kaffee/ja", response_class=HTMLResponse)
async def kaffee_ja(request: Request, token: str = Form(...), contact: str = Form("")):
    try:
        await cs.capture_lead(token, contact.strip())
    except Exception:
        logger.warning("coffee capture_lead failed for %s", token, exc_info=True)
    return HTMLResponse(_THANKS)
