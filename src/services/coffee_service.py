"""☕ Book-a-coffee lead capture for the head-shop campaign (PoC, happy-path e2e).

Flow: QR (per shop) → GET /kaffee/{token} renders the PERSONALIZED landing page (the token
IS the shop's identity) and logs the visit (repeat visits = a "mulling it" hot signal).
One-tap „Ja" → POST /kaffee/ja logs the lead + notifies Angel (email to ecolution + Telegram
ping). Durable JSONL logs; notifications are best-effort and NEVER fail the visitor's action.

v1 roster is a small in-code map (4-at-a-time precision campaign — no big store needed). The
notification rails mirror camper_email_service / camper_telegram_service. Refine content later.
"""
import asyncio
import json
import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("COFFEE_DATA_DIR", "/app/data"))
VISITS_LOG = DATA_DIR / "coffee_visits.jsonl"
LEADS_LOG = DATA_DIR / "coffee_leads.jsonl"

NOTIFY_EMAIL = os.environ.get("COFFEE_NOTIFY_EMAIL", "ecolution.gmbh@gmail.com")
SMTP_HOST = os.environ.get("COFFEE_SMTP_HOST", "mailhog")     # sandbox = MailHog; prod = Resend
SMTP_PORT = int(os.environ.get("COFFEE_SMTP_PORT", "1025"))
SMTP_USER = os.environ.get("COFFEE_SMTP_USER", "")
SMTP_PASS = os.environ.get("COFFEE_SMTP_PASS", "")
SMTP_FROM = os.environ.get("COFFEE_SMTP_FROM", "BANCO <noreply@lapiazza.app>")
TG_TOKEN = os.environ.get("BANCO_TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.environ.get("COFFEE_TELEGRAM_CHAT_ID", "")

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "kaffee_template.html"

# Default landing intro (the recipe overrides this per shop with a warm, pain-TUNED line —
# empathic peer voice, NOT a recited dossier about him).
DEFAULT_INTRO = (
    "Ich bin <b>Angel</b>. Ich hab dir die Karte geschickt &mdash; kein Verkaufsgespr&auml;ch. "
    "Ich hab eine Kasse gebaut, die den langweiligen Teil &uuml;bernimmt: <b>Belege, "
    "Mehrwertsteuer, Kassensturz</b>. Damit mehr Zeit f&uuml;r den Laden bleibt. Nicht SAP. "
    "Kein Spielzeug. F&uuml;r L&auml;den wie deinen."
)

# PoC roster: token -> shop identity. Personalize per fresh semi-qualified lead.
ROSTER = {
    "HS-ARTEMIS-COFFEE-0001": {
        "first_name": "Felix",
        "shop_name": "Artemis Kräuter & Düfte",
        "phone": "041 220 22 22",
        "logo": "/static/kaffee/assets/artemis-logo.png",
        "img": "/static/kaffee/assets/artemis-front.png",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append(path: Path, rec: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        logger.warning("coffee log append failed", exc_info=True)


def log_visit(token: str, ip, ua) -> None:
    _append(VISITS_LOG, {"token": token, "at": _now(), "ip": ip, "ua": (ua or "")[:200]})


def visit_count(token: str) -> int:
    """Crude repeat-visit count for the 'hot lead' flag."""
    try:
        return sum(1 for ln in VISITS_LOG.read_text(encoding="utf-8").splitlines() if f'"{token}"' in ln)
    except Exception:
        return 0


def render_landing(token: str):
    """Render the personalized landing page for a token, or None if unknown."""
    shop = ROSTER.get(token)
    if not shop:
        return None
    html = TEMPLATE.read_text(encoding="utf-8")
    for k, v in {
        "{{FIRST_NAME}}": shop["first_name"],
        "{{SHOP_NAME}}": shop["shop_name"],
        "{{SHOP_LOGO}}": shop.get("logo", ""),
        "{{SHOP_IMG}}": shop.get("img", ""),
        "{{TOKEN}}": token,
        "{{LANDING_INTRO}}": shop.get("landing_intro") or DEFAULT_INTRO,
    }.items():
        html = html.replace(k, v)
    return html


def _send_email(subject: str, html_body: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = NOTIFY_EMAIL
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            if SMTP_USER:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_FROM, [NOTIFY_EMAIL], msg.as_string())
        logger.info("coffee lead email sent to %s", NOTIFY_EMAIL)
        return True
    except Exception:
        logger.warning("coffee email failed", exc_info=True)
        return False


async def _send_telegram(text: str) -> bool:
    if not TG_TOKEN or not TG_CHAT:
        logger.info("[TELEGRAM STUB] %s", text)
        return True
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML"},
            )
        return r.status_code == 200
    except Exception:
        logger.warning("coffee telegram failed", exc_info=True)
        return False


async def capture_lead(token: str, contact: str) -> dict:
    """Log a coffee lead + notify Angel (email + Telegram). Best-effort notify."""
    shop = ROSTER.get(token, {})
    name = shop.get("first_name", "?")
    sn = shop.get("shop_name", token)
    ph = shop.get("phone", "")
    visits = visit_count(token)
    rec = {"token": token, "at": _now(), "first_name": name, "shop_name": sn,
           "phone": ph, "contact": contact, "visits": visits}
    _append(LEADS_LOG, rec)
    subject = f"☕ Einladung angefragt: {name} / {sn}"
    body = (f"<h2>Will eine Einladung zum Banco-Treffen</h2><p><b>{name}</b> — {sn}</p>"
            f"<p>Laden-Tel: {ph}</p><p>Notiz/Kontakt: {contact or '—'}</p>"
            f"<p>Karte: {token} · Seitenbesuche: {visits}</p>")
    tg = (f"☕ <b>Einladung angefragt</b>\n{name} — {sn}\nTel: {ph}\n"
          f"Notiz: {contact or '—'}\nKarte: {token} · Besuche: {visits}")
    await asyncio.to_thread(_send_email, subject, body)
    await _send_telegram(tg)
    return rec
