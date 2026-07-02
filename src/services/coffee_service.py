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
EVENTS_KEY = os.environ.get("COFFEE_EVENTS_KEY", "")  # guards the events feed (for the Postino CRM sync)

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "kaffee_template.html"

LANG_CODE = {"de": "de", "fr": "fr", "it": "it", "en": "en"}

# Default landing intro per language (the recipe overrides per shop with a warm, pain-TUNED
# line — empathic peer voice, NOT a recited dossier). FR/IT/EN = drafts, native-review before mail.
DEFAULT_INTRO = {
    "de": ("Ich bin <b>Angel</b>. Ich hab dir die Karte geschickt — kein Verkaufsgespräch. Ich hab "
           "eine Kasse gebaut, die den langweiligen Teil übernimmt: <b>Belege, Mehrwertsteuer, "
           "Kassensturz</b>. Damit mehr Zeit für den Laden bleibt. Nicht SAP. Kein Spielzeug. Für "
           "Läden wie deinen."),
    "fr": ("Je suis <b>Angel</b>. Je t'ai envoyé la carte — pas de discours de vente. J'ai construit "
           "une caisse qui prend en charge la partie pénible : <b>reçus, TVA, clôture de caisse</b>. "
           "Pour qu'il te reste plus de temps pour le magasin. Pas SAP. Pas un jouet. Pour des "
           "magasins comme le tien."),
    "it": ("Sono <b>Angel</b>. Ti ho mandato la cartolina — niente discorso di vendita. Ho costruito "
           "una cassa che si prende la parte noiosa: <b>scontrini, IVA, chiusura cassa</b>. Così ti "
           "resta più tempo per il negozio. Non SAP. Non un giocattolo. Per negozi come il tuo."),
    "en": ("I'm <b>Angel</b>. I sent you the card — no sales pitch. I built a till that takes the "
           "boring part off your plate: <b>receipts, VAT, cashing out</b>. So you get more time for "
           "the shop. Not SAP. Not a toy. For shops like yours."),
}

