"""BL-131 — read a product page's BODY and write the description that proves what the thing is.

The page's own tags give us the title, the picture and the price for free (`_page_product_facts`), but
`og:description` is SEO fluff — on the real GIZEH page it reads "GIZEH - Papers Large Slim Extra Fine
Black 34 - CBD Oil (Cannabidiol) – Cannabis Products". Useless. The details that actually IDENTIFY the
product — 33 leaves, ultra-thin rice paper, watermark for even burn, natural sugar gum — are in the
page BODY, in prose, where only a reader can get them.

Angel's rule, and the reason this exists: the description is the field that matters most. A name and a
price he can type himself in ten seconds; what he can't type is the spec that lets anyone say "yes,
that is definitely the one". It's also what makes the postcards real.

Guardrails:
- The model is told to EXTRACT, never to imagine. If the page doesn't say it, it doesn't go in.
- Return "" (not a guess) when the page isn't about a product / is unreadable.
- Never raises: enrichment must never break an import.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You extract product facts from a shop's web page for a Swiss head-shop catalog. "
    "You ONLY report what the page actually states. You never invent, infer, or embellish. "
    "If the page does not state a fact, you omit it. If the page is not about this product, you say so."
)

_PROMPT = """Here is the text of a shop page for this product:

PRODUCT: {name}

PAGE TEXT:
{text}

Write ONE paragraph (max 60 words) describing this product for a shop catalog, using ONLY facts stated
on that page. Lead with the details that IDENTIFY it and let someone confirm they have the right one:
material, dimensions, leaf/piece count, size/variant, strength/%, volume, weight, and any pack/tier
info (e.g. single vs 50-box). Plain English. No marketing language, no "premium quality", no invented
claims.

If the page is not clearly about this product, or states no usable details, reply with exactly: NONE
"""

_TAG_RE = re.compile(r"<(script|style|noscript|svg|nav|footer|header)[^>]*>.*?</\1>", re.I | re.S)
_ANY_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def html_to_text(html: str, limit: int = 6000) -> str:
    """Strip a page to readable prose. Crude on purpose: a real parser buys us nothing here — the model
    tolerates messy text, and every dependency is a thing that can break a deploy."""
    s = _TAG_RE.sub(" ", html or "")
    s = _ANY_TAG.sub(" ", s)
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
          .replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">"))
    return _WS.sub(" ", s).strip()[:limit]


async def describe_from_page(name: str, page_html: str) -> str:
    """-> a spec-led description, or "" when the page can't honestly support one."""
    text = html_to_text(page_html)
    if len(text) < 120:
        return ""
    try:
        from src.llm import run_llm, turbo_or_local
        res = await run_llm(
            _PROMPT.format(name=(name or "")[:160], text=text),
            target=turbo_or_local(),
            system=_SYSTEM,
        )
        out = (res.text or "").strip()
        # reasoning models leak <think> blocks — strip before use (same as the recipe runner)
        out = re.sub(r"<think>.*?</think>", "", out, flags=re.S).strip()
        out = _WS.sub(" ", out)
        if not out or out.upper().startswith("NONE") or len(out) < 25:
            return ""
        return out[:1200]
    except Exception as e:
        logger.info(f"describe_from_page failed for {name[:40]!r}: {str(e)[:70]}")
        return ""
