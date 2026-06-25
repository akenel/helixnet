"""
Unit tests for the vision engine (src/services/vision) + its product consumer.

No network, no key, no server: we monkeypatch the ONE provider call
(`vision._call_provider`) and feed a real in-memory Pillow image (so the
image_intake normalize step runs for real). Runs on the host .venv in ms.

LOCKS the promises:
  - a clean JSON answer maps onto the product fields (via suggest_product_from_image)
  - a ```json fenced answer still parses
  - tags as a list collapse to a comma string; price/confidence coerce safely
  - a provider/transport failure degrades to blank + a note (no raise)
  - a non-JSON answer degrades the same way
  - junk bytes raise VisionImageError (route → 400)
  - the selected provider + hint reach the model
  - the engine is GENERIC: analyze_image(domain=...) works, and a second domain
    (LAB_REPORT) coerces its own fields — the generalization is real
"""
import sys
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.services import vision  # noqa: E402 — patch the engine seam here
from src.services import vision_product_analyzer as vpa  # noqa: E402
from src.services.vision import VisionImageError  # noqa: E402


def _img_bytes(w=800, h=600, color=(40, 120, 60)):
    buf = BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def _patch_provider(monkeypatch, text, *, model="test-model", capture=None):
    async def fake(provider, b64, prompt, mime="image/jpeg"):
        if capture is not None:
            capture.update(provider=provider, prompt=prompt, mime=mime)
        if isinstance(text, Exception):
            raise text
        return text, model
    monkeypatch.setattr(vision, "_call_provider", fake)


# ---- product consumer (back-compat wrapper) -------------------------------

async def test_clean_json_maps_to_fields(monkeypatch):
    _patch_provider(monkeypatch, (
        '{"name":"Green Passion CBD Gelato 5g","brand":"Green Passion",'
        '"category":"CBD","size":"5g","description":"Indoor CBD flower.",'
        '"tags":["cbd","flower","indoor"],"price_estimate":29.9,"confidence":0.84}'
    ))
    out = await vpa.suggest_product_from_image(_img_bytes(), provider="gemini")
    s = out["suggestion"]
    assert s["name"] == "Green Passion CBD Gelato 5g"
    assert s["category"] == "CBD"
    assert s["tags"] == "cbd, flower, indoor"        # list -> comma string
    assert float(s["price_estimate"]) == 29.9
    assert s["confidence"] == 0.84
    assert out["model"] == "test-model"
    assert out["note"] is None
    assert isinstance(out["elapsed_ms"], int)


async def test_code_fenced_json_still_parses(monkeypatch):
    _patch_provider(monkeypatch, '```json\n{"name":"Kanna Vape","confidence":0.5}\n```')
    out = await vpa.suggest_product_from_image(_img_bytes(), provider="gemini")
    assert out["suggestion"]["name"] == "Kanna Vape"
    assert out["note"] is None


async def test_bad_confidence_and_price_coerce(monkeypatch):
    _patch_provider(monkeypatch, '{"name":"x","price_estimate":"n/a","confidence":"high"}')
    s = (await vpa.suggest_product_from_image(_img_bytes(), provider="gemini"))["suggestion"]
    assert s["price_estimate"] is None
    assert s["confidence"] == 0.0


async def test_provider_failure_degrades_gracefully(monkeypatch):
    _patch_provider(monkeypatch, RuntimeError("no key"))
    out = await vpa.suggest_product_from_image(_img_bytes(), provider="gemini")
    assert out["suggestion"]["name"] == ""
    assert out["suggestion"]["confidence"] == 0.0
    assert out["note"] and "hand" in out["note"]
    assert out["model"] == ""


async def test_non_json_answer_degrades(monkeypatch):
    _patch_provider(monkeypatch, "I think this is some kind of CBD product, hard to say.")
    out = await vpa.suggest_product_from_image(_img_bytes(), provider="claude")
    assert out["suggestion"]["name"] == ""
    assert out["note"] and "hand" in out["note"]


async def test_junk_bytes_raise_image_error(monkeypatch):
    _patch_provider(monkeypatch, '{"name":"never reached"}')
    with pytest.raises(VisionImageError):
        await vpa.suggest_product_from_image(b"not an image", provider="gemini")


async def test_selected_provider_and_hint_reach_model(monkeypatch):
    cap = {}
    _patch_provider(monkeypatch, '{"name":"y","confidence":0.3}', capture=cap)
    await vpa.suggest_product_from_image(_img_bytes(), provider="claude", hint="grow lamp")
    assert cap["provider"] == "claude"
    assert "grow lamp" in cap["prompt"]            # hint reaches the model


# ---- the GENERIC engine + a second domain (the generalization) ------------

async def test_generic_analyze_image_returns_data_envelope(monkeypatch):
    _patch_provider(monkeypatch, '{"name":"Generic item","confidence":0.7}')
    out = await vision.analyze_image(_img_bytes(), domain=vision.PRODUCT, provider="gemini")
    assert out["data"]["name"] == "Generic item"
    assert out["data"]["confidence"] == 0.7
    assert out["note"] is None


async def test_lab_report_domain_coerces_its_own_fields(monkeypatch):
    _patch_provider(monkeypatch, (
        '{"sample_name":"Gelato Indoor","lab_name":"Labor Spiez","lab_number":"CH-2026-114",'
        '"lot":"B-7741","thc_pct":0.8,"cbd_pct":18.2,"tested_on":"2026-05-03","confidence":0.9}'
    ))
    out = await vision.analyze_image(_img_bytes(), domain=vision.LAB_REPORT, provider="gemini")
    d = out["data"]
    assert d["lab_number"] == "CH-2026-114"
    assert d["lot"] == "B-7741"
    assert d["thc_pct"] == 0.8
    assert d["cbd_pct"] == 18.2
    assert "name" not in d                          # lab domain has its own shape
    assert d["tested_on"] == "2026-05-03"


def test_domain_registry_has_product_and_lab():
    assert set(vision.DOMAINS) >= {"product", "lab_report"}
    assert vision.DOMAINS["product"] is vision.PRODUCT