# Chrome string catalog (fixed UI copy) per language. One layout, four fills (Banco's own i18n
# pattern). FR/IT/EN are solid drafts — NATIVE-REVIEW before a real mailing.
CHROME = {
    "de": {
        "C_GREETING": "Hallo", "C_HERO_SUB": "Du hast gescannt — gut. Trinken wir den Kaffee.",
        "C_VIDEO": "20 Sekunden: Angel sagt kurz Hoi", "C_VIDEO2": "(Video kommt hierhin)",
        "C_QUAL_H": "Passt das überhaupt zu dir?",
        "C_QUAL_LEAD": "Sei ehrlich — ich bin's auch. Das ist nicht für jeden.",
        "C_FIT_HEAD": "Passt, wenn …",
        "C_FIT_1": "du deinen Laden <b>selbst</b> führst",
        "C_FIT_2": "du <b>1–3 Läden</b> hast — oder ein paar Leute an der Kasse",
        "C_FIT_3": "du noch mit <b>Zettel, Stift und Taschenrechner</b> kämpfst",
        "C_FIT_4": "du abends über Belegen, MwSt und Kassensturz sitzt",
        "C_FIT_5": "du mehr Zeit für den <b>Laden</b> willst, nicht für Papierkram",
        "C_NOFIT_HEAD": "Passt (noch) nicht, wenn …",
        "C_NOFIT_1": "du schon ein <b>System oder eigene Software</b> hast, mit dem du zufrieden bist — dann brauchst du mich nicht. Ehrlich.",
        "C_NOFIT_2": "du eine grosse Kette mit IT-Abteilung bist und ein volles ERP willst — dann ist SAP dein Ding, nicht meins.",
        "C_FINEPRINT": "Kosten minimal. Training minimal. Kein Abo-Zwang, keine Fessel.",
        "C_CTA_H": "So machen wir's — was passt dir?",
        "C_CTA_P": "Kein Verkaufsdruck. Sag einfach, wie's dir am besten passt:",
        "C_OPT_CALL": "Ruf mich an", "C_OPT_SHOP": "Komm bei mir im Laden vorbei", "C_OPT_MEET": "Lass uns kurz zusammensitzen",
        "C_BTN": "Abschicken", "C_WRITEIN": "Kurz was dazu schreiben? →",
        "C_PLACEHOLDER": "Tel / Mail — oder einfach eine Notiz",
        "C_NOTE": "Ich hab deine Laden-Nummer schon. Kein Verkaufsdruck — wir schauen nur, ob's passt.",
        "C_FOOT": "Passt's nicht, kein Problem. Dann eben ein andermal.",
    },
    "fr": {
        "C_GREETING": "Salut", "C_HERO_SUB": "Tu as scanné — bien. Prenons ce café.",
        "C_VIDEO": "20 secondes : Angel dit bonjour", "C_VIDEO2": "(la vidéo arrive ici)",
        "C_QUAL_H": "Est-ce que ça te correspond, au fond ?",
        "C_QUAL_LEAD": "Sois honnête — moi aussi. Ce n'est pas pour tout le monde.",
        "C_FIT_HEAD": "Ça colle, si …",
        "C_FIT_1": "tu gères ton magasin <b>toi-même</b>",
        "C_FIT_2": "tu as <b>1 à 3 magasins</b> — ou quelques personnes en caisse",
        "C_FIT_3": "tu te bats encore avec <b>papier, stylo et calculette</b>",
        "C_FIT_4": "tu passes tes soirées sur les reçus, la TVA et la clôture de caisse",
        "C_FIT_5": "tu veux plus de temps pour le <b>magasin</b>, pas pour la paperasse",
        "C_NOFIT_HEAD": "Ça ne colle pas (encore), si …",
        "C_NOFIT_1": "tu as déjà un <b>système ou ton propre logiciel</b> qui te convient — alors tu n'as pas besoin de moi. Franchement.",
        "C_NOFIT_2": "tu es une grande chaîne avec un service informatique et tu veux un ERP complet — alors SAP est ton truc, pas le mien.",
        "C_FINEPRINT": "Coûts minimes. Formation minime. Pas d'abonnement forcé, pas de laisse.",
        "C_CTA_H": "On fait comment — qu'est-ce qui te va ?",
        "C_CTA_P": "Aucune pression. Dis-moi simplement ce qui te convient le mieux :",
        "C_OPT_CALL": "Appelle-moi", "C_OPT_SHOP": "Passe à mon magasin", "C_OPT_MEET": "Asseyons-nous un moment",
        "C_BTN": "Envoyer", "C_WRITEIN": "Envie d'écrire un mot ? →",
        "C_PLACEHOLDER": "Tél / e-mail — ou juste un mot",
        "C_NOTE": "J'ai déjà le numéro de ton magasin. Aucune pression — on regarde juste si ça colle.",
        "C_FOOT": "Si ça ne colle pas, pas de souci. Ce sera pour une autre fois.",
    },
    "it": {
        "C_GREETING": "Ciao", "C_HERO_SUB": "Hai scansionato — bene. Prendiamoci quel caffè.",
        "C_VIDEO": "20 secondi: Angel dice ciao", "C_VIDEO2": "(il video arriva qui)",
        "C_QUAL_H": "Fa davvero per te?",
        "C_QUAL_LEAD": "Sii onesto — lo sono anch'io. Non è per tutti.",
        "C_FIT_HEAD": "Va bene, se …",
        "C_FIT_1": "gestisci il negozio <b>di persona</b>",
        "C_FIT_2": "hai <b>1–3 negozi</b> — o qualche persona alla cassa",
        "C_FIT_3": "combatti ancora con <b>carta, penna e calcolatrice</b>",
        "C_FIT_4": "passi le sere su scontrini, IVA e chiusura cassa",
        "C_FIT_5": "vuoi più tempo per il <b>negozio</b>, non per le scartoffie",
        "C_NOFIT_HEAD": "Non fa per te (ancora), se …",
        "C_NOFIT_1": "hai già un <b>sistema o un software tuo</b> che ti soddisfa — allora non ti servo. Davvero.",
        "C_NOFIT_2": "sei una grande catena con un reparto IT e vuoi un ERP completo — allora SAP è cosa tua, non mia.",
        "C_FINEPRINT": "Costi minimi. Formazione minima. Nessun abbonamento forzato, nessun vincolo.",
        "C_CTA_H": "Come facciamo — cosa ti va?",
        "C_CTA_P": "Nessuna pressione. Dimmi solo cosa ti va meglio:",
        "C_OPT_CALL": "Chiamami", "C_OPT_SHOP": "Passa dal mio negozio", "C_OPT_MEET": "Sediamoci un attimo",
        "C_BTN": "Invia", "C_WRITEIN": "Vuoi scrivere due righe? →",
        "C_PLACEHOLDER": "Tel / e-mail — o solo una nota",
        "C_NOTE": "Ho già il numero del negozio. Nessuna pressione — guardiamo solo se va bene.",
        "C_FOOT": "Se non va, nessun problema. Sarà per un'altra volta.",
    },
    "en": {
        "C_GREETING": "Hi", "C_HERO_SUB": "You scanned — good. Let's have that coffee.",
        "C_VIDEO": "20 seconds: Angel says hi", "C_VIDEO2": "(video goes here)",
        "C_QUAL_H": "Is this even right for you?",
        "C_QUAL_LEAD": "Be honest — I am too. This isn't for everyone.",
        "C_FIT_HEAD": "A fit, if …",
        "C_FIT_1": "you run your shop <b>yourself</b>",
        "C_FIT_2": "you have <b>1–3 shops</b> — or a few people at the till",
        "C_FIT_3": "you're still fighting <b>paper, pen and a calculator</b>",
        "C_FIT_4": "you spend evenings on receipts, VAT and cashing out",
        "C_FIT_5": "you want more time for the <b>shop</b>, not paperwork",
        "C_NOFIT_HEAD": "Not a fit (yet), if …",
        "C_NOFIT_1": "you already have a <b>system or your own software</b> you're happy with — then you don't need me. Honestly.",
        "C_NOFIT_2": "you're a big chain with an IT department wanting a full ERP — then SAP is your thing, not mine.",
        "C_FINEPRINT": "Minimal cost. Minimal training. No subscription trap, no leash.",
        "C_CTA_H": "How should we do this — what works for you?",
        "C_CTA_P": "No pressure. Just tell me what suits you best:",
        "C_OPT_CALL": "Call me", "C_OPT_SHOP": "Come by my shop", "C_OPT_MEET": "Let's sit down briefly",
        "C_BTN": "Send", "C_WRITEIN": "Rather write a note? →",
        "C_PLACEHOLDER": "Phone / email — or just a note",
        "C_NOTE": "I've already got your shop's number. No pressure — we just see if it fits.",
        "C_FOOT": "If it's not a fit, no problem. Another time then.",
    },
}

