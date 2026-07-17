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

Write a SCANNABLE product description for a shop catalog using ONLY facts stated on that page.

FORMAT — exactly this shape, nothing else:
<one plain sentence, max 20 words, saying what it is>
• <Spec>: <value>
• <Spec>: <value>
(3 to 6 bullets, max 8 words each)

Bullet the details that IDENTIFY it and let someone confirm they have the right pack: size/dimensions,
leaf or piece count, material, strength/%, volume, weight, colour/variant, and pack/tier pricing
(single vs display box) when the page states it. Most useful first.

RULES:
- Plain English. No marketing words ("premium", "high quality", "perfect for").
- Never invent. If the page doesn't state it, leave it out.
- A cashier reads this in 3 seconds standing up. No paragraphs, no essay.

If the page is not clearly about this product, or states no usable details, reply with exactly: NONE
"""

# BYO-brain: the model is DATA and the caller names it (src/llm). Turbo when BH_OLLAMA_KEY is set,
# else the local fallback — same pair the translation service uses.
DESC_MODEL = "gpt-oss:120b"
LOCAL_MODEL = "tinyllama:latest"

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
            target=turbo_or_local(DESC_MODEL, LOCAL_MODEL),
            system=_SYSTEM,
        )
        out = (res.text or "").strip()
        # reasoning models leak <think> blocks — strip before use (same as the recipe runner)
        out = re.sub(r"<think>.*?</think>", "", out, flags=re.S).strip()
        # The model reliably produces the BULLETS but not reliably the LINE BREAKS — it returns
        # "…resolution. • Capacity: 400 g • Readability: 0.01 g" all on one line, which renders as
        # another wall. Don't re-prompt for formatting a regex can guarantee: collapse whitespace,
        # then force every bullet onto its own line.
        out = _WS.sub(" ", out)
        out = re.sub(r"\s*[•·]\s*", "\n• ", out).strip()
        out = re.sub(r"\n{2,}", "\n", out)
        if not out or out.upper().startswith("NONE") or len(out) < 25:
            return ""
        return out[:1200]
    except Exception as e:
        # WARNING, not info: this returns "" on failure, and an empty description is indistinguishable
        # from "the page had nothing to say". A silent fallback that looks like a real answer is how a
        # broken call hides — a mis-called turbo_or_local() swallowed EVERY description here until the
        # log was turned up. If enrichment is dead, the log must say so.
        logger.warning(f"describe_from_page FAILED for {name[:40]!r}: {type(e).__name__}: {str(e)[:90]}")
        return ""


async def tidy_operator_note(note: str) -> str:
    """The operator's OWN note -> a description. Their words, tidied. Never re-imagined.

    Angel: "sometimes I'm taking the notes, and that could be just as good and valuable for a
    description — that's our secret sauce." Exactly: a note like "34 leaves, ultra thin, blue pack" is
    a person who picked the pack up and read it. That beats any scrape. So this only reshapes it into
    the house format — it must never add a fact they didn't write, and never drop one they did.

    Short enough to be a note (not a pasted page); the caller routes long text to describe_from_page.
    Returns "" only if there's nothing there.
    """
    n = _WS.sub(" ", (note or "").strip())
    if len(n) < 12:
        return ""
    # Already shaped? Leave it completely alone.
    if "•" in n or "\n" in note:
        return note.strip()[:1200]
    try:
        from src.llm import run_llm, turbo_or_local
        res = await run_llm(
            "Reshape this shop-floor note into a catalog description.\n\n"
            f"THE NOTE: {note.strip()[:900]}\n\n"
            "RULES — this is a human's own observation, so:\n"
            "- Use ONLY the facts in the note. Add nothing. Drop nothing.\n"
            "- If it names specs, bullet them: one short lead line, then '• Spec: value' lines.\n"
            "- If it's one plain remark, just return it cleanly as one line.\n"
            "- Keep the writer's language (do NOT translate).\n"
            "- No marketing words. Reply with the description only.",
            target=turbo_or_local(DESC_MODEL, LOCAL_MODEL),
            system="You tidy a shop worker's product note. You never invent or remove facts.",
        )
        out = re.sub(r"<think>.*?</think>", "", (res.text or ""), flags=re.S).strip()
        out = _WS.sub(" ", out)
        out = re.sub(r"\s*[•·]\s*", "\n• ", out).strip()
        out = re.sub(r"\n{2,}", "\n", out)
        # If the model gave us less than the human wrote, trust the human.
        return (out or n)[:1200] if len(out) >= 12 else n[:1200]
    except Exception as e:
        logger.warning(f"tidy_operator_note FAILED — keeping the operator's words verbatim: {str(e)[:70]}")
        return n[:1200]      # their note is ALWAYS better than nothing
