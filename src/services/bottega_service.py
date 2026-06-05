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

logger = logging.getLogger("helix.bottega")


def slugify(s: str) -> str:
    """username/handle -> url-safe slug (lowercase, hyphens, alnum only)."""
    s = re.sub(r"\s+", "-", (s or "").strip().lower())
    s = re.sub(r"[^a-z0-9-]", "", s)
    return s.strip("-")[:80] or "user"

# Brain config -- Turbo if a key is set, else local Ollama.
BH_OLLAMA_KEY = os.getenv("BH_OLLAMA_KEY", "")
OLLAMA_TURBO_URL = os.getenv("OLLAMA_TURBO_URL", "https://ollama.com")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
LOCAL_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama:latest")
BIO_MODEL = os.getenv("LPCX_BIO_MODEL", "gpt-oss:120b")  # Turbo model; override per env


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


async def _brain_chat(system: str, user: str, json_mode: bool = False) -> str:
    """Shared brain call -- the seed of the procedure-as-code recipe runner.
    Every template recipe routes through here. Turbo if BH_OLLAMA_KEY, else local."""
    import httpx
    use_turbo = bool(BH_OLLAMA_KEY)
    url = (OLLAMA_TURBO_URL if use_turbo else OLLAMA_URL).rstrip("/")
    model = BIO_MODEL if use_turbo else LOCAL_MODEL
    headers = {"Authorization": f"Bearer {BH_OLLAMA_KEY}"} if use_turbo else {}
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "stream": False,
    }
    if json_mode:
        body["format"] = "json"
    async with httpx.AsyncClient(timeout=180.0) as client:
        r = await client.post(f"{url}/api/chat", json=body, headers=headers)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "")


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
