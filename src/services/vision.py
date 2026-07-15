"""
Vision — the engine's "read a photo into structured data" capability.

Sibling to src/llm (model-as-data): this is **vision-as-data**. ONE place a photo
is sent to a multimodal model; the model is config, and the *task* is data — a
`VisionDomain` (a prompt + a coercion). New consumers (POS catalog, ISOTTO print,
La Piazza listings, seed-to-sale lab reports) register a domain; they don't write
another integration. The engine never gets a customer name (estate rule).

    analyze_image(raw, content_type, *, domain=PRODUCT) -> {
        "data": {...},          # the domain's coerced fields
        "provider", "model", "elapsed_ms", "note"
    }

Brain selection (model-agnostic, one env var):
    BANCO_VISION_PROVIDER   gemini | claude | ollama   (default: gemini)
    BH_GOOGLE_API_KEY       Gemini (AI Studio) key — auth via x-goog-api-key header
    GEMINI_VISION_MODEL     default gemini-2.5-flash
    ANTHROPIC_API_KEY · CLAUDE_VISION_MODEL (default claude-sonnet-4-6)
    OLLAMA_URL · OLLAMA_VISION_MODEL (default llama3.2-vision)

Reached over plain httpx (REST) — no extra SDK in the app image. Pillow-optional:
normalizes the phone shot when present, sends the raw bytes when it isn't (same
graceful degradation as the product-photo upload path). NEVER raises for model/
transport problems — returns a blank result + a human `note` so the caller's UI
degrades to plain typing. Bad-image bytes raise VisionImageError (→ a 400).

Rule #11 (Python first): asyncio + httpx, deterministic parsing.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Callable

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0


class VisionImageError(ValueError):
    """The upload wasn't a usable image. Defined HERE (no Pillow import) so a route
    can import + catch it WITHOUT pulling in Pillow, which may not be in the image
    yet — the route turns this into a clean 400."""


@dataclass(frozen=True)
class VisionDomain:
    """A vision *task* as data: how to ask, and how to shape the answer.

    prompt  — instructs the model to return ONLY a JSON object with known keys.
    coerce  — maps the model's raw JSON dict onto the domain's tidy field dict
              (defaults, type coercion, list→string, clamping). Pure function.
    """
    name: str
    prompt: str
    coerce: Callable[[dict], dict]
    intake: str = "product"   # image-intake preset: "product" (1024px) or "slip" (1600px, document)


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


# ---------------------------------------------------------------------------
# Provider adapters — (image b64, prompt, mime) -> (raw model text, model name).
# They raise on misconfig/transport/API error; analyze_image degrades gracefully.
# ---------------------------------------------------------------------------

async def _gemini(b64: str, prompt: str, mime: str = "image/jpeg") -> tuple[str, str]:
    key = os.getenv("BH_GOOGLE_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not key:
        raise RuntimeError("BH_GOOGLE_API_KEY not set")
    model = os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": mime, "data": b64}},
        ]}],
        "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"},
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.post(url, headers={"x-goog-api-key": key}, json=body)
        r.raise_for_status()
        data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"], model


async def _claude(b64: str, prompt: str, mime: str = "image/jpeg") -> tuple[str, str]:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    model = os.getenv("CLAUDE_VISION_MODEL", "claude-sonnet-4-6")
    body = {
        "model": model,
        "max_tokens": 600,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}},
            {"type": "text", "text": prompt},
        ]}],
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
            json=body,
        )
        r.raise_for_status()
        data = r.json()
    return data["content"][0]["text"], model


async def _ollama(b64: str, prompt: str, mime: str = "image/jpeg") -> tuple[str, str]:  # noqa: ARG001
    base = os.getenv("OLLAMA_URL", "http://ollama:11434").rstrip("/")
    model = os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision")
    headers = {}
    key = os.getenv("BH_OLLAMA_KEY", "")
    if key:  # Turbo-style bearer, if a hosted vision model is in use
        base = os.getenv("OLLAMA_TURBO_URL", "https://ollama.com").rstrip("/")
        headers["Authorization"] = f"Bearer {key}"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt, "images": [b64]}],
        "stream": False, "format": "json", "options": {"temperature": 0.2},
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.post(f"{base}/api/chat", headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    return data["message"]["content"], model


_PROVIDERS = {"gemini": _gemini, "claude": _claude, "ollama": _ollama}


async def _call_provider(provider: str, b64: str, prompt: str, mime: str = "image/jpeg") -> tuple[str, str]:
    """Dispatch to one provider. Split out so tests monkeypatch exactly here."""
    fn = _PROVIDERS.get(provider)
    if fn is None:
        raise RuntimeError(f"unknown vision provider: {provider}")
    return await fn(b64, prompt, mime)


def _normalize(raw: bytes, content_type: str, preset: str = "product") -> tuple[str, str]:
    """Phone shot -> (base64, mime). Pillow-optional: normalize when present
    (orient/shrink/strip EXIF — faster + cheaper tokens), else send raw.

    `preset` picks the intake profile: "product" (1024px) for an item photo, "slip"
    (1600px, document) for a delivery-note scan where the small print must stay legible."""
    mime = content_type if (content_type or "").startswith("image/") else "image/jpeg"
    try:
        from src.services.image_intake import process, PRODUCT, SLIP, ImageIntakeError
        presets = {"product": PRODUCT, "slip": SLIP}
        try:
            return _b64(process(raw, presets.get(preset, PRODUCT)).main), "image/jpeg"
        except ImageIntakeError as e:
            raise VisionImageError(str(e))
    except ImportError:
        logger.warning("Pillow not in image — sending photo to the model un-normalized.")
        if not raw:
            raise VisionImageError("empty image upload")
        return _b64(raw), mime


def _parse_json(text: str) -> dict:
    """Pull a JSON object out of model text (tolerates a ```json fence)."""
    raw = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1)
    else:
        brace = re.search(r"\{.*\}", raw, re.DOTALL)
        if brace:
            raw = brace.group(0)
    return json.loads(raw)  # may raise — caller catches


# ---- shared coercion helpers (used by domain coercers) --------------------

def _s(obj: dict, key: str) -> str:
    return str(obj.get(key) or "").strip()


def _opt(obj: dict, key: str) -> str | None:
    v = _s(obj, key)
    return v or None


def _tags(obj: dict, key: str = "tags") -> str | None:
    t = obj.get(key)
    if isinstance(t, list):
        t = ", ".join(str(x).strip() for x in t if str(x).strip())
    t = (str(t).strip() if t else "")
    return t or None


def _num(obj: dict, key: str):
    v = obj.get(key)
    try:
        return round(float(v), 2) if v not in (None, "", "null", "n/a", "N/A") else None
    except (TypeError, ValueError):
        return None


def _confidence(obj: dict) -> float:
    try:
        return max(0.0, min(1.0, float(obj.get("confidence", 0.0))))
    except (TypeError, ValueError):
        return 0.0


async def analyze_image(
    raw: bytes,
    content_type: str = "image/jpeg",
    *,
    domain: VisionDomain,
    hint: str | None = None,
    provider: str | None = None,
) -> dict:
    """Read a photo into the domain's structured fields.

    Returns {"data": {...}, "provider", "model", "elapsed_ms", "note"}. NEVER raises
    for model/transport problems (blank data + a `note`). Raises VisionImageError for
    un-decodable bytes when Pillow is present."""
    provider = (provider or os.getenv("BANCO_VISION_PROVIDER", "gemini")).lower()
    b64, mime = _normalize(raw, content_type, domain.intake)   # may raise VisionImageError
    prompt = domain.prompt if not hint else f"{domain.prompt}\nExtra hint: {hint.strip()}"

    started = time.perf_counter()
    try:
        text, model = await _call_provider(provider, b64, prompt, mime)
    except Exception as e:  # noqa: BLE001 — any provider/transport error degrades
        logger.warning("vision provider %s failed (%s): %s", provider, domain.name, e)
        return {"data": domain.coerce({}), "provider": provider, "model": "",
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
                "note": f"AI unavailable ({type(e).__name__}) — enter it by hand."}
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    try:
        data = domain.coerce(_parse_json(text))
        note = None
    except Exception as e:  # noqa: BLE001 — model returned non-JSON
        logger.warning("vision parse failed (%s): %.120s", e, text)
        data, note = domain.coerce({}), "AI answer wasn't readable — enter it by hand."

    return {"data": data, "provider": provider, "model": model,
            "elapsed_ms": elapsed_ms, "note": note}


# ===========================================================================
# DOMAINS — the registry of vision tasks (data, not code). Add an entry to give
# a new surface a vision brain; no new integration.
# ===========================================================================

# --- product (POS catalog / ISOTTO / La Piazza listings) — WIRED via POS ----
_PRODUCT_PROMPT = (
    "You are a Swiss head-shop / CBD point-of-sale assistant. Look at the photo of "
    "a single retail product and return ONLY a JSON object (no prose, no code fence) "
    "with these keys:\n"
    '  "name"          short shelf name (brand + product), e.g. "Green Passion CBD Blüten Gelato 5g"\n'
    '  "brand"         the brand if visible, else ""\n'
    '  "category"      one of: CBD, Flower, Vape, Accessories, Grow, Drinks, Cosmetics, Other\n'
    '  "size"          pack size / weight if visible (e.g. "5g", "10ml"), else ""\n'
    '  "description"   one tidy sentence a customer would read\n'
    '  "tags"          comma-separated keywords for search\n'
    '  "price_estimate" a number in CHF if you can guess from the type, else null\n'
    '  "confidence"    0.0–1.0, how sure you are about the name\n'
    "Read any visible text on the label literally. If unsure, use empty string / null "
    "and a low confidence. Output JSON only."
)


def _coerce_product(obj: dict) -> dict:
    return {
        "name": _s(obj, "name"), "brand": _s(obj, "brand"),
        "category": _opt(obj, "category"), "size": _s(obj, "size"),
        "description": _opt(obj, "description"), "tags": _tags(obj),
        "price_estimate": _num(obj, "price_estimate"), "confidence": _confidence(obj),
    }


PRODUCT = VisionDomain(name="product", prompt=_PRODUCT_PROMPT, coerce=_coerce_product)


# --- lab report (seed-to-sale traceability) — DEFINED, not yet wired ---------
# The Swiss CBD compliance differentiator: photograph a lab certificate, drop the
# numbers into farm→batch→lab_test→trace_event. Domain is ready; a consumer
# (endpoint + write into the trace models) is the next brick.
_LAB_REPORT_PROMPT = (
    "You are reading a cannabis/CBD laboratory analysis certificate (Swiss). Return "
    "ONLY a JSON object (no prose, no code fence) with these keys:\n"
    '  "sample_name"   the product/sample name on the report\n'
    '  "lab_name"      the testing laboratory\n'
    '  "lab_number"    the report / certificate number\n'
    '  "lot"           lot / batch identifier\n'
    '  "thc_pct"       total THC as a number (percent), else null\n'
    '  "cbd_pct"       total CBD as a number (percent), else null\n'
    '  "tested_on"     test date as YYYY-MM-DD if present, else ""\n'
    '  "confidence"    0.0–1.0\n'
    "Read numbers and identifiers literally. Unsure → null / empty + low confidence. JSON only."
)


def _coerce_lab_report(obj: dict) -> dict:
    return {
        "sample_name": _s(obj, "sample_name"), "lab_name": _s(obj, "lab_name"),
        "lab_number": _s(obj, "lab_number"), "lot": _s(obj, "lot"),
        "thc_pct": _num(obj, "thc_pct"), "cbd_pct": _num(obj, "cbd_pct"),
        "tested_on": _s(obj, "tested_on"), "confidence": _confidence(obj),
    }


LAB_REPORT = VisionDomain(name="lab_report", prompt=_LAB_REPORT_PROMPT, coerce=_coerce_lab_report)


# --- delivery slip (goods receipt) — the "read the Lieferschein" brain --------
# Photograph the supplier's delivery note; the model returns the header + every product
# line as structured JSON. The receiving endpoint then trigram-matches each line against
# the live catalogue so the operator just confirms. Uses the SLIP intake (1600px, keeps
# the small print legible). See docs/BANCO-RECEIVING-GOODS-RECEIPT-SPEC.md.
_DELIVERY_SLIP_PROMPT = (
    "You are reading a supplier DELIVERY NOTE (Lieferschein / bon de livraison / bolla di "
    "consegna) for a Swiss shop. Return ONLY a JSON object (no prose, no code fence) with:\n"
    '  "supplier"          the sender / supplier company name if visible, else ""\n'
    '  "delivery_note_no"  the delivery-note number if visible, else ""\n'
    '  "date"              the document/delivery date as YYYY-MM-DD if present, else ""\n'
    '  "lines"             an ARRAY, one object per PRODUCT line, each:\n'
    '        "description"  the article text exactly as printed (keep its language)\n'
    '        "quantity"     the quantity as a number (else 1)\n'
    '        "unit_price"   unit price as a number if the slip shows prices, else null\n'
    '  "confidence"        0.0-1.0 overall\n'
    "Include EVERY product line. SKIP header rows, subtotals, totals, VAT/MwSt and shipping "
    "lines. Read text and numbers literally; missing field -> \"\" or null. Output JSON only."
)


def _coerce_delivery_slip(obj: dict) -> dict:
    lines = []
    raw_lines = obj.get("lines")
    if isinstance(raw_lines, list):
        for it in raw_lines:
            if not isinstance(it, dict):
                continue
            desc = _s(it, "description")
            if not desc:
                continue
            qty = _num(it, "quantity")
            lines.append({
                "description": desc,
                "quantity": qty if (qty and qty > 0) else 1,
                "unit_price": _num(it, "unit_price"),
            })
    return {
        "supplier": _s(obj, "supplier"),
        "delivery_note_no": _s(obj, "delivery_note_no"),
        "date": _s(obj, "date"),
        "lines": lines,
        "confidence": _confidence(obj),
    }


DELIVERY_SLIP = VisionDomain(
    name="delivery_slip", prompt=_DELIVERY_SLIP_PROMPT,
    coerce=_coerce_delivery_slip, intake="slip",
)


# Registry — look a domain up by name (e.g. from an endpoint ?domain= param).
DOMAINS = {d.name: d for d in (PRODUCT, LAB_REPORT, DELIVERY_SLIP)}