# PoC roster: token -> shop identity. Personalize per fresh semi-qualified lead.
ROSTER = {
    "HS-ARTEMIS-COFFEE-0001": {
        "first_name": "Felix", "shop_name": "Artemis Kräuter & Düfte", "phone": "041 220 22 22",
        "logo": "/static/kaffee/assets/artemis-logo.png",
        "img": "/static/kaffee/assets/artemis-front.png", "language": "de",
    },
    # First real lead — Rudestore Headshop, Luzern (Postino #11 · opaque token, not enumerable). Scoped 2026-07-02.
    "VSWkHkZYVdst": {
        "first_name": "Stephan", "shop_name": "Rudestore Headshop", "phone": "",
        "logo": "", "img": "/static/kaffee/assets/rudestore-front.jpg", "language": "de",
        "landing_intro": (
            "Hoi Stephan — schön, dass du scannst. Ich war neulich bei dir im Laden (die Blättchen, "
            "und du hast mir die Rollen hinter der Theke gezeigt). Ich bin <b>Angel</b>. Ich bau eine "
            "Kasse, die den langweiligen Teil übernimmt — <b>Belege, MwSt, Kassensturz</b> — damit "
            "mehr Zeit für den Laden bleibt. Kein Verkaufsgespräch, nicht SAP, kein Spielzeug. "
            "Für Läden wie deinen."
        ),
    },
    # demo rows to verify FR/IT chrome renders (empty logo/img = clean)
    "HS-DEMO-FR-0001": {"first_name": "Luc", "shop_name": "CBD Léman", "phone": "021 000 00 00",
                        "logo": "", "img": "", "language": "fr"},
    "HS-DEMO-IT-0001": {"first_name": "Marco", "shop_name": "Canapa Ticino", "phone": "091 000 00 00",
                        "logo": "", "img": "", "language": "it"},
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


def _read_jsonl(p: Path) -> list:
    try:
        return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except Exception:
        return []


def read_events() -> dict:
    """All scan (visit) + lead (Ja) events, for the Postino CRM sync to ingest (join by token=ext_id)."""
    return {"visits": _read_jsonl(VISITS_LOG), "leads": _read_jsonl(LEADS_LOG)}


def render_landing(token: str):
    """Render the personalized, localized landing page for a token, or None if unknown."""
    shop = ROSTER.get(token)
    if not shop:
        return None
    lang = shop.get("language", "de")
    if lang not in CHROME:
        lang = "de"
    html = TEMPLATE.read_text(encoding="utf-8")
    fields = {
        "{{LANG}}": LANG_CODE.get(lang, "de"),
        "{{FIRST_NAME}}": shop["first_name"],
        "{{SHOP_NAME}}": shop["shop_name"],
        "{{SHOP_LOGO}}": shop.get("logo", ""),
        "{{SHOP_IMG}}": shop.get("img", ""),
        "{{TOKEN}}": token,
        "{{LANDING_INTRO}}": shop.get("landing_intro") or DEFAULT_INTRO.get(lang, DEFAULT_INTRO["de"]),
    }
    for ck, cv in CHROME[lang].items():
        fields["{{" + ck + "}}"] = cv
    for k, v in fields.items():
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


async def capture_lead(token: str, option: str = "", comment: str = "") -> dict:
    """Log a coffee lead + notify Angel (email + Telegram). Best-effort notify."""
    shop = ROSTER.get(token, {})
    name = shop.get("first_name", "?")
    sn = shop.get("shop_name", token)
    ph = shop.get("phone", "")
    visits = visit_count(token)
    opt_label = {"call": "Ruf mich an", "shop": "Im Laden vorbeikommen",
                 "meet": "Zusammensitzen"}.get(option, option or "—")
    rec = {"token": token, "at": _now(), "first_name": name, "shop_name": sn,
           "phone": ph, "option": option, "comment": comment, "visits": visits}
    _append(LEADS_LOG, rec)
    subject = f"☕ Antwort von {name} / {sn} — {opt_label}"
    body = (f"<h2>{name} hat geantwortet: {opt_label}</h2><p><b>{name}</b> — {sn}</p>"
            f"<p>Wunsch: <b>{opt_label}</b></p><p>Laden-Tel: {ph}</p>"
            f"<p>Kommentar: {comment or '—'}</p>"
            f"<p>Karte: {token} · Seitenbesuche: {visits}</p>")
    tg = (f"☕ <b>{name} — {sn}</b>\nWunsch: {opt_label}\nTel: {ph}\n"
          f"Kommentar: {comment or '—'}\nKarte: {token} · Besuche: {visits}")
    await asyncio.to_thread(_send_email, subject, body)
    await _send_telegram(tg)
    return rec
