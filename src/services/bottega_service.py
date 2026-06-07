# File: src/services/bottega_service.py
# Purpose: cv-to-bio recipe -- read a CV (PDF/Word/text) and build a Bottega profile
# (bio + tagline + skills + suggested categories) via the brain.
#
# Brain: prefer Ollama Turbo (capable model) via BH_OLLAMA_KEY for real quality;
# fall back to the local Ollama for dev. The bio is compressed to a tight band
# (CLAUDE.md: lean on Ollama summarization; bio 300-500 chars).

import json
import logging
import os
import re

import httpx

from src.llm import run_llm, turbo_or_local

logger = logging.getLogger("helix.bottega")


def slugify(s: str) -> str:
    """username/handle -> url-safe slug (lowercase, hyphens, alnum only)."""
    s = re.sub(r"\s+", "-", (s or "").strip().lower())
    s = re.sub(r"[^a-z0-9-]", "", s)
    return s.strip("-")[:80] or "user"

# Brain config -- DEFAULT model names. Backend selection (Turbo vs local Ollama,
# URL + auth) lives in src.llm.targets.turbo_or_local; here we own only the default
# model for each backend. A recipe may override the model per-job (see _brain_chat).
LOCAL_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama:latest")     # dev fallback
BIO_MODEL = os.getenv("LPCX_BIO_MODEL", "gpt-oss:120b")         # Turbo model; override per env


def extract_text(filename: str, data: bytes) -> str:
    """Pull plain text out of a CV. PDF -> PyMuPDF, .docx -> python-docx, else utf-8."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        import fitz  # PyMuPDF (lazy import; present after image rebuild)
        doc = fitz.open(stream=data, filetype="pdf")
        return "\n".join(page.get_text() for page in doc).strip()
    if name.endswith(".docx"):
        import io
        from docx import Document
        d = Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs).strip()
    # txt / fallback
    return data.decode("utf-8", errors="ignore").strip()


_SYSTEM = (
    "You build concise, warm professional profiles from a CV. "
    "Return STRICT JSON only, no prose."
)


def _prompt(cv_text: str, categories: list[str]) -> str:
    cats = ", ".join(categories) if categories else "(none provided)"
    return (
        "From this CV, produce a profile as JSON with EXACTLY these keys:\n"
        '  "bio": a warm first-person bio, 300-500 characters, no fluff;\n'
        '  "tagline": one punchy line, <= 80 chars;\n'
        '  "skills": array of 5-10 short skill tags (lowercase);\n'
        '  "categories": array of the BEST-MATCHING categories chosen ONLY from this '
        f"list: [{cats}]. If none fit well, return [].\n\n"
        f"CV:\n{cv_text[:8000]}"
    )


class BrainUnavailable(Exception):
    """The model backend failed (model not served, outage, timeout). Surfaced to the
    user as a friendly 'try again' -- never a raw 500 to the face."""


async def _brain_chat(system: str, user: str, json_mode: bool = False,
                      schema: dict | None = None, model: str | None = None,
                      model_local: str | None = None) -> str:
    """Shared brain call -- the seed of the procedure-as-code recipe runner. RESILIENT:
    routes through the single src.llm wrapper; if the pinned model isn't served (404) it
    falls back ONCE to the house brain; any total failure raises BrainUnavailable so the
    caller shows a friendly message instead of a 500.

    schema       = the outbound Service Interface (a JSON Schema), ENFORCED on the model.
    model        = the recipe's Turbo brain (DATA); default BIO_MODEL.
    model_local  = the local-Ollama fallback brain; default LOCAL_MODEL.
    A recipe can now name BOTH (turbo + local) so its model need not exist on both backends."""
    primary = turbo_or_local(model or BIO_MODEL, model_local or LOCAL_MODEL)
    house = turbo_or_local(BIO_MODEL, LOCAL_MODEL)
    try:
        res = await run_llm(user, target=primary, system=system, json_mode=json_mode, schema=schema)
        return res.text
    except httpx.HTTPStatusError as e:
        code = e.response.status_code if e.response is not None else 0
        # 404 = this backend doesn't serve the pinned model -> fall back to the house brain once.
        if code == 404 and primary.model != house.model:
            logger.warning("brain '%s' unavailable (404); falling back to house brain '%s'",
                           primary.model, house.model)
            try:
                res = await run_llm(user, target=house, system=system, json_mode=json_mode, schema=schema)
                return res.text
            except Exception as e2:  # noqa: BLE001
                raise BrainUnavailable(str(e2)) from e2
        raise BrainUnavailable(f"brain returned {code}") from e
    except (httpx.TimeoutException, httpx.TransportError) as e:
        raise BrainUnavailable(str(e)) from e


_TEASER_SYSTEM = (
    "You write the og:description for a La Piazza share card -- the line or two a stranger "
    "sees when this link is shared on WhatsApp, Telegram, or X. Make it irresistible: "
    "concrete, warm, and specific to THIS output, so the reader wants to click and make "
    "their own. Plain text only -- no hashtags, no quotation marks, no emojis, no markdown. "
    "One or two sentences, 200-300 characters, never more than 300."
)


async def share_teaser(title: str, content: str) -> str:
    """The meat & potatoes (Share-1): an irresistible 200-300 char teaser for the share
    card's og:description. Returns '' on any failure so the caller falls back (never blank)."""
    body = " ".join((content or "").split())[:2000]
    user = f"Title: {title}\n\nOutput:\n{body}\n\nWrite the share teaser now."
    try:
        text = await _brain_chat(_TEASER_SYSTEM, user)
    except Exception:  # noqa: BLE001
        logger.warning("share_teaser: brain call failed", exc_info=True)
        return ""
    return " ".join((text or "").split()).strip().strip('"').strip()[:300]


async def cv_to_bio(cv_text: str, categories: list[str] | None = None) -> dict:
    """Recipe: CV text -> {bio, tagline, skills[], categories[]}."""
    categories = categories or []
    content = await _brain_chat(_SYSTEM, _prompt(cv_text, categories), json_mode=True)
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("cv_to_bio: model returned non-JSON, salvaging")
        data = {"bio": content[:500], "tagline": "", "skills": [], "categories": []}
    # normalize
    return {
        "bio": (data.get("bio") or "").strip()[:1000],
        "tagline": (data.get("tagline") or "").strip()[:200],
        "skills": [str(s).strip().lower() for s in (data.get("skills") or [])][:12],
        "categories": [str(c).strip() for c in (data.get("categories") or [])
                       if not categories or c in categories][:6],
    }


_CV_SYSTEM = (
    "You are an expert CV writer. Rewrite ONLY from the source material -- never "
    "invent employers, dates, titles or credentials. Output clean Markdown."
)


async def generate_cv(cv_text: str, target_role: str = "", style: str = "concise") -> str:
    """Recipe: source CV (+ optional target role) -> polished, tailored CV in Markdown.
    Career pivots: re-frame TRANSFERABLE experience honestly toward the target and
    name the gaps to close -- it doesn't lie, it translates."""
    if target_role:
        aim = (f"Tailor it toward this target role/trade: '{target_role}'. Honestly "
               f"re-frame transferable experience toward it (don't fabricate), and end "
               f"with a short '## Bridge to {target_role}' section: what transfers, and "
               f"what to learn/certify to get there.")
    else:
        aim = "Polish and tighten it; keep it truthful."
    user = (
        f"Rewrite this CV as clean professional Markdown. {aim} Style: {style}.\n"
        "Sections: name + headline, ## Summary, ## Experience (each: role - org - dates, "
        "2-3 truthful bullets), ## Skills, ## Education. Do NOT invent facts.\n\n"
        f"SOURCE CV:\n{cv_text[:9000]}"
    )
    return (await _brain_chat(_CV_SYSTEM, user, json_mode=False)).strip()
