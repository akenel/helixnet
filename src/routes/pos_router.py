# File: src/routes/pos_router.py
"""
POS (Point of Sale) API Router for Felix's Artemis Store.
Handles products, transactions, scanning, and checkout.

Sprint 4: Added HTML interface routes for Pam's POS system.
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Body
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4
from typing import Optional
from pathlib import Path

from src.db.database import get_db_session
from src.services.fiscal_regime import resolve_regime
from src.services.store_settings_seeding import get_active_store_settings
from src.services.catalog_enrichment import mint_internal_ean13
from src.services.lp_publish import publish_product
from src.services.square_bridge import SquareBridgeError
from src.services.vat_resolver import line_vat, split_vat
from src.services.pricing import tier_unit_price
from src.db.models import (
    ProductModel,
    ProductBarcodeModel,
    ProductImageModel,
    ReferenceProductModel,
    PosStockMovementModel,
    TransactionModel,
    LineItemModel,
    UserModel,
    StoreSettingsModel,
    CustomerModel,
    ShiftSessionModel,
    SessionStatus,
    TransactionStatus,
    PaymentMethod,
    BacklogItemModel,
    BacklogItemType,
    BacklogPriority,
    CashShiftModel,
    CashShiftStatus,
    CashMovementModel,
    CashMovementKind,
    CustomerModel,
    CreditTransactionModel,
    CreditTransactionType,
    SupplierModel,
    ReorderItemModel,
    REORDER_REASONS,
    REORDER_STATUSES,
)
from src.core.constants import HelixApplication
from src.services.cash_shift_service import (
    expected_cash, close_result, denoms_total, money, denoms_for,
)
from pydantic import BaseModel
from src.schemas.pos_schema import (
    ProductCreate,
    ProductUpdate,
    ProductRead,
    ProductSuggestResponse,
    TransactionCreate,
    TransactionRead,
    TransactionWithItems,
    LineItemCreate,
    LineItemRead,
    BarcodeScanRequest,
    BarcodeScanResponse,
    CheckoutRequest,
    SaleCreate,
    RefundRequest,
    DailySummary,
    StoreSettingsRead,
    StoreSettingsUpdate,
    ReceivingRequest,
    ReceivingResponse,
    ReceivingLineResult,
    SupplierCreate,
    SupplierUpdate,
    SupplierRead,
)
from src.schemas.customer_schema import CustomerQRScanResponse
# Real Keycloak authentication with RBAC
from src.core.keycloak_auth import (
    require_roles,
    require_any_pos_role,
    require_admin,
    require_manager_or_admin,
)
from src.core.config import get_settings
# REFERENCE ONLY: Mock auth kept for comparison
# from src.core.mock_auth import get_mock_user as get_current_user

logger = logging.getLogger(__name__)

# API Router (JSON endpoints)
router = APIRouter(prefix="/api/v1/pos", tags=["POS"])

# HTML Router (Web UI pages for Pam)
html_router = APIRouter(tags=["🖥️ POS Web UI"])

# Setup Jinja2 templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))
# Real build stamp in the POS status bar (version + the SHA actually deployed).
from src.build_info import get_version, get_git_sha, get_build_date_short, get_build_date  # noqa: E402
templates.env.globals["app_version"] = get_version()
templates.env.globals["git_sha"] = get_git_sha()
templates.env.globals["build_date"] = get_build_date_short()  # BL-010: '29 Jun' freshness (POS instance)
templates.env.globals["build_date_iso"] = get_build_date()  # BL-012: offset-carrying ISO → client localizes to device tz
import os  # noqa: E402
# Env code (SBX/STG/PRD) for the status-bar pill. POS pages render via THIS templates instance
# (not main.py's), so the app_env global must be set here too. Read os.environ directly.
templates.env.globals["app_env"] = os.environ.get("HX_ENVIRONMENT", "")
# The POS realm the BROWSER login leg must hit — same env-driven value the server validates
# tokens against (settings.POS_REALM). Was hardcoded 'kc-pos-realm-dev' in login.html/base.html,
# which broke the per-env realm split (the app accepted -stg tokens but sent login to -dev).
templates.env.globals["pos_realm"] = get_settings().POS_REALM

# Shop timezone for "what counts as today" on daily reports. Sales timestamps are stored
# tz-aware (UTC); the report day-window must be built in the SHOP's local day, or late-night
# sales get attributed to the wrong calendar day. Felix's shop is Lucerne; env-overridable.
from zoneinfo import ZoneInfo  # noqa: E402
SHOP_TZ = ZoneInfo(os.environ.get("HX_SHOP_TZ", "Europe/Zurich"))


# ================================================================
# POS CONFIGURATION ENDPOINT
# ================================================================

async def _tenant_rate_table(db: AsyncSession) -> list[dict]:
    """The active tenant's N-rate VAT table for split_vat — the store's own edited table when it has
    one, else the CH config default (POS_VAT_RATE / _REDUCED).

    Piece C wiring: the VAT-computing call sites feed this to split_vat instead of None. For a CH shop
    with NULL store_settings.vat_rates, resolve_regime returns the exact A/B config table split_vat
    used before, so the money path is BYTE-IDENTICAL to today (golden lock). Wrapped so a DB blip
    degrades to the CH default and never turns VAT math into a 500.
    """
    try:
        store = await get_active_store_settings(db)
    except Exception:
        logger.warning("rate-table: store read failed; CH fallback", exc_info=True)
        store = None
    return resolve_regime(store)["vat_rates"]


def _validate_and_serialize_vat_rates(rows) -> str:
    """Validate an N-rate VAT MENU and return it as a JSON string for store_settings.vat_rates.

    Rules (mirror the client-side editor, enforced here too — defense in depth): a list of ≥1 row;
    each row has a non-blank code + a numeric rate in 0–100; codes are unique; exactly one row is
    the default/catch-all. Raises HTTPException(422) on any violation so a bad payload never persists
    a table that would mis-book VAT. Rates are stringified (like _rate_table_for) for a clean payload.
    """
    import json
    if not isinstance(rows, list) or not rows:
        raise HTTPException(status_code=422, detail="At least one VAT rate is required.")
    out, codes, defaults = [], set(), 0
    for r in rows:
        if not isinstance(r, dict):
            raise HTTPException(status_code=422, detail="Malformed VAT rate row.")
        code = str(r.get("code") or "").strip()
        if not code:
            raise HTTPException(status_code=422, detail="Every VAT rate needs a code.")
        if code in codes:
            raise HTTPException(status_code=422, detail=f"Duplicate VAT rate code: {code}")
        codes.add(code)
        try:
            rate = Decimal(str(r.get("rate")))
        except Exception:
            raise HTTPException(status_code=422, detail=f"VAT rate for {code} must be a number.")
        if rate < 0 or rate > 100:
            raise HTTPException(status_code=422, detail=f"VAT rate for {code} must be 0–100.")
        is_default = bool(r.get("default", False))
        defaults += 1 if is_default else 0
        out.append({"code": code, "label": str(r.get("label") or code),
                    "rate": str(rate), "default": is_default})
    if defaults != 1:
        raise HTTPException(status_code=422, detail="Exactly one VAT rate must be the default.")
    return json.dumps(out)


@router.get("/config")
async def get_pos_config(db: AsyncSession = Depends(get_db_session)):
    """
    Get POS configuration including VAT rate, currency, locale.
    This is public (no auth required) so the UI can load it on init.

    VAT rates are updated annually:
    - 2024: 7.7%
    - 2025: 8.1%

    PHASE 0 (Go-Italian) adds the additive `regime` key sourced per-tenant from Store #1.
    The pre-existing scalar keys are UNCHANGED (still from config). The regime source is
    wrapped in a MANDATORY try/except → resolve_regime(None): this endpoint was DB-less,
    so the new DB read must never turn a blip into a 500 — it degrades to CH.
    """
    settings = get_settings()
    store_name = "Banco POS"
    try:
        store = await get_active_store_settings(db)  # Store #1, may be None
        regime = resolve_regime(store)
        if store is not None and getattr(store, "store_name", None):
            store_name = store.store_name  # PHASE 2 fix: closeout/Z-report reads the REAL name
    except Exception:
        logger.warning("config: regime source failed; CH fallback", exc_info=True)
        regime = resolve_regime(None)
    # PHASE 1 (Go-Italian): serve the ordered face-value list for the TENANT currency so
    # the client denom grids stop being hardcoded CHF. denoms_for() falls back to CHF for
    # an unknown currency, so a CH tenant gets the byte-identical Swiss set.
    denominations = [str(d) for d in denoms_for(regime.get("currency", settings.POS_CURRENCY))]
    return {
        "vat_rate": settings.POS_VAT_RATE,
        "vat_rate_reduced": settings.POS_VAT_RATE_REDUCED,  # 2.6% — cafe takeaway food/drink
        "vat_year": settings.POS_VAT_YEAR,
        "currency": regime["currency"],  # PHASE 1: per-tenant (regime reads the store; CH tenant -> CHF, byte-identical)
        "locale": regime["locale"],      # PHASE 1: per-tenant (CH tenant -> de-CH, byte-identical)
        "vat_decimal": settings.POS_VAT_RATE / 100,  # 0.081 for calculations
        "regime": regime,  # additive (PHASE 0): per-tenant regime/currency/locale + CH rates
        "store_name": store_name,  # PHASE 2: the tenant store name (closeout/Z-report header)
        "denominations": denominations,  # additive (PHASE 1): face values for the tenant currency
    }


# ================================================================
# PRODUCT ENDPOINTS
# ================================================================

def _sanitize_product_codes(data: dict) -> dict:
    """Guard the immutable identity against NAME-shaped SKUs/barcodes — the receiving
    "typed the product name into the scan box" trap. A barcode/SKU is a code: no
    whitespace, sane length. A product NAME has spaces. When the incoming code looks like
    a name we drop the barcode and mint a clean internal SKU, so the catalogue key and the
    postcard serial are never born polluted (SKU is immutable — the pollution can't be
    edited out later). Backstop to the receiving-screen client guard; protects every caller."""
    def _is_code(s: str) -> bool:
        return bool(s) and len(s) <= 40 and not any(c.isspace() for c in s)
    bc = (data.get("barcode") or "").strip()
    data["barcode"] = bc if _is_code(bc) else None
    sku = (data.get("sku") or "").strip()
    data["sku"] = sku if _is_code(sku) else f"LZ-{uuid4().hex[:10]}"
    return data


async def _mint_next_sku(db: AsyncSession, prefix: str) -> str:
    """Next sequential SKU for a prefix: PREFIX-0001, PREFIX-0002, … (max existing + 1).

    Server-side so two receivers can't collide on the same number; a rare race loses the
    UNIQUE(sku) insert (409) and the caller retries. Only 4-digit PREFIX-NNNN rows count —
    a legacy TAM-21577 import under the same prefix won't skew the maker sequence."""
    import re as _re
    res = await db.execute(select(ProductModel.sku).where(ProductModel.sku.like(f"{prefix}-%")))
    pat = _re.compile(rf"^{_re.escape(prefix)}-(\d{{1,6}})$")
    mx = 0
    for (s,) in res:
        m = pat.match(s or "")
        if m:
            mx = max(mx, int(m.group(1)))
    return f"{prefix}-{mx + 1:04d}"


async def _apply_supplier_mode_identity(db: AsyncSession, data: dict) -> dict:
    """Receiving 'supplier mode' (§3–5 of the goods-receipt spec). Strips the two receiving-only
    keys ALWAYS; when mint_identity was set, it mints the immutable identity server-side:
      • SKU = PREFIX-####  — the supplier's own prefix (ECO), else the shop's house prefix from
        settings (never ART/LZ; defaults to 'ITEM').
      • barcode = internal EAN-13 (GS1 20–29 in-store range) IF the item has no real barcode, so
        a no-code maker item is still scannable at the till and printable on a label.
      • supplier_name denormalized onto the product (the per-item supplier tag).
    No-op (beyond stripping the keys) for non-receiving callers."""
    mint = bool(data.pop("mint_identity", False))
    supplier_id = data.pop("supplier_id", None)
    if not mint:
        return data
    supplier = None
    if supplier_id:
        supplier = (await db.execute(
            select(SupplierModel).where(SupplierModel.id == supplier_id))).scalar_one_or_none()
    prefix = supplier.prefix if (supplier and supplier.prefix) else None
    if not prefix:
        settings_row = await get_active_store_settings(db)
        prefix = (getattr(settings_row, "house_sku_prefix", None) or "ITEM").upper()
    data["sku"] = await _mint_next_sku(db, prefix)
    if not (data.get("barcode") or "").strip():
        # Seed the EAN from the just-minted (unique) SKU → stable + unique; UNIQUE(barcode) backstops.
        data["barcode"] = mint_internal_ean13(data["sku"])
    if supplier is not None:
        data["supplier_name"] = supplier.name
    return data


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Create a new product in the catalog.

    Any cashier can CAPTURE a new item (Banco's born-once / sell-to-seed spirit — the person
    on the floor grows the catalog by selling). Destructive edits stay manager-only: changing
    price/details (PUT) and deleting (DELETE) still require a manager/admin."""

    data = await _apply_supplier_mode_identity(db, _sanitize_product_codes(product.model_dump()))
    new_product = ProductModel(**data)
    db.add(new_product)
    try:
        await db.commit()
    except IntegrityError:
        # BL-32: a duplicate barcode/SKU is NOT a dead-end — the operator was almost certainly
        # enriching an item that already exists without knowing. Find the existing row and hand its
        # id back in the 409 so the client can offer "apply your changes to the existing one".
        await db.rollback()
        existing = None
        conflict = None
        bc = (product.barcode or "").strip()
        sku = (product.sku or "").strip()
        if bc:
            existing = (await db.execute(
                select(ProductModel).where(ProductModel.barcode == bc))).scalar_one_or_none()
            if existing is not None:
                conflict = "barcode"
        if existing is None and sku:
            existing = (await db.execute(
                select(ProductModel).where(ProductModel.sku == sku))).scalar_one_or_none()
            if existing is not None:
                conflict = "sku"
        detail = {"message": "A product with this barcode or SKU already exists.", "conflict": conflict}
        if existing is not None:
            detail["existing_id"] = str(existing.id)
            detail["existing_name"] = existing.name
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    await db.refresh(new_product)

    logger.info(f"Product created: {new_product.sku} by user {current_user['username']}")
    return new_product


@router.post("/products/quick", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def quick_create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Cashier-safe on-the-fly create for no-barcode goods.

    Unlike full catalogue management (manager-only), a CASHIER can do this quick
    create — so Pam can ring up and re-sell a brand-new item in a rush (Christina's
    cups) without a manager. Minimal fields; auto-filed under "On the fly" if no
    category is given, so a manager can enhance or discontinue it later.
    """
    data = await _apply_supplier_mode_identity(db, _sanitize_product_codes(product.model_dump()))
    if not (data.get("name") or "").strip():
        raise HTTPException(status_code=422, detail="Name is required")
    if data.get("price") is None:
        raise HTTPException(status_code=422, detail="Price is required")
    if not (data.get("category") or "").strip():
        data["category"] = "On the fly"
    data["is_active"] = True
    # 18+ toggle (cashier contract): the checkout age gate reads product_class, NOT the
    # is_age_restricted column — bind the toggle to a gating class + keep the two in sync.
    # PLUS a compliance safety net: if the operator leaves it plain 'standard' but the NAME is
    # an age-restricted substance (tobacco/nicotine/alcohol/CBD), auto-gate it so an on-the-fly
    # "Swisher Sweets" can't be rung without ID (field 2026-07-08). Gate-only — never un-gates.
    from src.services.catalog_taxonomy import resolve_class_on_create
    data["product_class"], data["is_age_restricted"] = resolve_class_on_create(
        data.get("name"), data.get("product_class"), data.get("is_age_restricted"))
    new_product = ProductModel(**data)
    db.add(new_product)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this barcode or SKU already exists.",
        )
    await db.refresh(new_product)
    logger.info(f"Quick on-the-fly product: {new_product.sku} by {current_user['username']}")
    return new_product


@router.post("/products/ai-suggest", response_model=ProductSuggestResponse)
async def ai_suggest_product(
    file: UploadFile = File(...),
    hint: Optional[str] = None,
    provider: Optional[str] = None,
    current_user: dict = Depends(require_any_pos_role()),
):
    """Snap a photo of an unmarked item → AI drafts the product fields.

    Same gate as the quick on-the-fly create (any POS role): a cashier holding a
    new, barcode-less item can shoot it and get name/category/description back to
    confirm. This endpoint ONLY suggests — it does not persist. The flow is:
        /products/ai-suggest (photo) → cashier confirms → /products/quick → /images.

    Brain is model-agnostic (BANCO_VISION_PROVIDER: gemini default / claude / ollama);
    `?provider=` overrides per call (handy for the timing probe). The AI round-trip
    is returned as `elapsed_ms`.
    """
    raw = await file.read()
    if len(raw) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 15 MB)")
    if not (file.content_type or "").lower().startswith("image/"):
        raise HTTPException(status_code=415, detail="Please upload an image")

    from src.services.vision_product_analyzer import suggest_product_from_image
    from src.services.image_intake import ImageIntakeError
    try:
        result = await suggest_product_from_image(
            raw, file.content_type or "image/jpeg", hint=hint, provider=provider,
        )
    except ImageIntakeError:
        raise HTTPException(status_code=400, detail="That doesn't look like a usable photo")

    logger.info(
        "AI product suggest: provider=%s model=%s %dms conf=%.2f name=%r by %s",
        result["provider"], result["model"], result["elapsed_ms"],
        result["suggestion"]["confidence"], result["suggestion"]["name"],
        current_user["username"],
    )
    return result


async def _find_catalog_matches(db: AsyncSession, q: str, limit: int = 6) -> dict:
    """Find-first: given a NAME, search the LIVE catalog (`products`) AND the FourTwenty
    reference (`reference_products`) by pg_trgm similarity and return the REAL matching
    rows, best-first. This is the *librarian* half of snap-find — it FINDS what already
    exists instead of drafting a new product. Reused by GET /products/find-matches (a
    typed or AI-read name) and by POST /products/snap-find (photo → AI name → this).

    HONEST confidence: each match carries its trigram similarity (0..1) — a *match* score,
    not a model self-rating. `best_match_score` = the top catalog hit's similarity, so the
    UI can say "found it" vs "no strong match → search or create new" (the grinder lesson:
    never a confident wrong answer)."""
    from sqlalchemy import text
    from src.services.catalog_taxonomy import class_promo_restricted

    q = (q or "").strip()
    limit = max(1, min(int(limit or 6), 20))
    empty = {"query": q, "product_matches": [], "reference_matches": [], "best_match_score": 0.0}
    if not q:
        return empty

    # Live catalog = the Artemis-Luzern truth already imported into `products`.
    # BL-33: INCLUDE inactive products here (unlike the till search) — an inactive product
    # still exists AND owns its barcode (a create would 409), so hiding it made a dead-end.
    # Surface it flagged `is_active:false`; active matches rank first.
    # LANGUAGE-AGNOSTIC MATCH (the migration unlock): the AI reads a photo in ENGLISH, but the
    # Artemis catalog NAME is German ("Feuerzeug Gas Tycoon", "Mühle") — plain name-trigram
    # misses (grinder↔Mühle = 0.00). The DESCRIPTION, however, is the English text Artemis
    # already publishes on its /en/ pages (BL-18 scraped it — 96% populated). We score by the
    # GREATEST of name-trigram AND word_similarity(query, name+description): word_similarity
    # matches the query against the best SUBSTRING, so it's not diluted by a long description
    # and English keywords hit German-named items. No translation, no new column — the English
    # is already there.
    prod_rows = (await db.execute(text("""
        SELECT id, sku, barcode, name, category, price, image_url, product_class,
               is_age_restricted, price_tiers, tier_mode, is_active,
               GREATEST(
                 similarity(name, :q),
                 word_similarity(:q, coalesce(name,'') || ' ' || coalesce(description,''))
               ) AS score
        FROM products
        WHERE name ILIKE '%' || :q || '%'
           OR similarity(name, :q) > 0.15
           OR word_similarity(:q, coalesce(name,'') || ' ' || coalesce(description,'')) > 0.45
           OR supplier_name ILIKE '%' || :q || '%'
        ORDER BY is_active DESC,
                 CASE WHEN name ILIKE :q || '%' THEN 0 ELSE 1 END,
                 score DESC, name
        LIMIT :limit
    """), {"q": q, "limit": limit})).fetchall()
    product_matches = [{
        "id": str(r.id), "sku": r.sku, "barcode": r.barcode, "name": r.name,
        "category": r.category, "price": float(r.price) if r.price else 0,
        "image_url": r.image_url, "product_class": r.product_class,
        "is_age_restricted": bool(r.is_age_restricted),
        "promo_restricted": class_promo_restricted(r.product_class),
        "price_tiers": r.price_tiers, "tier_mode": r.tier_mode,
        "is_active": bool(r.is_active),
        "score": round(float(r.score), 3) if r.score is not None else 0.0,
    } for r in prod_rows]

    # FourTwenty reference (adoptable — carries real supplier EANs when present).
    ref_rows = (await db.execute(text("""
        SELECT id, supplier, supplier_sku, barcode, title, description, image_url,
               category, suggested_price, similarity(title, :q) AS score
        FROM reference_products
        WHERE title ILIKE '%' || :q || '%' OR similarity(title, :q) > 0.1
        ORDER BY CASE WHEN title ILIKE :q || '%' THEN 0 ELSE 1 END,
                 similarity(title, :q) DESC, title
        LIMIT :limit
    """), {"q": q, "limit": limit})).fetchall()
    reference_matches = [{
        "id": str(r.id), "supplier": r.supplier, "supplier_sku": r.supplier_sku,
        "barcode": r.barcode, "title": r.title, "name": r.title,
        "description": r.description, "image_url": r.image_url, "category": r.category,
        "suggested_price": float(r.suggested_price) if r.suggested_price is not None else None,
        "is_reference": True,
        "score": round(float(r.score), 3) if r.score is not None else 0.0,
    } for r in ref_rows]

    best = product_matches[0]["score"] if product_matches else 0.0
    return {"query": q, "product_matches": product_matches,
            "reference_matches": reference_matches, "best_match_score": best}


@router.get("/products/find-matches")
async def find_product_matches(
    q: str = "",
    limit: int = 6,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Find-first search: given a NAME (typed, or read off a photo by the AI), return the
    REAL catalog + reference rows that match, ranked by trigram similarity with honest
    scores. The librarian — it finds what already exists rather than inventing a new
    product. Pairs with POST /products/snap-find (photo → AI name → this)."""
    return await _find_catalog_matches(db, q, limit)


@router.post("/products/snap-find")
async def snap_find_product(
    file: UploadFile = File(...),
    hint: Optional[str] = None,
    provider: Optional[str] = None,
    limit: int = 6,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Snap a photo → the AI reads the item → SEARCH the real catalog for it (find-first).

    The librarian, not the author. Where /products/ai-suggest only DRAFTS a new product,
    this reads the name off the photo and runs it through _find_catalog_matches so the
    cashier can pick the item that ALREADY exists (in `products` or the FourTwenty
    reference). The AI draft rides along as the fallback for a genuine new item.

    Returns the ai-suggest envelope (`suggestion`/`provider`/`model`/`elapsed_ms`) PLUS
    `query`, `product_matches`, `reference_matches`, `best_match_score`. Honest confidence
    is the match score, not the model's self-rating — the grinder can't return a confident
    wrong answer, because a low `best_match_score` means "not found → search or create"."""
    raw = await file.read()
    if len(raw) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 15 MB)")
    if not (file.content_type or "").lower().startswith("image/"):
        raise HTTPException(status_code=415, detail="Please upload an image")

    from src.services.vision_product_analyzer import suggest_product_from_image
    from src.services.image_intake import ImageIntakeError
    try:
        result = await suggest_product_from_image(
            raw, file.content_type or "image/jpeg", hint=hint, provider=provider,
        )
    except ImageIntakeError:
        raise HTTPException(status_code=400, detail="That doesn't look like a usable photo")

    # Build the search from what the AI read: name is the strongest signal; fold in brand
    # when the model split it out (so "Flower Mill" grinder still hits with brand=Next-Gen).
    s = result.get("suggestion") or {}
    name = (s.get("name") or "").strip()
    brand = (s.get("brand") or "").strip()
    q = f"{brand} {name}".strip() if (brand and brand.lower() not in name.lower()) else (name or brand)

    matches = await _find_catalog_matches(db, q, limit)
    logger.info(
        "AI snap-find: provider=%s %dms q=%r → %d catalog + %d reference (best=%.2f) by %s",
        result.get("provider"), result.get("elapsed_ms", 0), q,
        len(matches["product_matches"]), len(matches["reference_matches"]),
        matches["best_match_score"], current_user["username"],
    )
    return {**result, **matches}


@router.get("/products/search-suppliers-live")
async def search_suppliers_live(
    q: str = "",
    limit: int = 4,
    suppliers: str = "",
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Live fallback for find-first: when the local catalog + reference cache MISS, search the
    shop's SUPPLIER WEBSITES live and return adoptable rows (name / price / photo / real EAN /
    tier ladder). Supplier-list-driven — it iterates the active suppliers that have a website
    (`source_url`) and dispatches each to its platform adapter (magento/tamar/shopware, or a
    sniffed one). `suppliers` optionally restricts by supplier code/name (comma-separated).
    One slow supplier can't sink the batch (per-adapter deadline)."""
    from src.services.supplier_search import search_suppliers
    keys = [s for s in (suppliers or "").split(",") if s.strip()] or None
    out = await search_suppliers(q, db, suppliers=keys, limit=max(1, min(int(limit or 4), 8)))
    logger.info("live supplier-search q=%r → %d results (%s), errors=%s by %s",
                q, len(out["results"]), out.get("suppliers"), out["errors"], current_user["username"])
    return out


@router.post("/products/adopt-live-reference")
async def adopt_live_reference(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """SELF-HEAL: cache a chosen live supplier result into `reference_products` so the next
    lookup is a local hit. Idempotent upsert on (supplier, ref_key) where ref_key is the real
    EAN when present, else a slug of the product URL. Returns the reference row (with id) so
    the picker can adopt it via the existing reference path. Non-CHF prices (Near Dark = EUR)
    are kept out of `suggested_price` so the CHF compare panel never mixes currencies."""
    import re
    from sqlalchemy import text as _text

    supplier = (payload.get("supplier") or "").strip()
    title = (payload.get("title") or payload.get("name") or "").strip()
    if not supplier or not title:
        raise HTTPException(status_code=422, detail="supplier and title are required")
    barcode = (payload.get("barcode") or "").strip() or None
    product_url = (payload.get("product_url") or "").strip() or None
    currency = (payload.get("currency") or "CHF").strip().upper()
    price = payload.get("price")
    suggested = None
    if price is not None and currency == "CHF":
        try:
            suggested = round(float(price), 2)
        except (TypeError, ValueError):
            suggested = None

    # Stable per-supplier key: prefer the real EAN, else a slug of the product URL.
    ref_key = barcode
    if not ref_key and product_url:
        ref_key = re.sub(r"[^a-z0-9]+", "-", product_url.rsplit("/", 1)[-1].lower()).strip("-")[:150]
    if not ref_key:
        ref_key = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:150]

    raw = {"product_url": product_url, "currency": currency,
           "price_tiers": payload.get("price_tiers") or [], "tier_mode": payload.get("tier_mode") or "per_unit",
           "adopted_live_by": current_user["username"], "is_live": True}

    row = (await db.execute(_text("""
        INSERT INTO reference_products
            (id, supplier, ref_key, supplier_sku, barcode, title, description,
             image_url, category, suggested_price, raw, imported_at)
        VALUES
            (gen_random_uuid(), :supplier, :ref_key, NULL, :barcode, :title, :description,
             :image_url, :category, :suggested, CAST(:raw AS jsonb), now())
        ON CONFLICT ON CONSTRAINT uq_reference_products_supplier_refkey DO UPDATE SET
            barcode = EXCLUDED.barcode, title = EXCLUDED.title,
            description = COALESCE(EXCLUDED.description, reference_products.description),
            image_url = COALESCE(EXCLUDED.image_url, reference_products.image_url),
            category = COALESCE(EXCLUDED.category, reference_products.category),
            suggested_price = COALESCE(EXCLUDED.suggested_price, reference_products.suggested_price),
            raw = EXCLUDED.raw, imported_at = now()
        RETURNING id, supplier, supplier_sku, barcode, title, description, image_url,
                  category, suggested_price
    """), {
        "supplier": supplier, "ref_key": ref_key, "barcode": barcode, "title": title[:255],
        "description": (payload.get("description") or "").strip() or None,
        "image_url": (payload.get("image_url") or "").strip()[:500] or None,
        "category": (payload.get("category") or "").strip()[:100] or None,
        "suggested": suggested, "raw": json.dumps(raw),
    })).fetchone()
    await db.commit()

    logger.info("self-heal: adopted live %s %r → reference %s by %s",
                supplier, title, row.id, current_user["username"])
    return {
        "healed": True,
        "id": str(row.id), "supplier": row.supplier, "supplier_sku": row.supplier_sku,
        "barcode": row.barcode, "title": row.title, "name": row.title,
        "description": row.description, "image_url": row.image_url, "category": row.category,
        "suggested_price": float(row.suggested_price) if row.suggested_price is not None else None,
        "price_tiers": raw["price_tiers"], "tier_mode": raw["tier_mode"],
        "currency": currency, "is_reference": True, "is_live": True,
    }


@router.get("/products/{product_id}/i18n-description")
async def product_i18n_description(
    product_id: str,
    lang: str = "en",
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """BL-36: the product's description in the operator's language, filled on demand. A
    Tamar/Artemis product is fetched natively (DE/EN/FR/IT are published); anything else is
    machine-translated from the base (Ollama) and cached in product_translations. Falls back
    to the raw base description so the modal always shows something."""
    from src.db.models.product_model import ProductModel
    from src.services.product_translations import ensure_description
    product = await db.get(ProductModel, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return await ensure_description(db, product, lang)


@router.get("/products", response_model=list[ProductRead])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """List all products in catalog (any POS role)"""
    query = select(ProductModel)

    if active_only:
        query = query.where(ProductModel.is_active == True)

    if category:
        query = query.where(ProductModel.category == category)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()

    return products


@router.get("/products/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get product by ID (any POS role)"""
    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.post("/products/{product_id}/publish-to-lapiazza", status_code=status.HTTP_201_CREATED)
async def publish_to_lapiazza(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "🛠️ pos-developer", "👑️ pos-admin"])),
):
    """Publish a product to La Piazza as a DRAFT listing under the shop's business account (manager-only).

    The shop must have the La Piazza module enabled (store_settings.lapiazza_enabled). The listing is
    created as a DRAFT for the owner to review + publish (push-once-then-decouple — re-publishing makes
    a NEW listing, never an update). Returns the bridge result incl. view_url. The listing id/slug are
    recorded on the product so the UI can show 'on La Piazza' + the Banco QR can resolve to it later."""
    product = (await db.execute(select(ProductModel).where(ProductModel.id == product_id))).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    store = (await db.execute(
        select(StoreSettingsModel).order_by(StoreSettingsModel.store_number))).scalars().first()
    if not store:
        raise HTTPException(status_code=400, detail="Store is not configured")
    if not store.lapiazza_enabled:
        raise HTTPException(status_code=400,
                            detail="The La Piazza module is off for this shop — enable it first")
    try:
        res = await publish_product(db, product, store)
    except SquareBridgeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"published": True, **res}


async def _find_product_by_any_barcode(db: AsyncSession, barcode: str) -> Optional[ProductModel]:
    """
    Resolve a scanned barcode to a product, checking BOTH the primary
    products.barcode AND the product_barcodes alias table (BL-90). This is what
    makes "scan once, known forever" hold even when a pack carries more than one
    barcode — every code the product has ever been scanned under resolves here.
    """
    # Primary barcode first (the common case, indexed).
    result = await db.execute(select(ProductModel).where(ProductModel.barcode == barcode))
    product = result.scalar_one_or_none()
    if product:
        return product
    # Fall back to the alias table.
    result = await db.execute(
        select(ProductModel)
        .join(ProductBarcodeModel, ProductBarcodeModel.product_id == ProductModel.id)
        .where(ProductBarcodeModel.barcode == barcode)
    )
    return result.scalar_one_or_none()


@router.get("/products/barcode/{barcode}", response_model=ProductRead)
async def get_product_by_barcode(
    barcode: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get product by barcode (for scanning) — matches primary OR alias barcodes."""
    product = await _find_product_by_any_barcode(db, barcode)

    if not product:
        raise HTTPException(status_code=404, detail=f"Product with barcode '{barcode}' not found")

    if not product.is_active:
        raise HTTPException(status_code=400, detail="Product is inactive")

    return product


class AddBarcodeRequest(BaseModel):
    barcode: str


@router.post("/products/{product_id}/barcodes", status_code=status.HTTP_201_CREATED)
async def add_product_barcode(
    product_id: UUID,
    body: AddBarcodeRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),  # cashiers capture: link a scanned code
):
    """
    Attach an additional barcode to an existing product (BL-90 alias barcodes).

    Use this when a product carries more than one barcode (retail + case code), or
    when an operator realises a freshly-scanned code belongs to an item already in
    the catalog — instead of creating a duplicate product. Idempotent: if this code
    already points at THIS product (primary or alias) it's a no-op; if it points at
    a DIFFERENT product it's a 409.
    """
    barcode = (body.barcode or "").strip()
    if not barcode:
        raise HTTPException(status_code=400, detail="Barcode is required")

    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Already resolves somewhere? Decide no-op vs conflict.
    existing = await _find_product_by_any_barcode(db, barcode)
    if existing is not None:
        if existing.id == product.id:
            return {"status": "already_linked", "product_id": str(product.id), "barcode": barcode}
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Barcode '{barcode}' already belongs to another product ({existing.name}).",
        )

    # If the product has no primary barcode yet, set it there; else add an alias.
    if not product.barcode:
        product.barcode = barcode
        product.updated_at = datetime.now(timezone.utc)
    else:
        db.add(ProductBarcodeModel(product_id=product.id, barcode=barcode))

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Barcode '{barcode}' already exists.",
        )

    logger.info(f"Barcode '{barcode}' linked to product {product.sku} by {current_user['username']}")
    return {"status": "linked", "product_id": str(product.id), "barcode": barcode}


# ============================================================================
# BL-97 — REFERENCE CATALOG (product master): search + adopt
# A supplier-fed lookup list. Search it, then ADOPT a row into the live `products`
# catalog (copying the real title/description/photo) instead of re-typing made-up data.
# Lookup-only; never sells from here. Zero-perpetual-inventory unchanged.
# ============================================================================

@router.get("/reference/search")
async def search_reference_catalog(
    q: str = "",
    barcode: str = "",
    limit: int = 8,
    skip: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """Search the reference catalog (trigram on title + exact barcode). Same envelope
    shape as /search. Public (catalog lookup). `name`/`price` are aliased from
    title/suggested_price so the scan modal can render reference + live hits the same way."""
    from sqlalchemy import text

    q = (q or "").strip()
    barcode = (barcode or "").strip()
    limit = max(1, min(int(limit or 8), 50))

    query = text("""
        SELECT id, supplier, supplier_sku, barcode, title, description, image_url,
               category, suggested_price,
               count(*) OVER() AS total_count
        FROM reference_products
        WHERE (
            (:barcode <> '' AND barcode = :barcode)
            OR (:q <> '' AND (title ILIKE '%' || :q || '%' OR similarity(title, :q) > 0.1))
        )
        ORDER BY
          CASE WHEN :barcode <> '' AND barcode = :barcode THEN 0 ELSE 1 END,
          CASE WHEN title ILIKE :q || '%' THEN 0 ELSE 1 END,
          similarity(title, :q) DESC, title
        LIMIT :limit OFFSET :skip
    """)
    rows = (await db.execute(query, {
        "q": q, "barcode": barcode, "limit": limit, "skip": skip,
    })).fetchall()

    total = int(rows[0].total_count) if rows else 0
    items = [
        {
            "id": str(row.id), "supplier": row.supplier, "supplier_sku": row.supplier_sku,
            "barcode": row.barcode, "title": row.title, "name": row.title,
            "description": row.description, "image_url": row.image_url, "category": row.category,
            "suggested_price": float(row.suggested_price) if row.suggested_price is not None else None,
            "price": float(row.suggested_price) if row.suggested_price is not None else None,
            "is_reference": True,
        }
        for row in rows
    ]
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/products/{product_id}/supplier-compare")
async def supplier_compare(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Slice-3 price comparison. For a product, find the best reference-catalog match PER
    SUPPLIER (fuzzy on name — Artemis products carry no EAN), so a manager can see what each
    supplier charges and price to beat them. Display-only + computed fresh (never stored). The
    match is a SUGGESTION — the operator confirms it by the title + similarity before trusting it.
    Reuses the same trigram path as /reference/search (GIN index ix_reference_products_title_trgm)."""
    from sqlalchemy import text
    product = (await db.execute(
        select(ProductModel).where(ProductModel.id == product_id))).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    name = (product.name or "").strip()
    matches = []
    if name:
        rows = (await db.execute(text("""
            SELECT DISTINCT ON (supplier)
                   id, supplier, supplier_sku, barcode, title, description, image_url,
                   suggested_price, cost,
                   similarity(title, :q) AS sim
            FROM reference_products
            WHERE :q <> '' AND (title ILIKE '%' || :q || '%' OR similarity(title, :q) > 0.25)
            ORDER BY supplier, similarity(title, :q) DESC, title
        """), {"q": name})).fetchall()
        matches = [
            {
                "supplier": r.supplier,
                "ref_id": str(r.id),
                "supplier_sku": r.supplier_sku,
                "barcode": r.barcode,
                "title": r.title,
                "description": r.description,          # the source's real copy (pull instead of AI make-up)
                "image_url": r.image_url,              # the source's real photo (pull instead of phone shot)
                "suggested_price": float(r.suggested_price) if r.suggested_price is not None else None,
                "cost": float(r.cost) if r.cost is not None else None,
                "similarity": round(float(r.sim), 2) if r.sim is not None else None,
            }
            for r in rows
        ]
        matches.sort(key=lambda m: (m["similarity"] or 0), reverse=True)
    return {
        "product": {
            "id": str(product.id), "name": product.name,
            "price": float(product.price) if product.price is not None else None,
        },
        "matches": matches,
        "best": matches[0] if matches else None,
    }


class AdoptReferenceRequest(BaseModel):
    barcode: Optional[str] = None       # the scanned code to bind (usually the scan-miss)
    price: Optional[Decimal] = None     # cashier's price; falls back to suggested_price


def _ref_adopt_sku(supplier: str, supplier_sku: Optional[str], barcode: Optional[str], ref_id) -> str:
    """A stable, unique-ish SKU for an adopted reference item so re-adopting is idempotent."""
    tail = (supplier_sku or barcode or str(ref_id)[:8] or "").strip()
    return ("REF-" + supplier + "-" + tail).upper().replace(" ", "")[:100]


@router.post("/reference/{ref_id}/adopt", response_model=ProductRead,
             status_code=status.HTTP_201_CREATED)
async def adopt_reference_product(
    ref_id: UUID,
    body: AdoptReferenceRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Cherry-pick a reference item into the live catalog (cashier-safe).

    Copies the canonical title/description/image/category across, binds the scanned barcode
    as the new product's PRIMARY barcode (so it stays cashier-safe — no manager-only alias
    call), and sets the price (cashier's, else the supplier's suggested). Idempotent: if the
    barcode or the derived SKU already resolves to a live product, that product is returned
    instead of creating a duplicate twin."""
    ref = (await db.execute(
        select(ReferenceProductModel).where(ReferenceProductModel.id == ref_id)
    )).scalar_one_or_none()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference product not found")

    barcode = (body.barcode or ref.barcode or "").strip() or None

    # Idempotency guard 1: this barcode already points at a live product → return it.
    if barcode:
        existing = await _find_product_by_any_barcode(db, barcode)
        if existing is not None:
            return existing

    sku = _ref_adopt_sku(ref.supplier, ref.supplier_sku, ref.barcode, ref.id)

    # Idempotency guard 2: already adopted under this SKU → return it.
    existing_sku = (await db.execute(
        select(ProductModel).where(ProductModel.sku == sku)
    )).scalar_one_or_none()
    if existing_sku is not None:
        return existing_sku

    price = body.price if body.price is not None else ref.suggested_price
    if price is None:
        raise HTTPException(status_code=422, detail="Price is required (no suggested price on file)")
    price = Decimal(str(price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if price < 0:
        raise HTTPException(status_code=422, detail="Price must be >= 0")

    new_product = ProductModel(
        barcode=barcode,
        sku=sku,
        name=ref.title,
        description=ref.description,
        price=price,
        cost=ref.cost,
        # BL-96: carry our skeleton category + behaviour class + 18+ flag (set by the enricher),
        # falling back to FourTwenty's raw category if the item wasn't reclassified yet.
        category=(ref.our_category or ref.category or "").strip() or "Other",
        product_class=ref.our_class or "standard",
        is_age_restricted=bool(ref.age_restricted),
        image_url=ref.image_url,    # provisional — copied into our storage below (best-effort)
        supplier_name=ref.supplier,
        supplier_sku=ref.supplier_sku,
        # Non-destructive price reference: keep what the supplier suggested (RRP) alongside our
        # editable `price` (the operator's own selling price). Lets us later show the supplier
        # figure as a grayed reference to beat, instead of losing it the moment we adopt.
        supplier_price=ref.suggested_price,
        is_active=True,
    )
    db.add(new_product)
    try:
        await db.commit()
    except IntegrityError:
        # Race / duplicate barcode|sku → return whatever now exists rather than 500.
        await db.rollback()
        if barcode:
            existing = await _find_product_by_any_barcode(db, barcode)
            if existing is not None:
                return existing
        existing_sku = (await db.execute(
            select(ProductModel).where(ProductModel.sku == sku)
        )).scalar_one_or_none()
        if existing_sku is not None:
            return existing_sku
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Could not adopt — a conflicting product already exists.")
    await db.refresh(new_product)
    # BL-97c: copy the supplier image into our own storage so we don't hotlink a URL that may
    # rot. Best-effort — on any failure the product keeps the external URL set above.
    if ref.image_url:
        await _copy_external_image_to_storage(db, new_product, ref.image_url)
    logger.info(f"Adopted reference '{ref.title}' ({ref.supplier}) → product {sku} "
                f"by {current_user['username']}")
    return new_product


@router.put("/products/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: UUID,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Update product details (manager/admin only)"""

    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update only provided fields
    update_data = product_update.model_dump(exclude_unset=True)
    # BL-26: validate + normalize quantity-break tiers before they land (ascending, unique).
    # The first-row rule is mode-aware: per_unit needs a qty-1 base row; bundle ("N for X")
    # starts at qty>=2 (base = the product's own price). Use the incoming tier_mode if the edit
    # sets one, else the product's current mode.
    if "price_tiers" in update_data:
        from src.services.pricing import validate_price_tiers
        tier_mode = update_data.get("tier_mode") or product.tier_mode or "per_unit"
        try:
            update_data["price_tiers"] = validate_price_tiers(update_data["price_tiers"], tier_mode)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"Invalid price tiers: {e}")

    # Snapshot the text fields that DRIVE the translation cache before we overwrite them.
    # If a manager rewrites the name/description, the cached per-language skins
    # (product_translations) are now derived from stale text — the postcard would keep
    # serving the old translated wording. We compare after the setattr loop and, if either
    # changed, invalidate the cache so ensure_description regenerates on next view.
    _text_before = (product.name, product.description)

    for field, value in update_data.items():
        setattr(product, field, value)

    _text_changed = (product.name, product.description) != _text_before

    # If this edit touched the 18+ toggle or the class, reconcile them so product_class (which
    # the checkout gate reads) and the is_age_restricted flag can never drift — a manager flipping
    # "18+" in the cleanup cockpit on a plain item files it under the gating "age_restricted" class.
    if "is_age_restricted" in update_data or "product_class" in update_data:
        from src.services.catalog_taxonomy import reconcile_age
        product.product_class, product.is_age_restricted = reconcile_age(
            product.product_class, product.is_age_restricted)

    product.updated_at = datetime.now(timezone.utc)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this barcode or SKU already exists.",
        )
    await db.refresh(product)

    # A rewritten name/description makes the cached translations stale — clear them so the
    # postcard and multilingual views regenerate from the new base text (BL: stale-translation fix).
    if _text_changed:
        from src.services.product_translations import invalidate_translations
        cleared = await invalidate_translations(db, product.id)
        if cleared:
            logger.info(f"Cleared {cleared} stale translation(s) for {product.sku} after text edit")

    logger.info(f"Product updated: {product.sku} by user {current_user['username']}")
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Soft delete product (set inactive - manager/admin only)"""

    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = False
    product.updated_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"Product deactivated: {product.sku} by user {current_user['username']}")


# ================================================================
# SUPPLIER REGISTRY — a supplier IS an import source, keyed by a unique SKU prefix
# (TAM-=Tamar/Artemis, FTW-=FourTwenty, future CSV/manual). Foundation for
# multi-source import + receiving ("pick a supplier or add a new one").
# ================================================================
async def _count_products_for_prefix(db: AsyncSession, prefix: Optional[str]) -> int:
    """How many products carry this SKU prefix (e.g. TAM- → TAM-21577).

    This is the 'is the prefix in use?' check behind the freeze guardrail: the
    prefix is baked into every product SKU, so once products exist it can't change
    without orphaning them. Same spirit as source-scoped sync (§6f)."""
    if not prefix:
        return 0
    res = await db.execute(
        select(func.count()).select_from(ProductModel).where(ProductModel.sku.like(f"{prefix}-%"))
    )
    return int(res.scalar() or 0)


@router.get("/suppliers", response_model=list[SupplierRead])
async def list_suppliers(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """List active suppliers (for the receiving dropdown + admin screen).

    Read is open to any POS role so the receiving screen can populate its picker;
    creating/editing a supplier stays manager/admin (below)."""
    result = await db.execute(
        select(SupplierModel)
        .where(SupplierModel.is_active == True)  # noqa: E712
        .order_by(SupplierModel.name)
    )
    suppliers = result.scalars().all()
    # Per-prefix product counts so the UI can lock the prefix field once it's in use.
    # One grouped pass over products: first SKU segment (TAM-21577 → TAM) → count.
    counts_res = await db.execute(
        select(
            func.upper(func.split_part(ProductModel.sku, "-", 1)).label("pfx"),
            func.count().label("n"),
        )
        .where(ProductModel.sku.isnot(None))
        .group_by("pfx")
    )
    counts = {row.pfx: int(row.n) for row in counts_res}
    for s in suppliers:
        s.product_count = counts.get((s.prefix or "").upper(), 0)
    return suppliers


@router.post("/suppliers", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier: SupplierCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Register a new supplier / import source (manager/admin only).

    The prefix is force-uppercased and validated (^[A-Z]{2,3}$, not the reserved
    ART/LZ) by the Pydantic schema; the DB UNIQUE constraint backstops duplicates."""
    data = supplier.model_dump()
    # `code` is the legacy Sourcing-System NOT NULL unique column — mirror the prefix
    # into it so a registry row satisfies the old schema without a second concept.
    new_supplier = SupplierModel(code=data["prefix"], **data)
    db.add(new_supplier)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A supplier with prefix '{data['prefix']}' already exists.",
        )
    await db.refresh(new_supplier)
    new_supplier.product_count = 0  # brand new — nothing carries its prefix yet
    logger.info(f"Supplier created: {new_supplier.prefix} ({new_supplier.name}) by {current_user['username']}")
    return new_supplier


@router.patch("/suppliers/{supplier_id}", response_model=SupplierRead)
async def update_supplier(
    supplier_id: str,
    supplier_update: SupplierUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Edit or deactivate a supplier (manager/admin only). Send is_active=false to
    retire one (it drops out of the dropdown but the SKU prefix stays reserved)."""
    result = await db.execute(select(SupplierModel).where(SupplierModel.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_data = supplier_update.model_dump(exclude_unset=True)
    # FREEZE GUARDRAIL: the prefix is baked into every product SKU (TAM-21577).
    # Editable until used, frozen once used — changing it after products exist would
    # orphan them. So a prefix *change* is rejected while the CURRENT prefix is in use;
    # all other fields (name, contacts, source_url, adapter_type, vat) stay editable.
    new_prefix = update_data.get("prefix")
    if new_prefix is not None and new_prefix != supplier.prefix:
        in_use = await _count_products_for_prefix(db, supplier.prefix)
        if in_use > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Prefix '{supplier.prefix}' is in use by {in_use} product(s) "
                    f"and can't be changed (it's baked into their SKUs)."
                ),
            )
        supplier.code = new_prefix  # keep legacy `code` mirrored to the prefix
    for field, value in update_data.items():
        setattr(supplier, field, value)
    # NOTE: do NOT set updated_at here. The legacy `suppliers` table uses a NAIVE
    # DateTime column with onupdate=datetime.utcnow (which fires automatically on
    # flush). Assigning a tz-AWARE value (datetime.now(timezone.utc)) makes asyncpg
    # raise "can't subtract offset-naive and offset-aware datetimes" -> 500.
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A supplier with this prefix already exists.",
        )
    await db.refresh(supplier)
    supplier.product_count = await _count_products_for_prefix(db, supplier.prefix)
    logger.info(f"Supplier updated: {supplier.prefix} ({supplier.name}) by {current_user['username']}")
    return supplier


# ================================================================
# BL-21/22 — THE ORDER BOOK (reorder pencil-list + per-line supplier pick)
# Zero-perpetual doctrine (docs/BANCO-REORDER-ORDER-BOOK.md): never compute from an on-hand
# count. Track order STATE (to_order → on_order → received), suggest by sales VELOCITY, let
# the human decide. BL-22: each line carries the supplier the human PICKED for it.
# ================================================================

class ReorderCreate(BaseModel):
    product_id: Optional[UUID] = None      # None = free-typed "we don't stock this yet"
    title: Optional[str] = None            # required if no product_id
    qty: int = 1
    reason: str = "restock"                # restock | customer_request
    customer_id: Optional[UUID] = None
    customer_note: Optional[str] = None
    supplier_code: Optional[str] = None
    note: Optional[str] = None


class ReorderUpdate(BaseModel):
    qty: Optional[int] = None
    status: Optional[str] = None           # to_order | on_order | received | cancelled
    supplier_code: Optional[str] = None
    eta: Optional[date] = None
    note: Optional[str] = None
    customer_note: Optional[str] = None


def _reorder_dto(r: ReorderItemModel) -> dict:
    return {
        "id": str(r.id),
        "product_id": str(r.product_id) if r.product_id else None,
        "title": r.title,
        "qty": r.qty,
        "reason": r.reason,
        "customer_id": str(r.customer_id) if r.customer_id else None,
        "customer_note": r.customer_note,
        "supplier_code": r.supplier_code,
        "status": r.status,
        "eta": r.eta.isoformat() if r.eta else None,
        "note": r.note,
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("/reorder")
async def list_reorder(
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The Order Book. Any POS role can read it (it's the shared pencil-list). Default view
    hides cancelled + long-received; pass ?status_filter=all for everything."""
    q = select(ReorderItemModel)
    if status_filter and status_filter in REORDER_STATUSES:
        q = q.where(ReorderItemModel.status == status_filter)
    elif status_filter != "all":
        q = q.where(ReorderItemModel.status.in_(("to_order", "on_order", "received")))
    q = q.order_by(ReorderItemModel.created_at.desc())
    rows = (await db.execute(q)).scalars().all()
    return {"items": [_reorder_dto(r) for r in rows]}


@router.post("/reorder", status_code=status.HTTP_201_CREATED)
async def add_reorder(
    body: ReorderCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),   # a cashier captures "Larry wanted X"
):
    """Add a line to the Order Book — a restock or a customer special-order. A product_id
    snapshots its name; otherwise `title` is required (free-typed, not-yet-stocked item)."""
    if body.reason not in REORDER_REASONS:
        raise HTTPException(status_code=422, detail=f"reason must be one of {REORDER_REASONS}")
    title = (body.title or "").strip()
    if body.product_id:
        p = (await db.execute(
            select(ProductModel).where(ProductModel.id == body.product_id)
        )).scalar_one_or_none()
        if p is None:
            raise HTTPException(status_code=404, detail="Product not found")
        if not title:
            title = p.name
        # BL-22: default the supplier to the product's known supplier if the caller didn't pick one.
        if not body.supplier_code and p.supplier_name:
            body.supplier_code = p.supplier_name
    if not title:
        raise HTTPException(status_code=422, detail="title is required for a free-typed item")
    item = ReorderItemModel(
        product_id=body.product_id,
        title=title[:200],
        qty=max(1, body.qty or 1),
        reason=body.reason,
        customer_id=body.customer_id,
        customer_note=(body.customer_note or None),
        supplier_code=(body.supplier_code or None),
        note=(body.note or None),
        status="to_order",
        created_by=current_user["username"],
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    logger.info(f"Order Book +1: '{item.title}' ({item.reason}) by {current_user['username']}")
    return _reorder_dto(item)


@router.patch("/reorder/{item_id}")
async def update_reorder(
    item_id: UUID,
    body: ReorderUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),   # advancing state = manager's call
):
    """Advance an Order Book line: pick/switch supplier (BL-22), set qty/eta/note, or move
    its status (to_order → on_order → received / cancelled)."""
    item = (await db.execute(
        select(ReorderItemModel).where(ReorderItemModel.id == item_id)
    )).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Order Book item not found")
    data = body.model_dump(exclude_unset=True)
    if "status" in data and data["status"] not in REORDER_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {REORDER_STATUSES}")
    if "qty" in data and data["qty"] is not None:
        data["qty"] = max(1, data["qty"])
    for field, value in data.items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    logger.info(f"Order Book ~ '{item.title}' → {item.status} "
                f"(supplier={item.supplier_code}) by {current_user['username']}")
    return _reorder_dto(item)


@router.delete("/reorder/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reorder(
    item_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """Remove an Order Book line outright (manager/admin)."""
    item = (await db.execute(
        select(ReorderItemModel).where(ReorderItemModel.id == item_id)
    )).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Order Book item not found")
    await db.delete(item)
    await db.commit()
    return None


@router.get("/reorder/suggestions")
async def reorder_suggestions(
    days: int = 21,
    limit: int = 15,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Advisory ONLY (never a gate): fastest-selling products over the last `days` that are
    NOT already on the Order Book. Velocity is rock-solid even with zero-perpetual — the till
    knows exactly what sold. Suggest, don't decide."""
    since = datetime.now(timezone.utc) - timedelta(days=max(1, days))
    # Products already on the book (to_order / on_order) — don't re-suggest them.
    on_book = set((await db.execute(
        select(ReorderItemModel.product_id).where(
            ReorderItemModel.product_id.isnot(None),
            ReorderItemModel.status.in_(("to_order", "on_order")),
        )
    )).scalars().all())
    rows = (await db.execute(
        select(
            LineItemModel.product_id,
            func.sum(LineItemModel.quantity).label("sold"),
        )
        .join(TransactionModel, LineItemModel.transaction_id == TransactionModel.id)
        .where(
            TransactionModel.status == TransactionStatus.COMPLETED,
            TransactionModel.created_at >= since,
            LineItemModel.product_id.isnot(None),
        )
        .group_by(LineItemModel.product_id)
        .order_by(func.sum(LineItemModel.quantity).desc())
        .limit(limit * 3)   # over-fetch, then filter out on-book ones
    )).all()
    out = []
    for pid, sold in rows:
        if pid in on_book:
            continue
        p = (await db.execute(
            select(ProductModel).where(ProductModel.id == pid)
        )).scalar_one_or_none()
        if p is None:
            continue
        out.append({
            "product_id": str(pid), "title": p.name, "sold": int(sold),
            "supplier_code": p.supplier_name, "days": days,
        })
        if len(out) >= limit:
            break
    return {"suggestions": out, "days": days}


# ================================================================
# PRODUCT PHOTO GALLERY — many pictures per product. The picture IS the label
# for ~100%-unmarked goods; a few angles is how you recognise an item later.
# Bytes live in MinIO; product_images rows index + order them; products.image_url
# is the cover. Served back through the app (no public bucket / presigned URLs).
# Tidied + shrunk by the BL-92 Pillow pipeline when present; stored as-is otherwise.
# ================================================================

_MAX_IMAGE_BYTES = 15 * 1024 * 1024  # a phone photo, not a video


def _gallery_image_key(product_id, image_id) -> str:
    return f"pos-products/{product_id}/{image_id}.jpg"


def _image_serve_url(product_id, image_id) -> str:
    return f"/api/v1/pos/products/{product_id}/images/{image_id}"


def _process_image_upload(raw: bytes, content_type: str) -> bytes:
    """Validate + (optionally) tidy/shrink an uploaded photo. Raises HTTPException."""
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(raw) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 15 MB)")
    if not (content_type or "").lower().startswith("image/"):
        raise HTTPException(status_code=415, detail="Please upload an image")
    # Pillow pipeline if it's in the image; otherwise keep the original bytes so the
    # feature works before any image rebuild (Pillow==10.4.0 is queued in requirements).
    try:
        from src.services.image_intake import process, PRODUCT, ImageIntakeError
        try:
            return process(raw, PRODUCT).main
        except ImageIntakeError:
            raise HTTPException(status_code=400, detail="That doesn't look like a usable photo")
    except ImportError:
        logger.warning("Pillow not in image — storing product photo as-is (no resize).")
        return raw


async def _copy_external_image_to_storage(db: AsyncSession, product, source_url: str):
    """Best-effort: pull an external image (e.g. a supplier's reference URL) into MinIO as a
    gallery photo + cover, so we own the bytes instead of hotlinking a URL that may rot. (BL-97c)

    Returns the served URL on success, else None (the caller keeps the external URL). NEVER
    raises — adopting a reference item must not fail because an image couldn't be copied."""
    import io as _io
    import asyncio as _asyncio

    url = (source_url or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return None
    # Already one of ours? Nothing to copy.
    if "/api/v1/pos/products/" in url and "/images/" in url:
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as c:
            resp = await c.get(url)
        if resp.status_code != 200 or not resp.content:
            return None
        out_bytes = _process_image_upload(resp.content, resp.headers.get("content-type", "image/jpeg"))
    except HTTPException:
        return None   # not a usable image — keep the external URL
    except Exception as e:
        logger.warning(f"Reference image fetch failed ({url[:80]}): {e}")
        return None
    try:
        from src.services.minio_service import minio_service
        image = ProductImageModel(product_id=product.id, sort_order=0)
        db.add(image)
        await db.flush()
        key = _gallery_image_key(product.id, image.id)
        loop = _asyncio.get_running_loop()
        await loop.run_in_executor(
            None, minio_service.client.put_object,
            minio_service.bucket_name, key, _io.BytesIO(out_bytes), len(out_bytes), "image/jpeg",
        )
        serve = _image_serve_url(product.id, image.id)
        product.image_url = serve
        product.updated_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Copied reference image into storage for {product.sku} ({len(out_bytes)} bytes)")
        return serve
    except Exception as e:
        await db.rollback()
        logger.warning(f"Reference image store failed for {product.sku}: {e}")
        return None


@router.post("/products/{product_id}/images")
async def add_product_image(
    product_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Add a photo to a product's gallery (any POS role). A cashier snapping a
    photo during the born-once flow IS the same action as creating the item
    (which /products/quick already allows), so the photo add matches that gate —
    NOT manager-only. Catalogue management (price edits, cover, delete) stays
    manager-gated; only the benign photo-add opens up. The first photo also
    becomes the cover (products.image_url) if none is set yet."""
    import io as _io
    import asyncio as _asyncio
    from src.services.minio_service import minio_service

    product = (await db.execute(select(ProductModel).where(ProductModel.id == product_id))).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    out_bytes = _process_image_upload(await file.read(), file.content_type)

    # Next sort_order = current count (append to the end of the gallery).
    existing = (await db.execute(
        select(func.count()).where(ProductImageModel.product_id == product_id)
    )).scalar() or 0
    image = ProductImageModel(product_id=product_id, sort_order=existing)
    db.add(image)
    await db.flush()   # assign image.id before we build the key/url

    key = _gallery_image_key(product_id, image.id)
    loop = _asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            None, minio_service.client.put_object,
            minio_service.bucket_name, key, _io.BytesIO(out_bytes), len(out_bytes), "image/jpeg",
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"MinIO product image upload failed for {key}: {e}")
        raise HTTPException(status_code=500, detail="Photo upload to storage failed")

    url = _image_serve_url(product_id, image.id)
    is_cover = False
    # No cover yet (or it pointed at the legacy single slot)? Make this the cover.
    if not product.image_url or "/images/" not in (product.image_url or ""):
        product.image_url = url
        is_cover = True
    product.updated_at = datetime.now(timezone.utc)
    await db.commit()
    logger.info(f"Gallery photo added: {product.sku} #{existing+1} ({len(out_bytes)} bytes) by {current_user['username']}")
    return {"id": str(image.id), "url": url, "is_cover": is_cover, "image_url": product.image_url}


@router.get("/products/{product_id}/images")
async def list_product_images(
    product_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """List a product's gallery (public). Cover first if it's one of these."""
    rows = (await db.execute(
        select(ProductImageModel).where(ProductImageModel.product_id == product_id)
        .order_by(ProductImageModel.sort_order, ProductImageModel.created_at)
    )).scalars().all()
    product = (await db.execute(select(ProductModel).where(ProductModel.id == product_id))).scalar_one_or_none()
    cover = product.image_url if product else None
    items = [
        {"id": str(r.id), "url": _image_serve_url(product_id, r.id),
         "is_cover": _image_serve_url(product_id, r.id) == cover}
        for r in rows
    ]
    return {"items": items, "cover": cover}


@router.get("/products/{product_id}/images/{image_id}")
async def get_product_image(
    product_id: UUID,
    image_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """Stream one gallery photo from MinIO (public — catalogue images need no auth)."""
    import asyncio as _asyncio
    from src.services.minio_service import minio_service

    loop = _asyncio.get_running_loop()
    try:
        data = await loop.run_in_executor(
            None, minio_service.download_artifact, _gallery_image_key(product_id, image_id))
    except Exception:
        data = None
    if not data:
        raise HTTPException(status_code=404, detail="No such photo")
    return Response(content=data, media_type="image/jpeg",
                    headers={"Cache-Control": "public, max-age=86400"})


@router.put("/products/{product_id}/images/{image_id}/cover")
async def set_product_cover(
    product_id: UUID,
    image_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "🛠️ pos-developer", "👑️ pos-admin"])),
):
    """Pick which gallery photo is the cover (the one shown in lists + the cart)."""
    image = (await db.execute(
        select(ProductImageModel).where(
            ProductImageModel.id == image_id, ProductImageModel.product_id == product_id)
    )).scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="No such photo")
    product = (await db.execute(select(ProductModel).where(ProductModel.id == product_id))).scalar_one_or_none()
    product.image_url = _image_serve_url(product_id, image_id)
    product.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"image_url": product.image_url}


@router.delete("/products/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_image(
    product_id: UUID,
    image_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "🛠️ pos-developer", "👑️ pos-admin"])),
):
    """Remove one gallery photo. If it was the cover, repoint to the next remaining."""
    import asyncio as _asyncio
    from src.services.minio_service import minio_service

    image = (await db.execute(
        select(ProductImageModel).where(
            ProductImageModel.id == image_id, ProductImageModel.product_id == product_id)
    )).scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="No such photo")

    serve_url = _image_serve_url(product_id, image_id)
    await db.delete(image)

    # Best-effort remove the object from MinIO (don't fail the request if it's gone).
    loop = _asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            None, minio_service.client.remove_object,
            minio_service.bucket_name, _gallery_image_key(product_id, image_id))
    except Exception as e:
        logger.warning(f"MinIO remove_object skipped for {image_id}: {e}")

    # If we just deleted the cover, repoint it to the first remaining photo (or clear).
    product = (await db.execute(select(ProductModel).where(ProductModel.id == product_id))).scalar_one_or_none()
    if product and product.image_url == serve_url:
        nxt = (await db.execute(
            select(ProductImageModel).where(
                ProductImageModel.product_id == product_id, ProductImageModel.id != image_id)
            .order_by(ProductImageModel.sort_order, ProductImageModel.created_at).limit(1)
        )).scalar_one_or_none()
        product.image_url = _image_serve_url(product_id, nxt.id) if nxt else None
        product.updated_at = datetime.now(timezone.utc)
    await db.commit()


# ================================================================
# RECEIVING (BL-91) — stock IN at the counter: scan -> count -> stock up
# ================================================================

@router.post("/receiving", response_model=ReceivingResponse)
async def receive_stock(
    body: ReceivingRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Record goods coming IN (manager/admin only). Lean by design (BL-91): each line
    is a known product + a typed count; we bump stock and write an audit movement.
    No purchase orders, no costing — "scan to sell, scan to receive, one camera".

    New items are lazy-created on the receiving page first (POST /products), so this
    endpoint only deals in product_ids. The whole batch is one transaction: if any
    line's product is missing, nothing is applied.
    """
    # Resolve every product up front so a bad line fails the WHOLE batch (atomic).
    resolved = []
    for item in body.items:
        result = await db.execute(select(ProductModel).where(ProductModel.id == item.product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found — nothing was received.",
            )
        resolved.append((product, item.quantity))

    reference = (body.reference or "").strip() or None
    lines = []
    total_units = 0
    for product, qty in resolved:
        product.stock_quantity = (product.stock_quantity or 0) + qty
        product.updated_at = datetime.now(timezone.utc)
        db.add(PosStockMovementModel(
            product_id=product.id,
            direction="in",
            quantity=qty,
            quantity_after=product.stock_quantity,
            reason="receiving",
            reference=reference,
            performed_by=current_user.get("username"),
        ))
        total_units += qty
        lines.append(ReceivingLineResult(
            product_id=product.id,
            name=product.name,
            quantity_received=qty,
            stock_after=product.stock_quantity,
        ))

    await db.commit()
    logger.info(
        f"Receiving: {len(lines)} line(s), {total_units} unit(s) in by "
        f"{current_user['username']}" + (f" (ref {reference})" if reference else "")
    )
    return ReceivingResponse(
        success=True,
        received_lines=len(lines),
        total_units=total_units,
        lines=lines,
    )


# ================================================================
# FAST SEARCH ENDPOINTS (PostgreSQL Full-Text + Trigram)
# ================================================================

@router.get("/search")
async def search_products_fast(
    q: str = "",
    category: Optional[str] = None,
    sort: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Fast paginated product search (trigram fuzzy + ILIKE + exact sku/barcode),
    backed by the GIN trigram index. Built for a big (thousands) catalog.

    Returns an envelope: {items, total, skip, limit}. `total` is the HONEST count
    of all matches (window count), so the UI can paginate / show "Found N".
    No auth required for search (public catalog).
    """
    from sqlalchemy import text

    # Normalize blanks: the UI sends `category=` (empty string) when no filter is
    # picked. Treated as a real filter it became `category ILIKE '%%'`, which
    # EXCLUDES every product whose category IS NULL (e.g. born-once items) — they
    # vanished from search. Empty → None = "no category filter". Empty q is fine:
    # it lists all active products (the catalogue browses by default).
    q = (q or "").strip()
    category = (category or "").strip() or None

    # BL-101 durable layer: expand an ENGLISH/brand ask to the GERMAN category/keyword terms
    # the catalog actually stores ("lighter" → "feuerzeug…", "scale" → "waage…"). Only kicks
    # in when a concept is recognised; otherwise syn_like is empty and the query below runs
    # exactly as the plain search. See services/catalog_search_synonyms.py.
    from src.services.catalog_search_synonyms import expand_search_terms
    syn_like = [f"%{t}%" for t in expand_search_terms(q)]
    # SQL fragments injected only when we have expansions (never user text → no injection):
    # a category/name hit on a synonym term scores a floor high enough to beat an incidental
    # description mention, so "lighter" surfaces the whole "Feuerzeuge" shelf, BIC included.
    syn_score = (
        ", CASE WHEN category ILIKE ANY(:syn_like) THEN 0.75"
        "       WHEN name ILIKE ANY(:syn_like) THEN 0.55 ELSE 0 END"
    ) if syn_like else ""
    syn_recall = " OR category ILIKE ANY(:syn_like) OR name ILIKE ANY(:syn_like)" if syn_like else ""

    # Sort is interpolated from a FIXED whitelist (never user text) → no injection surface;
    # q/category/limit/skip stay bound params. (No stock/reorder filter on purpose: the shop
    # reorders by eyeballing the shelf + a pencil list, not thresholds — and under
    # zero-perpetual-inventory the raw stock count is unreliable anyway.)
    order_clause = {
        "name":       "name ASC",
        "price_asc":  "price ASC, name",
        "price_desc": "price DESC, name",
        "recent":     "created_at DESC NULLS LAST, name",
        "stock":      "stock_quantity ASC, name",   # informational view, not a stock claim
    }.get((sort or "").strip().lower(),
          # default: relevance when searching, else name. BL-101: rank by the SELECT-list
          # `relevance` = GREATEST(name-trigram, word_similarity(q, name+description)). The
          # Artemis catalog NAME is German ("Feuerzeug BIC mini") but the DESCRIPTION is the
          # English text Artemis publishes — so an English query ("lighter", "bic lighter")
          # scored ~0 on the German name and sank under any item whose NAME held a token
          # ("Lighter", "LED …Light"). Scoring name-OR-description floats the real item up.
          # (Same trick the photo/capture search already uses — see search_reference_catalog.)
          "CASE WHEN name ILIKE :q || '%' THEN 0 ELSE 1 END, relevance DESC, name")

    # image fallback: a product's cover lives in products.image_url, but a cashier-
    # uploaded gallery photo only sets the cover when none exists yet — so a product can
    # have a perfectly good photo (visible in the edit gallery) while image_url is NULL,
    # and the LIST avatar then shows the placeholder. COALESCE to the product's FIRST
    # gallery image so the list renders the SAME picture the edit modal shows.
    query = text(f"""
        SELECT id, sku, barcode, name, category, price, price_tiers, tier_mode, stock_quantity, image_url, updated_at,
               is_age_restricted, product_class,
               (SELECT pi.id FROM product_images pi
                  WHERE pi.product_id = products.id
                  ORDER BY pi.sort_order, pi.created_at LIMIT 1) AS first_image_id,
               GREATEST(
                 similarity(name, :q),
                 -- description at HALF weight: it should LIFT a German-named/English-described
                 -- item ("Feuerzeug BIC mini" for "bic lighter") without letting an incidental
                 -- word in a long description outrank a real name match. Full weight let
                 -- unrelated items whose description merely mentions the word saturate the top.
                 0.5 * word_similarity(:q, coalesce(name,'') || ' ' || coalesce(description,'')){syn_score}
               ) AS relevance,
               count(*) OVER() AS total_count
        FROM products
        WHERE is_active = true
          AND (
            :q = '' OR name ILIKE '%' || :q || '%' OR sku ILIKE '%' || :q || '%'
            OR barcode ILIKE '%' || :q || '%' OR similarity(name, :q) > 0.1
            -- also match the SUPPLIER (find "Mama Cynthia" by her name) + the description text
            OR supplier_name ILIKE '%' || :q || '%'
            OR description ILIKE '%' || :q || '%'
            -- BL-101: word-similarity against name+description catches English queries on
            -- German-named items ("lighter"/"bic lighter" → "Feuerzeug BIC mini") and
            -- tolerates word order + minor typos the whole-phrase ILIKE misses.
            OR word_similarity(:q, coalesce(name,'') || ' ' || coalesce(description,'')) > 0.35
            {syn_recall}
          )
          AND (CAST(:category AS TEXT) IS NULL OR category ILIKE '%' || CAST(:category AS TEXT) || '%')
        ORDER BY {order_clause}
        LIMIT :limit OFFSET :skip
    """)
    params = {"q": q or "", "category": category, "limit": limit, "skip": skip}
    if syn_like:
        params["syn_like"] = syn_like
    rows = (await db.execute(query, params)).fetchall()

    from src.services.catalog_taxonomy import class_promo_restricted

    total = int(rows[0].total_count) if rows else 0
    items = [
        {
            "id": str(row.id), "sku": row.sku, "barcode": row.barcode, "name": row.name,
            "category": row.category, "price": float(row.price) if row.price else 0,
            "stock_quantity": row.stock_quantity or 0,
            # Cover, else the first gallery photo (so an uploaded photo always shows here).
            "image_url": row.image_url or (
                _image_serve_url(row.id, row.first_image_id) if row.first_image_id else None),
            # The uploaded gallery photo, ALWAYS surfaced when one exists — even if the cover
            # (image_url) is set to something that won't render (e.g. a supplier PRODUCT-PAGE
            # URL, not an image). The UI swaps to this if the cover image fails to load, so a
            # photo the cashier actually uploaded never hides behind a broken cover.
            "fallback_image_url": (
                _image_serve_url(row.id, row.first_image_id) if row.first_image_id else None),
            # updated_at lets the UI cache-bust the avatar so a freshly-added photo shows
            # without a hard refresh.
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "is_age_restricted": bool(row.is_age_restricted),
            "product_class": row.product_class,
            "promo_restricted": class_promo_restricted(row.product_class),
            "price_tiers": row.price_tiers,   # BL-26: so the cart can preview the tier line (shown==charged)
            "tier_mode": row.tier_mode,
            "relevance": float(row.relevance) if row.relevance else 0,
        }
        for row in rows
    ]
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/search/categories")
async def get_product_categories(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """Get all product categories with counts.

    Also returns the level-1 `product_group` each category belongs to (e.g.
    Headshop, Papers & Co, CBD), so the catalog filter can nest categories under
    group headers (a 2-level <optgroup> picker) instead of a flat ~52-long list.
    The group is the *dominant* group across that category's products (mode);
    a category whose products carry no group (e.g. on-the-fly manual items)
    resolves to NULL and the UI buckets it under "Other / Ungrouped".
    """
    from sqlalchemy import text

    # Query products directly (not the product_categories view, which has no
    # product_group). mode() ignores NULLs, so a category with a real group on
    # most rows reports that group; an all-NULL category reports NULL.
    query = text("""
        SELECT category AS name,
               count(*) AS count,
               avg(price) AS avg_price,
               mode() WITHIN GROUP (ORDER BY product_group) AS product_group
        FROM products
        WHERE is_active = true AND category IS NOT NULL AND category <> ''
        GROUP BY category
        ORDER BY count(*) DESC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    # The WHERE is_active = true + GROUP BY + count(*) already guarantees every row
    # returned has >= 1 ACTIVE product, so a category whose last product was
    # deleted/deactivated simply drops out. But the URL is stable, so a browser can
    # serve a STALE category list from its HTTP cache (the "Grinders (1)" ghost: count
    # > 0 in the dropdown while the product list is empty). Forbid caching so the
    # dropdown always reflects the live catalog.
    response.headers["Cache-Control"] = "no-store, max-age=0"

    return [
        {
            "name": row.name,
            "count": row.count,
            "avg_price": float(row.avg_price) if row.avg_price else 0,
            "product_group": row.product_group,
        }
        for row in rows
    ]


@router.post("/assist/vouch")
async def vouch_for_customer(
    customer_handle: str,
    voucher_handle: str,
    amount: float,
    item_description: str,
    fallback_contact: str = "pam",
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Forgot My Card — Trust network deferred payment.

    BLQ Scene: Coolie forgot his card.
    Sylvie: "I'll take care of it. You met Pam already.
             We're all connected here."

    Creates a vouch record:
    - Who vouched (Sylvie)
    - For whom (Coolie)
    - Amount (the torch lighter)
    - Fallback contact (Pam has details)

    Payment settled later through the network.
    """
    from datetime import datetime, timezone

    vouch_record = {
        "vouch_id": f"VOUCH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "customer": customer_handle,
        "vouched_by": voucher_handle,
        "amount_chf": amount,
        "item": item_description,
        "fallback_contact": fallback_contact,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "network_message": f"{voucher_handle} vouches for {customer_handle}. "
                          f"Fallback: ask {fallback_contact} for contact details.",
        "trust_chain": [voucher_handle, fallback_contact, "felix"]
    }

    logger.info(f"VOUCH: {voucher_handle} vouches for {customer_handle} - CHF {amount}")

    return {
        "success": True,
        "vouch": vouch_record,
        "message": f"I'll take care of it. You met {fallback_contact} already. We're all connected.",
        "contact_script": f"If you have issues, call me on Telegram or ask {fallback_contact} — she has all my details."
    }


@router.get("/assist/decide")
async def assist_decision(
    product_a: str,
    product_b: str,
    customer_context: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Seal the Deal — Help customer decide between two options.

    BLQ Scene: Coolie can't decide blue or black torch.
    Sylvie steps in: "The blue. It matches your bag."

    Staff uses this when customer is stuck.
    Returns: recommendation + reason + upsell.
    """
    # Simple decision helper - in real life could use AI
    recommendations = {
        "blue": "Stands out, matches most bags, popular choice",
        "black": "Classic, professional, never goes out of style",
        "gold": "Premium feel, gift-worthy, collector's item",
        "silver": "Sleek, modern, easy to spot in a drawer",
    }

    # Pick one (simple logic - could be smarter)
    choice = product_a.lower()
    reason = recommendations.get(choice, "Quality choice, can't go wrong")

    if customer_context and "bag" in customer_context.lower():
        reason = f"Matches the bag. {reason}"

    return {
        "recommendation": product_a,
        "reason": reason,
        "closer_script": f"The {product_a}. {reason}. I'll take care of it.",
        "upsell": "Need a case for that?",
        "seal_it": True
    }


@router.get("/search/picture")
async def search_from_picture(
    description: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Product lookup from picture/description.

    BLQ Scene: Joey shows Ralph a picture on his phone.
    "Ever seen these before?" - Jack Herer papers.

    Ralph types what he sees: "jack herer rolling papers gold"
    System searches products + returns suggestions.

    No image AI needed - just good description search.
    YAGNI: Phone works. Type what you see.
    """
    from sqlalchemy import text

    if not description or len(description) < 2:
        return {
            "success": False,
            "message": "Describe what you see in the picture",
            "products": [],
            "suggestions": []
        }

    # Search products by description
    query = text("""
        SELECT id, sku, barcode, name, category, price, stock_quantity, image_url, relevance
        FROM search_products(:search_term, NULL, 20)
    """)

    result = await db.execute(query, {"search_term": description})
    rows = result.fetchall()

    products = [
        {
            "id": str(row.id),
            "sku": row.sku,
            "name": row.name,
            "category": row.category,
            "price": float(row.price) if row.price else 0,
            "in_stock": (row.stock_quantity or 0) > 0,
            "relevance": float(row.relevance) if row.relevance else 0
        }
        for row in rows
    ]

    # Build helpful response
    if products:
        top = products[0]
        return {
            "success": True,
            "message": f"Found {len(products)} matches. Best: {top['name']}",
            "products": products,
            "suggestions": [
                "Check stock in back room",
                "Ask if customer wants to order",
                "Note for Felix: sourcing request"
            ] if not top['in_stock'] else [
                f"In stock! {top['name']}",
                "Show customer the product",
                "Add to transaction"
            ]
        }

    return {
        "success": False,
        "message": "No matches found. Try different words from the picture.",
        "products": [],
        "suggestions": [
            "Create sourcing request for Felix",
            "Take photo for KB",
            "Ask customer for more details",
            "Check supplier catalogs"
        ]
    }


@router.get("/search/stats")
async def get_product_stats(
    db: AsyncSession = Depends(get_db_session),
):
    """Get product catalog statistics."""
    from sqlalchemy import text

    query = text("SELECT * FROM product_stats")
    result = await db.execute(query)
    row = result.fetchone()

    if row:
        return {
            "total": row.total_products,
            "categories": row.categories,
            "with_barcode": row.with_barcode,
            "in_stock": row.in_stock,
            "avg_price": float(row.avg_price) if row.avg_price else 0
        }

    return {"total": 0, "categories": 0, "with_barcode": 0, "in_stock": 0, "avg_price": 0}


# ================================================================
# CUSTOMER QR SCAN (BLQ: Rapid Checkout)
# ================================================================

@router.get("/customer/scan", response_model=CustomerQRScanResponse)
async def scan_customer_qr(
    code: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Rapid customer lookup via QR code scan.

    BLQ Scene: Coolie shows QR on phone → Pam scans → Instant recognition

    The code format is: HLX-XXXXXXXX (8 hex chars after prefix)

    Returns customer info for checkout:
    - Handle, tier, discount
    - Credits balance
    - VIP status

    No auth required - scan is public (code is the secret).
    """
    if not code:
        return CustomerQRScanResponse(
            success=False,
            message="No QR code provided"
        )

    # Look up by QR code
    result = await db.execute(
        select(CustomerModel).where(CustomerModel.qr_code == code)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        return CustomerQRScanResponse(
            success=False,
            message=f"Customer not found for code: {code}"
        )

    if not customer.is_active:
        return CustomerQRScanResponse(
            success=False,
            message="Customer account is inactive"
        )

    logger.info(f"QR scan: Customer '{customer.handle}' recognized via {code}")

    return CustomerQRScanResponse(
        success=True,
        message=f"Welcome back, {customer.handle}!",
        customer_id=customer.id,
        handle=customer.handle,
        qr_code=customer.qr_code,
        loyalty_tier=customer.loyalty_tier.value,
        tier_discount_percent=customer.tier_discount_percent,
        credits_balance=customer.credits_balance,
        crack_level=customer.crack_level.value,
        is_vip=customer.is_vip,
    )


@router.post("/customer/{customer_id}/generate-qr")
async def generate_customer_qr(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "👑️ pos-admin"])),
):
    """
    Generate a new QR code for a customer (manager/admin only).

    Returns the new QR code value that should be encoded in a QR image.
    """
    result = await db.execute(
        select(CustomerModel).where(CustomerModel.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Generate new QR code
    new_code = customer.generate_qr_code()
    await db.commit()

    logger.info(f"QR code generated for '{customer.handle}': {new_code}")

    return {
        "customer_id": str(customer.id),
        "handle": customer.handle,
        "qr_code": new_code,
        "message": f"QR code generated: {new_code}"
    }


# ================================================================
# SHIFT SESSION WIZARD (BLQ: Pam forgot logout, Ralph needs POS)
# ================================================================

@router.post("/shift/start")
async def start_shift_session(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Start a new POS shift session.

    BLQ Scene: Ralph arrives, logs in, starts his shift.

    Creates a session record for:
    - Tracking who's on the register
    - Cash drawer accountability
    - Shift handoff chain
    """
    user_id = current_user.get('sub', current_user.get('preferred_username', 'unknown'))
    username = current_user.get('preferred_username', current_user.get('name', 'Unknown'))

    # Already on shift? This endpoint is a presence-tap fired on every dashboard load (the My Day
    # auto-tally), so being already-active is the NORMAL case, not an error — return the existing
    # session (200, idempotent) instead of a 400. Raising here only spammed a red "API call failed"
    # in the console/network tab for a no-op the caller already swallows.
    existing = (await db.execute(
        select(ShiftSessionModel).where(
            ShiftSessionModel.user_id == user_id,
            ShiftSessionModel.status == SessionStatus.ACTIVE
        )
    )).scalar_one_or_none()
    if existing:
        return {
            "session_id": str(existing.id),
            "username": existing.username,
            "store_number": existing.store_number,
            "started_at": existing.started_at.isoformat(),
            "already_active": True,
            "message": f"Shift already active for {username}",
        }

    # Create new session
    session = ShiftSessionModel(
        user_id=user_id,
        username=username,
        store_number=1,  # Default store
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info(f"Shift started: {username} at store {session.store_number}")

    return {
        "session_id": str(session.id),
        "username": session.username,
        "store_number": session.store_number,
        "started_at": session.started_at.isoformat(),
        "message": f"Shift started for {username}"
    }


@router.post("/shift/end")
async def end_shift_session(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    End current user's shift session (normal logout).
    """
    user_id = current_user.get('sub', current_user.get('preferred_username', 'unknown'))
    username = current_user.get('preferred_username', 'Unknown')

    result = await db.execute(
        select(ShiftSessionModel).where(
            ShiftSessionModel.user_id == user_id,
            ShiftSessionModel.status == SessionStatus.ACTIVE
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="No active session found")

    session.end_session(ended_by=user_id, reason="Normal logout")
    await db.commit()

    logger.info(f"Shift ended: {username}")

    return {
        "session_id": str(session.id),
        "username": session.username,
        "ended_at": session.ended_at.isoformat(),
        "transaction_count": session.transaction_count,
        "message": f"Shift ended for {username}"
    }


@router.get("/shift/today")
async def shift_today_presence(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Today's presence tally for the logged-in user, derived from login sessions.

    Powers My Day's auto-fill — "it shows when they logged in, so we tally it for them."
    Returns the first login of the day + minutes on shift so far; the employee just confirms.
    """
    user_id = current_user.get('sub', current_user.get('preferred_username', 'unknown'))
    now = datetime.now(timezone.utc)
    start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    result = await db.execute(
        select(ShiftSessionModel)
        .where(ShiftSessionModel.user_id == user_id)
        .where(ShiftSessionModel.started_at >= start_of_day)
        .order_by(ShiftSessionModel.started_at.asc())
    )
    sessions = list(result.scalars().all())

    # Fallback: still on a shift that began before midnight.
    if not sessions:
        result = await db.execute(
            select(ShiftSessionModel)
            .where(ShiftSessionModel.user_id == user_id)
            .where(ShiftSessionModel.status == SessionStatus.ACTIVE)
            .order_by(ShiftSessionModel.started_at.asc())
        )
        sessions = list(result.scalars().all())

    if not sessions:
        return {"present": False, "first_login": None, "total_minutes": 0,
                "suggested_hours": 0.0, "active": False}

    total = 0.0
    active = False
    for s in sessions:
        end = s.ended_at or now
        if s.ended_at is None and s.status == SessionStatus.ACTIVE:
            active = True
        total += max(0.0, (end - s.started_at).total_seconds() / 60.0)

    return {
        "present": True,
        "first_login": sessions[0].started_at.isoformat(),
        "total_minutes": int(round(total)),
        "suggested_hours": round((total / 60.0) * 4) / 4,  # nearest 0.25h
        "active": active,
    }


@router.post("/day-survey/draft")
async def draft_end_of_day_survey(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The AI End-of-Day Survey: Banco reads the caller's day at the till and DRAFTS the
    shift note for them — busy/steady/slow, a rough footfall, and a warm 1–2 line summary.
    The cashier just confirms or tweaks (My Day folds it into their closeout note).

    Resilient: if no brain is configured / it's down, returns an honest deterministic draft
    built from the numbers (ai=false). The survey never blocks closeout."""
    from src.services.day_survey import draft_day_survey
    return await draft_day_survey(db, await _resolve_cashier_uid(db, current_user))


@router.get("/shift/active")
async def get_active_sessions(
    store_number: int = 1,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get all active sessions at a store.

    BLQ Scene: Ralph arrives, sees Pam is still logged in.
    """
    result = await db.execute(
        select(ShiftSessionModel).where(
            ShiftSessionModel.store_number == store_number,
            ShiftSessionModel.status == SessionStatus.ACTIVE
        ).order_by(ShiftSessionModel.started_at.desc())
    )
    sessions = result.scalars().all()

    return {
        "store_number": store_number,
        "active_sessions": [
            {
                "session_id": str(s.id),
                "username": s.username,
                "started_at": s.started_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
                "transaction_count": s.transaction_count,
                "drawer_opened": s.drawer_opened,
            }
            for s in sessions
        ],
        "count": len(sessions)
    }


@router.post("/shift/force-end/{session_id}")
async def force_end_session(
    session_id: UUID,
    reason: str = "Manager override",
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Force end another user's session (manager/admin only).

    BLQ Scene: Felix on the road, gets call from Ralph.
    Felix force-ends Pam's session so Ralph can start his shift.
    """
    manager_id = current_user.get('sub', current_user.get('preferred_username', 'unknown'))
    manager_name = current_user.get('preferred_username', 'Manager')

    result = await db.execute(
        select(ShiftSessionModel).where(ShiftSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")

    session.force_end(manager_id=manager_id, reason=reason)
    await db.commit()

    logger.warning(f"Session FORCE ENDED: {session.username} by {manager_name} - {reason}")

    return {
        "session_id": str(session.id),
        "username": session.username,
        "ended_by": manager_name,
        "reason": reason,
        "message": f"Session force-ended for {session.username}"
    }


@router.post("/shift/handoff/{session_id}")
async def handoff_shift(
    session_id: UUID,
    next_user: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Handoff shift to next user (manager/admin only).

    BLQ Scene: Shift change - Pam → Ralph with manager approval.
    Creates audit trail of who handed off to whom.
    """
    manager_id = current_user.get('sub', current_user.get('preferred_username', 'unknown'))
    manager_name = current_user.get('preferred_username', 'Manager')

    result = await db.execute(
        select(ShiftSessionModel).where(ShiftSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")

    old_user = session.username
    session.handoff_to(next_user=next_user, manager_id=manager_id)
    await db.commit()

    logger.info(f"Shift HANDOFF: {old_user} → {next_user} (approved by {manager_name})")

    return {
        "session_id": str(session.id),
        "from_user": old_user,
        "to_user": next_user,
        "approved_by": manager_name,
        "message": f"Shift handed off from {old_user} to {next_user}"
    }


@router.get("/shift/my-session")
async def get_my_session(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get current user's active session (if any).

    Used by UI to show session status in header.
    """
    user_id = current_user.get('sub', current_user.get('preferred_username', 'unknown'))

    result = await db.execute(
        select(ShiftSessionModel).where(
            ShiftSessionModel.user_id == user_id,
            ShiftSessionModel.status == SessionStatus.ACTIVE
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        return {"active": False, "message": "No active session"}

    # Update activity
    session.update_activity()
    await db.commit()

    return {
        "active": True,
        "session_id": str(session.id),
        "username": session.username,
        "store_number": session.store_number,
        "started_at": session.started_at.isoformat(),
        "transaction_count": session.transaction_count,
        "drawer_opened": session.drawer_opened,
    }


# ================================================================
# TRANSACTION ENDPOINTS (Cart/Checkout)
# ================================================================

@router.get("/transactions", response_model=list[TransactionRead])
async def list_transactions(
    date: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status_filter: Optional[str] = None,
    payment_method: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """List transactions with optional filters. Managers see all, cashiers see their own."""
    query = select(TransactionModel)

    # Read-only visibility (BL-95): cashiers see ALL of TODAY's sales, not just their own —
    # small-shop transparency, and they can't change anything (refund/void/edit stay
    # manager-only). Managers/admins/auditors may also browse other dates. (Flip back to
    # per-cashier privacy by re-adding `where(cashier_id == sub)` for a larger shop.)
    user_roles = current_user.get("user_roles", [])
    is_manager = any("pos-manager" in r or "pos-admin" in r or "pos-auditor" in r for r in user_roles)

    # Date filter — cashiers are pinned to today; managers may pick a single date OR a range
    # (date_from..date_to, for "last 2 weeks" style reporting). An open bound collapses to
    # the other; a reversed range is swapped so from<=to always holds.
    def _parse(d):
        return datetime.strptime(d, "%Y-%m-%d").date()

    if is_manager and (date_from or date_to):
        lo = _parse(date_from) if date_from else _parse(date_to)
        hi = _parse(date_to) if date_to else _parse(date_from)
        if lo > hi:
            lo, hi = hi, lo
    elif date and is_manager:
        lo = hi = _parse(date)
    else:
        lo = hi = datetime.now(timezone.utc).date()

    start_of_day = datetime.combine(lo, datetime.min.time(), tzinfo=timezone.utc)
    end_of_day = datetime.combine(hi, datetime.max.time(), tzinfo=timezone.utc)
    query = query.where(TransactionModel.created_at >= start_of_day)
    query = query.where(TransactionModel.created_at <= end_of_day)

    # Status filter
    if status_filter:
        try:
            ts = TransactionStatus(status_filter.upper())
            query = query.where(TransactionModel.status == ts)
        except ValueError:
            pass
    else:
        # BL-86: hide reaped/cancelled empty carts from the default view so the report
        # stays clean. They're not deleted -- still reachable via status_filter=cancelled.
        query = query.where(TransactionModel.status != TransactionStatus.CANCELLED)

    # Payment method filter
    if payment_method:
        try:
            pm = PaymentMethod(payment_method.upper())
            query = query.where(TransactionModel.payment_method == pm)
        except ValueError:
            pass

    query = query.order_by(TransactionModel.created_at.desc())
    result = await db.execute(query)
    txns = result.scalars().all()

    # BL-83 (Felix): show WHO rang each sale. cashier_id is the Keycloak sub, which
    # matches users.id -- resolve it to a display name (first name, else username) so
    # the report says "Pam"/"Felix", not a generic "Cashier". One batched lookup.
    cashier_ids = {t.cashier_id for t in txns if t.cashier_id}
    names: dict = {}
    if cashier_ids:
        urows = await db.execute(
            select(UserModel.id, UserModel.first_name, UserModel.username)
            .where(UserModel.id.in_(cashier_ids))
        )
        names = {uid: (first or uname) for uid, first, uname in urows.all()}
    for t in txns:
        t.cashier_name = names.get(t.cashier_id)

    # Resolve the loyalty member each sale was rung under, so the list shows WHO she sold to
    # (anonymous walk-ins stay blank). One batched lookup.
    customer_ids = {t.customer_id for t in txns if t.customer_id}
    cust_names: dict = {}
    if customer_ids:
        crows = await db.execute(
            select(CustomerModel.id, CustomerModel.real_name, CustomerModel.handle)
            .where(CustomerModel.id.in_(customer_ids))
        )
        cust_names = {cid: (real or handle) for cid, real, handle in crows.all()}
    for t in txns:
        t.customer_name = cust_names.get(t.customer_id)
    return txns


@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["💰️ pos-cashier", "👔️ pos-manager", "👑️ pos-admin"])),
):
    """Create new transaction (open cart) - cashier/manager/admin only"""
    # Generate transaction number (simple sequential for demo)
    today = date.today().strftime("%Y%m%d")
    # TODO: Make this atomic with proper sequence
    count_result = await db.execute(
        select(func.count()).where(TransactionModel.transaction_number.like(f"TXN-{today}-%"))
    )
    count = count_result.scalar() or 0
    transaction_number = f"TXN-{today}-{count + 1:04d}"

    # Resolve the cashier to their stable users.id (FK target). One resolver, used by every
    # cashier-scoped path, so the sale, the drawer and "My Day" all key on the SAME value —
    # otherwise a 2nd sale collides on ix_users_keycloak_id and the drawer mis-counts. See
    # _resolve_cashier_uid for the seeded-PK-vs-sub story.
    cashier_uid = await _resolve_cashier_uid(db, current_user)

    new_transaction = TransactionModel(
        transaction_number=transaction_number,
        cashier_id=cashier_uid,
        status=TransactionStatus.OPEN,
        notes=transaction.notes,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total=Decimal("0.00"),
    )

    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)

    logger.info(f"Transaction created: {transaction_number} by cashier {current_user['username']}")
    return new_transaction


@router.get("/transactions/next-number")
async def next_transaction_number(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Preview the number the NEXT sale will get (TXN-YYYYMMDD-NNNN).

    Display-only, so the New Sale header reads the real next number instead of a
    random placeholder. The authoritative number is still assigned atomically in
    create_transaction; this preview can differ if another till rings up first.
    (Declared BEFORE /transactions/{transaction_id} so 'next-number' isn't parsed
    as a UUID.)
    """
    today = date.today().strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count()).where(TransactionModel.transaction_number.like(f"TXN-{today}-%"))
    )
    count = count_result.scalar() or 0
    return {"transaction_number": f"TXN-{today}-{count + 1:04d}"}


@router.get("/transactions/{transaction_id}")
async def get_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get transaction details with line items"""
    result = await db.execute(
        select(TransactionModel).where(TransactionModel.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Load line items separately
    line_items_result = await db.execute(
        select(LineItemModel).where(LineItemModel.transaction_id == transaction_id)
    )
    line_items = line_items_result.scalars().all()

    # Resolve product names so the receipt shows "CBD Oil 20%", not a generic "Product"
    # (one batched lookup, no N+1).
    from src.services.catalog_taxonomy import class_is_age_restricted
    product_names: dict = {}
    product_lapiazza: dict = {}   # product_id -> La Piazza slug (showcased items only) for the receipt QR
    product_age: dict = {}        # product_id -> 18+ flag (derived from class) for the 🔞 receipt badge
    product_ids = {item.product_id for item in line_items if item.product_id is not None}
    if product_ids:
        prod_rows = await db.execute(
            select(ProductModel).where(ProductModel.id.in_(product_ids))
        )
        for p in prod_rows.scalars().all():
            product_names[p.id] = p.name
            product_lapiazza[p.id] = p.lapiazza_slug
            product_age[p.id] = class_is_age_restricted(p.product_class)

    # Manually construct response to avoid async issues
    return {
        "id": str(transaction.id),
        "transaction_number": transaction.transaction_number,
        "cashier_id": str(transaction.cashier_id),
        "customer_id": str(transaction.customer_id) if transaction.customer_id else None,
        "status": transaction.status.value,
        "payment_method": transaction.payment_method.value if transaction.payment_method else None,
        "subtotal": str(transaction.subtotal),
        "discount_amount": str(transaction.discount_amount),
        "tax_amount": str(transaction.tax_amount),
        "total": str(transaction.total),
        "amount_tendered": str(transaction.amount_tendered) if transaction.amount_tendered else None,
        "change_given": str(transaction.change_given) if transaction.change_given else None,
        "receipt_number": transaction.receipt_number,
        "receipt_pdf_url": transaction.receipt_pdf_url,
        "notes": transaction.notes,
        "created_at": transaction.created_at.isoformat(),
        "updated_at": transaction.updated_at.isoformat(),
        "completed_at": transaction.completed_at.isoformat() if transaction.completed_at else None,
        "line_items": [
            {
                "id": str(item.id),
                "transaction_id": str(item.transaction_id),
                "product_id": str(item.product_id) if item.product_id else None,
                # Real product -> catalog name; custom line -> the name kept in notes.
                "product_name": product_names.get(item.product_id) or (item.notes if item.product_id is None else None),
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "discount_percent": str(item.discount_percent),
                "discount_amount": str(item.discount_amount),
                "line_total": str(item.line_total),
                "notes": item.notes,
                "is_giveaway": bool(item.is_giveaway),
                # 18+ line -> receipt prints a 🔞 badge (derived server-side from product class).
                "is_age_restricted": bool(product_age.get(item.product_id, False)),
                # Per-line VAT (INC2/4): the receipt prints a rate code (A=8.1% / B=2.6%) + legend.
                "consumption": item.consumption,
                "vat_rate": str(item.vat_rate) if item.vat_rate is not None else None,
                # showcased on La Piazza? -> the receipt shows a "scan to discuss" QR for this line
                "lapiazza_slug": product_lapiazza.get(item.product_id),
                "created_at": item.created_at.isoformat()
            }
            for item in line_items
        ]
    }


# ================================================================
# 🧹 BL-86: empty-cart reaper (end-of-day cleanup)
# ================================================================
async def reap_stale_open_carts(db: AsyncSession, older_than_hours: int = 12) -> dict:
    """Cancel abandoned empty carts so the report stays clean.

    A real shop leaves dangling OPEN carts behind: a cashier opens a sale and the
    customer walks, or someone mis-taps. We retire only the *truly empty* ones --
    OPEN, zero value, AND no line items -- once they're older than `older_than_hours`.
    We set status=CANCELLED (auditable, the number survives), never delete, and never
    touch a cart that has items or any value. Idempotent: a cart cancelled once won't
    match again. Returns the count + the transaction numbers reaped.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
    has_items = (
        select(LineItemModel.id)
        .where(LineItemModel.transaction_id == TransactionModel.id)
        .exists()
    )
    rows = (await db.execute(
        select(TransactionModel).where(
            TransactionModel.status == TransactionStatus.OPEN,
            TransactionModel.total == 0,
            TransactionModel.created_at < cutoff,
            ~has_items,
        )
    )).scalars().all()

    reaped = []
    now = datetime.now(timezone.utc)
    for t in rows:
        t.status = TransactionStatus.CANCELLED
        t.updated_at = now
        reaped.append(t.transaction_number)
    if rows:
        await db.commit()
    return {
        "cancelled": len(reaped),
        "older_than_hours": older_than_hours,
        "transaction_numbers": reaped,
    }


@router.post("/maintenance/reap-empty-carts")
async def reap_empty_carts(
    older_than_hours: int = 12,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "👑️ pos-admin"])),
):
    """Manually run the empty-cart reaper (it also runs hourly in the background).
    Manager/admin only. `older_than_hours` defaults to 12 -- anything still empty and
    open from earlier in the day gets cancelled."""
    result = await reap_stale_open_carts(db, older_than_hours=older_than_hours)
    logger.info(
        f"🧹 Empty-cart reaper (manual by {current_user.get('username')}): {result['cancelled']} cancelled"
    )
    return result


def _inclusive_vat(gross: Decimal) -> Decimal:
    """The VAT *contained within* a gross (VAT-inclusive) amount. Swiss retail prices include
    VAT, so for a gross G at rate r%, the contained VAT = G * r / (100 + r), rounded to cents.
    e.g. CHF 89.90 at 8.1% -> 6.74 VAT, leaving 83.16 net."""
    rate = Decimal(str(get_settings().POS_VAT_RATE))
    return (gross * rate / (Decimal("100") + rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@router.post("/transactions/{transaction_id}/items", response_model=LineItemRead)
async def add_item_to_transaction(
    transaction_id: UUID,
    item: LineItemCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["💰️ pos-cashier", "👔️ pos-manager", "👑️ pos-admin"])),
):
    """Add item to transaction cart (cashier/manager/admin only)"""
    # Verify transaction exists and is open
    trans_result = await db.execute(
        select(TransactionModel).where(TransactionModel.id == transaction_id)
    )
    transaction = trans_result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status != TransactionStatus.OPEN:
        raise HTTPException(status_code=400, detail="Transaction is not open")

    # Manual-discount ceiling by role (cashier 10% / manager 25% / admin unlimited).
    # The till caps this in the UI, but enforce it server-side too so the API can't
    # be used to over-discount past a cashier's limit (edge-sweep finding D1).
    if item.discount_percent is not None:
        cap = await _max_discount_pct(db, current_user)
        if item.discount_percent > cap:
            raise HTTPException(
                status_code=403,
                detail=f"Discount {item.discount_percent}% exceeds your {cap}% limit.")

    if item.product_id is not None:
        # Catalog product: price from the catalog (client unit_price ignored -> no
        # tampering). A real product on the shelf is ALWAYS sellable — Banco never
        # blocks a sale on a stock count (the count is a lie for ~100% unmarked goods,
        # and "sell anything, anytime" is the rule). Stock is still tracked: it's
        # deducted at checkout (floored at 0) and feeds the low-stock reorder signal —
        # informational, never a gate.
        prod_result = await db.execute(
            select(ProductModel).where(ProductModel.id == item.product_id)
        )
        product = prod_result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if not product.is_active:
            raise HTTPException(status_code=400, detail="Product is inactive")

        # A giveaway is a real product handed over free: zero revenue, but stock still
        # leaves (deducted at checkout) so it's tracked for COGS/tax.
        unit_price = Decimal("0.00") if item.is_giveaway else product.price
        tier_final = False
        if not item.is_giveaway:
            # BL-26: a quantity-break tier price wins over the flat price for this qty.
            unit_price, tier_final = tier_unit_price(
                product.price_tiers, unit_price, item.quantity, mode=product.tier_mode or "per_unit")
        line_notes = ("🎁 Treat — on the house" if item.is_giveaway else item.notes)
    else:
        # Custom line (manual catalog entry / product-as-change treat): no catalog
        # product, so the till supplies the price + name. No stock to check or deduct.
        if item.unit_price is None:
            raise HTTPException(status_code=422, detail="Custom line item requires unit_price")
        unit_price = item.unit_price
        tier_final = False
        # Keep the name for the receipt -- stored in notes (the only free-text column).
        line_notes = item.name or item.notes

    # Line is stored GROSS (qty x unit_price). The cart-wide % discount is applied ONCE
    # at the transaction level below. (Per-line discounting + the running subtotal being
    # re-rounded on each item's commit drifted a cent vs the till's single-rounded total
    # on multi-item discounts.)
    line_gross = (unit_price * item.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    line_total = line_gross

    # Per-line Swiss VAT (cafe multi-line tax). The product's behaviour class drives the
    # rate (alcohol/tobacco always 8.1%; cafe food/drink splits dine-in 8.1% / takeaway
    # 2.6%); a custom line has no class -> "standard" (8.1%, the legal default). The rate
    # + amount are SNAPSHOTTED here so a later rate change never rewrites this receipt.
    # (INC2: line-level only; the transaction total still uses the single-rate rollup
    # below — INC3 sums these per-line amounts.)
    prod_class = product.product_class if item.product_id is not None else "standard"
    line_rate, line_vat_amount = line_vat(prod_class, item.consumption, line_total)

    # Compliance: NO promotional discount on a promo-restricted class (tobacco, alcohol).
    # Swiss law (Tabakproduktegesetz / Alkoholgesetz) restricts sales promotions on these,
    # and it's about the SALE, not the operator — so this blocks cashier AND manager alike
    # (a role cap isn't enough). Exact scope is still pending the Treuhänder; this is the
    # safe default. A real markdown path (e.g. damaged goods) would be a separate flow.
    from src.services.catalog_taxonomy import class_promo_restricted, class_meta
    if item.discount_percent and item.discount_percent > 0 and class_promo_restricted(prod_class):
        raise HTTPException(
            status_code=400,
            detail=f"Discounts aren't allowed on {class_meta(prod_class)['label']} — "
                   f"sales promotions on these are restricted by law.")

    # BL-26: a quantity-break price is final — no further discount stacks on a tiered line.
    if item.discount_percent and item.discount_percent > 0 and tier_final:
        raise HTTPException(
            status_code=400,
            detail="No discount on a quantity-break price — the volume price is already the deal.")

    new_line_item = LineItemModel(
        transaction_id=transaction_id,
        product_id=item.product_id,
        quantity=item.quantity,
        unit_price=unit_price,
        discount_percent=item.discount_percent,
        discount_amount=Decimal("0.00"),
        line_total=line_total,
        notes=line_notes,
        is_giveaway=item.is_giveaway,
        consumption=item.consumption.value,
        vat_rate=line_rate,
        vat_amount=line_vat_amount,
    )

    db.add(new_line_item)

    # Transaction totals (inclusive VAT: subtotal & total are the GROSS the customer pays).
    # total = round(subtotal * (1 - pct/100)) -- the EXACT formula the till displays, so the
    # charged total always equals what the cashier/customer saw. discount = the reconciling gap.
    transaction.subtotal += line_gross
    keep = (Decimal("100") - item.discount_percent) / Decimal("100")
    transaction.total = (transaction.subtotal * keep).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    transaction.discount_amount = transaction.subtotal - transaction.total
    transaction.tax_amount = _inclusive_vat(transaction.total)
    transaction.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(new_line_item)

    item_label = product.sku if item.product_id is not None else (item.name or "custom")
    logger.info(f"Item added to transaction {transaction.transaction_number}: {item_label} x{item.quantity}")
    return new_line_item


@router.post("/transactions/{transaction_id}/scan", response_model=BarcodeScanResponse)
async def scan_barcode(
    transaction_id: UUID,
    scan: BarcodeScanRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["💰️ pos-cashier", "👔️ pos-manager", "👑️ pos-admin"])),
):
    """Scan barcode and add to transaction (cashier/manager/admin only)"""
    # Find product by barcode — primary OR alias (BL-90).
    product = await _find_product_by_any_barcode(db, scan.barcode)

    if not product:
        return BarcodeScanResponse(
            success=False,
            message=f"Product with barcode '{scan.barcode}' not found"
        )

    if not product.is_active:
        return BarcodeScanResponse(
            success=False,
            message="Product is inactive",
            product=ProductRead.model_validate(product)
        )

    # Add to transaction
    line_item_data = LineItemCreate(
        product_id=product.id,
        quantity=scan.quantity
    )

    try:
        line_item = await add_item_to_transaction(transaction_id, line_item_data, db, current_user)
        return BarcodeScanResponse(
            success=True,
            message=f"Added {scan.quantity}x {product.name}",
            product=ProductRead.model_validate(product),
            line_item=LineItemRead.model_validate(line_item)
        )
    except HTTPException as e:
        return BarcodeScanResponse(
            success=False,
            message=str(e.detail),
            product=ProductRead.model_validate(product)
        )


def _log_age_clearance(txn_ref: str, method: str, subject: str,
                       current_user: dict, cashier_uid) -> None:
    """Compliance trail: who cleared an 18+ sale, when, and how (member vs cashier-attest)."""
    actor = (current_user or {}).get("preferred_username") or (current_user or {}).get("sub") or str(cashier_uid)
    logger.info(
        f"AGE-GATE cleared · txn={txn_ref} · method={method} · subject={subject} · "
        f"verified_by={actor} · at={datetime.now(timezone.utc).isoformat()}")


def _assert_age_cleared(cart_age_restricted: bool, customer, age_verified: bool,
                        current_user: dict, cashier_uid, txn_ref: str) -> str | None:
    """Server-side 18+ age gate for the sale path (the client 🔞 alert is bypassable, this is not).
    No-op when the cart holds no age-restricted line. Otherwise the sale is REJECTED (400) unless:
      • an OF-AGE loyalty member is attached  -> method 'member', OR
      • the cashier explicitly attested a walk-in is 18+ (age_verified) -> method 'cashier_attest'.
    A member PROVEN under 18 by DOB is authoritative — blocked even if age_verified is set.
    Existing members (no DOB, age_confirmed=True) clear as of-age (back-compat). Emits a
    compliance log line on clearance. Returns the method used, or None for a clean cart."""
    if not cart_age_restricted:
        return None

    if customer is not None:
        # DOB is authoritative when present: a proven minor can't be overridden by attestation.
        if customer.birthdate is not None and not customer.is_of_age:
            raise HTTPException(
                status_code=400,
                detail="This loyalty member is under 18 — age-restricted (18+) items cannot be sold to them.")
        if customer.is_of_age:
            _log_age_clearance(txn_ref, "member", f"member:{customer.handle}", current_user, cashier_uid)
            return "member"
        # Legacy member with neither DOB nor age_confirmed: fall through to cashier attestation.

    if age_verified:
        _log_age_clearance(txn_ref, "cashier_attest", "walk-in", current_user, cashier_uid)
        return "cashier_attest"

    raise HTTPException(
        status_code=400,
        detail="Age-restricted (18+) item — verify age first: confirm the customer is 18+ "
               "(ID checked) or attach an of-age member.")


@router.post("/transactions/{transaction_id}/checkout", response_model=TransactionRead)
async def checkout_transaction(
    transaction_id: UUID,
    checkout: CheckoutRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["💰️ pos-cashier", "👔️ pos-manager", "👑️ pos-admin"])),
):
    """Process checkout and complete transaction (cashier/manager/admin only)"""
    trans_result = await db.execute(
        select(TransactionModel).where(TransactionModel.id == transaction_id)
    )
    transaction = trans_result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status != TransactionStatus.OPEN:
        raise HTTPException(status_code=400, detail="Transaction already processed")

    # Guard: never complete an empty cart — a CHF 0 sale with no lines is meaningless
    # and pollutes the day's count (found by the monkey/fuzz pass 2026-06-27).
    li_count = await db.scalar(
        select(func.count()).select_from(LineItemModel)
        .where(LineItemModel.transaction_id == transaction_id)
    )
    if not li_count:
        raise HTTPException(status_code=400, detail="Cannot check out an empty cart — add at least one item.")

    # --- CRM: attach the loyalty member + apply their tier discount (before the cash
    # check, so the member pays the discounted total). The total already reflects any
    # manual cart discount; the tier discount stacks on top of it. ---
    customer = None
    if checkout.customer_id is not None:
        customer = await db.get(CustomerModel, checkout.customer_id)
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer (loyalty member) not found")
        transaction.customer_id = customer.id
        tier_pct = int(customer.tier_discount_percent or 0)
        # Separate lanes: the member's tier stacks on any manual discount already on the txn.
        # The manual was capped at the cashier's own limit when it was applied (the /items
        # endpoint); the tier is the shop's loyalty promise and rides on top, uncapped by role.
        if tier_pct > 0:
            # Member discount applies ONLY to the eligible (non-promo-restricted) portion —
            # tobacco/alcohol never get a promo discount (Swiss law). Same rule as the atomic
            # /sales path; custom lines (no product) count as eligible standard goods.
            from src.services.catalog_taxonomy import class_promo_restricted as _cpr
            _rows = (await db.execute(
                select(LineItemModel.line_total, ProductModel.product_class)
                .select_from(LineItemModel)
                .outerjoin(ProductModel, ProductModel.id == LineItemModel.product_id)
                .where(LineItemModel.transaction_id == transaction_id))).all()
            eligible_total = sum((lt for lt, pc in _rows if not _cpr(pc)), Decimal("0.00"))
            tier_disc = (eligible_total * Decimal(tier_pct) / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)
            transaction.total = Decimal(str(transaction.total)) - tier_disc
            transaction.discount_amount = Decimal(str(transaction.discount_amount or 0)) + tier_disc

    # --- SAFETY FLOOR (parity with the atomic /sales path): the total can never go negative,
    # whatever caps/tiers are configured. Clamp so the customer is never owed money. ---
    if Decimal(str(transaction.total)) < 0:
        transaction.discount_amount = Decimal(str(transaction.subtotal))
        transaction.total = Decimal("0.00")

    # --- Age gate (18+): does this cart hold any age-restricted line? The class is the source
    # of truth (products.product_class -> taxonomy), joined via the staged line items. Reject
    # (400) an 18+ sale unless an of-age member is attached OR the cashier attested a walk-in. ---
    from src.services.catalog_taxonomy import class_is_age_restricted
    _age_classes = (await db.execute(
        select(ProductModel.product_class)
        .join(LineItemModel, LineItemModel.product_id == ProductModel.id)
        .where(LineItemModel.transaction_id == transaction_id)
    )).scalars().all()
    cart_age_restricted = any(class_is_age_restricted(c) for c in _age_classes)
    _assert_age_cleared(
        cart_age_restricted, customer, checkout.age_verified, current_user,
        await _resolve_cashier_uid(db, current_user), transaction.transaction_number)

    # Validate cash payment
    if checkout.payment_method == PaymentMethod.CASH:
        # A cash sale physically lands in the drawer, so it MUST belong to an OPEN
        # cash shift — otherwise the money is unassigned and can't be reconciled at
        # close (the bug Angel hit: cash taken before the drawer was opened). Card /
        # TWINT / debit never touch the drawer, so they're not gated. 409 = the till
        # prompts the cashier to open + initialise their drawer first.
        if not await _open_shift_for(db, await _resolve_cashier_uid(db, current_user)):
            raise HTTPException(
                status_code=409,
                detail="Open your cash drawer before taking a cash sale.")
        if not checkout.amount_tendered:
            raise HTTPException(status_code=400, detail="Cash payment requires amount_tendered")
        # Compare money at CENT precision. A JSON number like 226.17 reaches us as an
        # imprecise Decimal (226.16999…), so a strict `tendered < total` falsely rejected an
        # EXACT payment (the till already cent-rounds, so it showed change 0.00 then got a
        # 400). Quantize both to cents before comparing + computing change.
        tendered = Decimal(str(checkout.amount_tendered)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_due = Decimal(str(transaction.total)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if tendered < total_due:
            raise HTTPException(status_code=400, detail="Insufficient payment amount")
        transaction.change_given = tendered - total_due

    transaction.payment_method = checkout.payment_method
    transaction.amount_tendered = checkout.amount_tendered
    transaction.status = TransactionStatus.COMPLETED
    transaction.completed_at = datetime.now(timezone.utc)
    transaction.updated_at = datetime.now(timezone.utc)

    # VAT is the SUM of the per-line contained VAT at each line's snapshotted rate (INC3) — so a
    # mixed cafe cart (8.1% dine-in lines + 2.6% takeaway lines) gets the legally-correct total,
    # not a single blanket rate. The cart-wide discount is prorated across lines. Falls back to
    # the single-rate inclusive VAT if the sale has no priced lines (defensive).
    _lines = (await db.execute(
        select(LineItemModel.vat_rate, LineItemModel.line_total)
        .where(LineItemModel.transaction_id == transaction.id)
    )).all()
    if _lines:
        # Piece C: feed the tenant's rate table (CH shop w/ NULL vat_rates → CH config → byte-identical).
        _rate_table = await _tenant_rate_table(db)
        _split = split_vat([(r, lt) for r, lt in _lines], transaction.total, transaction.subtotal,
                           rate_table=_rate_table)
        transaction.tax_amount = _split["vat_total"]
    else:
        transaction.tax_amount = _inclusive_vat(transaction.total)

    # Generate receipt number
    transaction.receipt_number = f"REC-{transaction.transaction_number}"

    # TODO: Generate PDF receipt and store in MinIO

    # Zero perpetual inventory: a sale never decrements a stock count. The count was
    # always wrong for ~100% unmarked goods, and gating on it would refuse to sell
    # product physically on the shelf. Velocity is read from the sales log itself
    # (line items + completed_at) — see the velocity reporting spec (v2).

    # --- CRM: the member earns points + their record updates (1 credit per CHF paid,
    # floored). Updates lifetime spend, history, average basket, then re-tiers. ---
    if customer is not None:
        paid = Decimal(str(transaction.total))
        earned = int(paid)  # 1 credit per CHF, rounded down
        now = transaction.completed_at or datetime.now(timezone.utc)
        customer.lifetime_spend = Decimal(str(customer.lifetime_spend or 0)) + paid
        customer.purchase_count = (customer.purchase_count or 0) + 1
        if customer.first_purchase is None:
            customer.first_purchase = now
        customer.last_purchase = now
        customer.last_visit = now
        customer.average_basket = (customer.lifetime_spend / customer.purchase_count).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
        if earned > 0:
            customer.credits_balance = (customer.credits_balance or 0) + earned
            customer.credits_earned_total = (customer.credits_earned_total or 0) + earned
            db.add(CreditTransactionModel(
                customer_id=customer.id,
                transaction_type=CreditTransactionType.PURCHASE,
                credits=earned,
                balance_after=customer.credits_balance,
                reference_id=transaction.id,
                reference_type="order",
                description=f"Purchase {transaction.transaction_number}: +{earned} credits",
            ))
        from src.services.loyalty_service import policy_from_settings
        _tier_store = await get_active_store_settings(db)
        customer.recalculate_tier(policy_from_settings(_tier_store))

    await db.commit()
    await db.refresh(transaction)

    logger.info(f"Transaction completed: {transaction.transaction_number} - Total: {transaction.total} CHF"
                + (f" - member {customer.handle} +{int(Decimal(str(transaction.total)))}cr" if customer else ""))
    return transaction


@router.post("/sales", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale: SaleCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["💰️ pos-cashier", "👔️ pos-manager", "👑️ pos-admin"])),
):
    """P2.1 — atomic, idempotent create-sale: the WHOLE cart + payment in ONE request and ONE
    DB transaction. The keystone for the offline outbox, and strictly better online (no fragile
    3-round-trip partial-failure window). Idempotent on `client_uuid`: a replayed sale — a
    network retry, or an offline outbox draining on reconnect — is adopted EXACTLY ONCE, never
    double-rung. Same server-authoritative money rules as the legacy 3-step path (catalog price
    wins, per-line VAT snapshot, promo guard, role discount cap, cash-drawer gate, member tier +
    CRM) — proven equivalent by tests/pos/test_create_sale_atomic.py so the two paths never drift."""
    from src.services.catalog_taxonomy import class_promo_restricted, class_meta, class_is_age_restricted

    # --- Idempotency: if this client_uuid already rang, return that sale untouched (replay-safe). ---
    existing = (await db.execute(
        select(TransactionModel).where(TransactionModel.client_uuid == sale.client_uuid))).scalar_one_or_none()
    if existing is not None:
        logger.info(f"Idempotent replay adopted: client_uuid={sale.client_uuid} -> {existing.transaction_number}")
        return existing

    # --- SEPARATE LANES (Felix's call 2026-07-13, superseding the old "Option B" suppression).
    # Two independent discounts, two different pockets:
    #   • the member's earned TIER rate — the shop's loyalty promise, automatic, ALWAYS applies;
    #   • the cashier's MANUAL discount — their own discretion / rounding room.
    # The role cap is a fat-finger guard on the CASHIER'S OWN manual number only — it never
    # touches the member's tier. So a platinum member (20%) served by a cashier (cap 15%) still
    # gets their full 20% automatically, and the cashier may round down up to 15% MORE on top.
    # Damaged-goods / clearance markdowns ride the ladder: cashier 15 / manager 70 / owner 100. ---
    manual_pct = sale.discount_percent or Decimal("0")

    # Fetch the attached loyalty member up-front — reused for the tier discount applied later.
    customer = None
    if sale.customer_id is not None:
        customer = await db.get(CustomerModel, sale.customer_id)
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer (loyalty member) not found")

    cap = await _max_discount_pct(db, current_user)
    if manual_pct and manual_pct > cap:
        raise HTTPException(status_code=403,
                            detail=f"Discount {manual_pct}% exceeds your {cap}% limit.")

    cashier_uid = await _resolve_cashier_uid(db, current_user)

    # Transaction number: same count-based scheme as the legacy path (the "make this atomic"
    # TODO carries forward — client_uuid is the new idempotency guard either way).
    today = date.today().strftime("%Y%m%d")
    count = (await db.execute(
        select(func.count()).where(TransactionModel.transaction_number.like(f"TXN-{today}-%")))).scalar() or 0
    transaction_number = f"TXN-{today}-{count + 1:04d}"

    # Explicit id so line-item FKs resolve before the single flush/commit.
    txn = TransactionModel(
        id=uuid4(),
        transaction_number=transaction_number,
        client_uuid=sale.client_uuid,
        cashier_id=cashier_uid,
        status=TransactionStatus.OPEN,
        notes=sale.notes,
        subtotal=Decimal("0.00"), discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"), total=Decimal("0.00"),
    )
    db.add(txn)

    # --- Build every line server-authoritatively: catalog price wins, VAT snapshot, promo guard. ---
    built_lines = []
    subtotal = Decimal("0.00")
    eligible_subtotal = Decimal("0.00")  # non-promo-restricted lines only -> the member tier discount base
    cart_age_restricted = False  # set True by any 18+ line -> triggers the age gate below
    for ln in sale.lines:
        tier_final = False  # BL-26: True once a volume break (min_qty>=2) sets the price → discount-final
        if ln.product_id is not None:
            product = (await db.execute(
                select(ProductModel).where(ProductModel.id == ln.product_id))).scalar_one_or_none()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product not found: {ln.product_id}")
            if not product.is_active:
                raise HTTPException(status_code=400, detail=f"Product is inactive: {product.name}")
            unit_price = Decimal("0.00") if ln.is_giveaway else product.price
            if not ln.is_giveaway:
                # BL-26: a quantity-break tier price wins over the flat price for this qty.
                unit_price, tier_final = tier_unit_price(
                    product.price_tiers, unit_price, ln.quantity, mode=product.tier_mode or "per_unit")
            line_notes = ("🎁 Treat — on the house" if ln.is_giveaway else ln.notes)
            prod_class = product.product_class
        else:
            if ln.unit_price is None:
                raise HTTPException(status_code=422, detail="Custom line item requires unit_price")
            unit_price = ln.unit_price
            line_notes = ln.name or ln.notes
            prod_class = "standard"

        if class_is_age_restricted(prod_class):
            cart_age_restricted = True

        # Compliance note: a promo-restricted class (tobacco/alcohol) simply never enters the
        # discount base (eligible_subtotal, below) — the manual discount, like the member tier,
        # applies to the ELIGIBLE portion only, so tobacco always rings full price. No hard block,
        # no dead-end: a mixed cart discounts the rest and completes.

        line_gross = (unit_price * ln.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        line_total = line_gross
        line_rate, line_vat_amount = line_vat(prod_class, ln.consumption, line_total)
        line = LineItemModel(
            transaction_id=txn.id, product_id=ln.product_id, quantity=ln.quantity,
            unit_price=unit_price, discount_percent=Decimal("0.00"),
            discount_amount=Decimal("0.00"), line_total=line_total, notes=line_notes,
            is_giveaway=ln.is_giveaway, consumption=ln.consumption.value,
            vat_rate=line_rate, vat_amount=line_vat_amount,
        )
        db.add(line)
        built_lines.append(line)
        subtotal += line_gross
        # BL-26: a volume-break line is discount-FINAL — keep it out of the discount base too.
        if not class_promo_restricted(prod_class) and not tier_final:
            eligible_subtotal += line_gross   # only this portion can carry a discount (manual or member)

    # --- Cart totals (inclusive VAT; the EXACT formula the till displays, so charged == shown).
    # The MANUAL discount applies to the ELIGIBLE portion only — tobacco/alcohol always ring full
    # price (Swiss law), the same rule as the member tier. A mixed cart is never blocked. ---
    manual_disc = (eligible_subtotal * manual_pct / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    txn.subtotal = subtotal
    txn.total = subtotal - manual_disc
    txn.discount_amount = manual_disc

    # --- Member tier discount + attach (before the cash check, so the member pays discounted).
    # `customer` was already fetched up-front for the combined-cap check — reuse it here. ---
    if customer is not None:
        txn.customer_id = customer.id
        tier_pct = int(customer.tier_discount_percent or 0)
        if tier_pct > 0:
            # Member discount applies ONLY to the eligible (non-promo-restricted) portion — tobacco
            # and alcohol never get a promotional discount (Swiss law), the SAME per-line rule the
            # manual discount follows. One receipt: cigarettes ring full price, the lighter gets the
            # member rate. The manual discount STACKS on top (separate lane): both come off the same
            # eligible base, so a Silver 5% member + a 15% cashier manual = 20% off the eligible items.
            tier_base = eligible_subtotal
            tier_disc = (tier_base * Decimal(tier_pct) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            txn.total = Decimal(str(txn.total)) - tier_disc
            txn.discount_amount = Decimal(str(txn.discount_amount)) + tier_disc

    # --- SAFETY FLOOR (the "never pay the customer" guard). No matter what caps or tiers are
    # configured — even fat-fingered (a 100% owner cap + a 25% tier = 125%, or a mistyped setting) —
    # the combined discount can NEVER exceed the value of the discountable items. The sale floors
    # at the non-discountable (tobacco/alcohol) portion: total >= 0, always. This lives at the
    # point money is decided, so bad settings upstream can't ever produce a refund/negative total. ---
    if Decimal(str(txn.discount_amount)) > eligible_subtotal:
        txn.discount_amount = eligible_subtotal
        txn.total = subtotal - eligible_subtotal   # = the promo-restricted portion, guaranteed >= 0

    # --- Age gate (18+): reject the sale unless an of-age member is attached OR the cashier
    # attested a walk-in. cart_age_restricted was set from each line's class in the loop above. ---
    _assert_age_cleared(
        cart_age_restricted, customer, sale.age_verified, current_user,
        cashier_uid, transaction_number)

    # --- Cash drawer gate + cent-precision tender (identical rules to legacy checkout). ---
    if sale.payment_method == PaymentMethod.CASH:
        if not await _open_shift_for(db, cashier_uid):
            raise HTTPException(status_code=409, detail="Open your cash drawer before taking a cash sale.")
        if not sale.amount_tendered:
            raise HTTPException(status_code=400, detail="Cash payment requires amount_tendered")
        tendered = Decimal(str(sale.amount_tendered)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_due = Decimal(str(txn.total)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if tendered < total_due:
            raise HTTPException(status_code=400, detail="Insufficient payment amount")
        txn.change_given = tendered - total_due

    txn.payment_method = sale.payment_method
    txn.amount_tendered = sale.amount_tendered
    txn.status = TransactionStatus.COMPLETED
    txn.completed_at = datetime.now(timezone.utc)
    txn.updated_at = datetime.now(timezone.utc)

    # VAT = sum of per-line contained VAT at each snapshotted rate (mixed cart legally correct),
    # computed from the in-memory lines (no flush needed). Falls back to single-rate if no lines.
    _lines = [(l.vat_rate, l.line_total) for l in built_lines]
    # Piece C: tenant rate table (CH shop w/ NULL vat_rates → CH config → byte-identical).
    _rate_table = await _tenant_rate_table(db) if _lines else None
    txn.tax_amount = (split_vat(_lines, txn.total, txn.subtotal, rate_table=_rate_table)["vat_total"]
                      if _lines else _inclusive_vat(txn.total))

    txn.receipt_number = f"REC-{transaction_number}"

    # --- CRM: member earns 1 credit/CHF (floored) + record updates + re-tier (same as legacy). ---
    if customer is not None:
        paid = Decimal(str(txn.total))
        earned = int(paid)
        now = txn.completed_at
        customer.lifetime_spend = Decimal(str(customer.lifetime_spend or 0)) + paid
        customer.purchase_count = (customer.purchase_count or 0) + 1
        if customer.first_purchase is None:
            customer.first_purchase = now
        customer.last_purchase = now
        customer.last_visit = now
        customer.average_basket = (customer.lifetime_spend / customer.purchase_count).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
        if earned > 0:
            customer.credits_balance = (customer.credits_balance or 0) + earned
            customer.credits_earned_total = (customer.credits_earned_total or 0) + earned
            db.add(CreditTransactionModel(
                customer_id=customer.id, transaction_type=CreditTransactionType.PURCHASE,
                credits=earned, balance_after=customer.credits_balance,
                reference_id=txn.id, reference_type="order",
                description=f"Purchase {transaction_number}: +{earned} credits"))
        from src.services.loyalty_service import policy_from_settings
        _tier_store = await get_active_store_settings(db)
        customer.recalculate_tier(policy_from_settings(_tier_store))

    # ONE commit. The UNIQUE index on client_uuid is the real idempotency guard: if a concurrent
    # replay raced us, the INSERT loses the unique race — roll back and return the sale that won.
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        won = (await db.execute(
            select(TransactionModel).where(TransactionModel.client_uuid == sale.client_uuid))).scalar_one_or_none()
        if won is not None:
            logger.info(f"Idempotent race resolved: client_uuid={sale.client_uuid} -> {won.transaction_number}")
            return won
        raise
    await db.refresh(txn)

    logger.info(f"Sale rung (atomic): {transaction_number} - Total: {txn.total} CHF"
                + (f" - member {customer.handle} +{int(Decimal(str(txn.total)))}cr" if customer else "")
                + f" [client_uuid={sale.client_uuid}]")
    return txn


@router.post("/transactions/{transaction_id}/refund", response_model=TransactionRead)
async def refund_transaction(
    transaction_id: UUID,
    refund: RefundRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "👑️ pos-admin"])),
):
    """
    Process a refund for a completed transaction.

    Only managers and admins can process refunds.
    Customer always gets cash back (even if they paid with card).
    This is common in Swiss retail - simpler for accounting.

    Args:
        transaction_id: UUID of completed transaction to refund
        refund: RefundRequest with reason and optional partial amount

    Returns:
        Updated transaction — REFUNDED on a full refund, or COMPLETED at its net
        (kept) value on a partial refund (so the daily report counts what was retained).
    """
    # Get transaction
    trans_result = await db.execute(
        select(TransactionModel).where(TransactionModel.id == transaction_id)
    )
    transaction = trans_result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status != TransactionStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Can only refund completed transactions. Current status: {transaction.status.value}"
        )

    # Calculate refund amount. Quantize to cents BEFORE comparing — a partial_amount sent
    # as a JSON number is an imprecise Decimal, same class of bug as the cash-tendered check,
    # so an un-rounded `> total` could falsely reject a valid full-value partial refund.
    raw_refund = refund.partial_amount if refund.partial_amount else transaction.total
    refund_amount = Decimal(str(raw_refund)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    original_total = Decimal(str(transaction.total)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if refund_amount > original_total:
        raise HTTPException(
            status_code=400,
            detail=f"Refund amount ({refund_amount}) cannot exceed transaction total ({original_total})"
        )

    is_partial = Decimal("0") < refund_amount < original_total

    # Update transaction
    transaction.updated_at = datetime.now(timezone.utc)
    if is_partial:
        # Partial refund: the sale STAYS COMPLETED at its net (kept) value so the daily
        # report counts the money actually retained. The old code flipped the WHOLE txn to
        # REFUNDED, and the report (COMPLETED-only) then dropped the entire original sale —
        # so refunding CHF 5 of a CHF 50 sale erased all 50 from the day's takings.
        net = (original_total - refund_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        transaction.total = net
        transaction.tax_amount = _inclusive_vat(net)
        transaction.subtotal = (net - transaction.tax_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        # status stays COMPLETED
    else:
        # Full refund: the sale is reversed entirely and drops out of sales totals.
        transaction.status = TransactionStatus.REFUNDED

    # Add refund note with cashier info
    cashier_name = current_user.get('preferred_username', 'Unknown')
    label = "PARTIAL REFUND" if is_partial else "REFUNDED"
    refund_note = f"{label}: CHF {refund_amount} cash back | Reason: {refund.reason} | Processed by: {cashier_name} | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"

    if transaction.notes:
        transaction.notes = f"{transaction.notes}\n{refund_note}"
    else:
        transaction.notes = refund_note

    # Zero perpetual inventory: a refund moves money only — there's no stock count to
    # put back on the shelf. The refund is recorded in the transaction notes above.

    await db.commit()
    await db.refresh(transaction)

    logger.info(f"Refund processed: {transaction.transaction_number} - CHF {refund_amount} by {cashier_name}")
    return transaction


# ================================================================
# REPORTING ENDPOINTS
# ================================================================

@router.get("/reports/daily-summary", response_model=DailySummary)
async def get_daily_summary(
    report_date: Optional[str] = None,
    mine: bool = False,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Get daily sales summary - accessible by any POS role (cashiers need it for closeout).

    mine=true filters to the CALLER's own sales (so a cashier's dashboard shows their
    own takings, not the whole store). Default false = store-wide (for managers/Felix)."""
    # Default to today — in the SHOP's timezone, not the server's (a UTC box would roll
    # the day over at 01:00/02:00 Swiss time and split the evening's takings across two reports).
    if not report_date:
        target_date = datetime.now(SHOP_TZ).date()
    else:
        target_date = datetime.strptime(report_date, "%Y-%m-%d").date()

    # The day window is the shop's local calendar day, tz-aware, so it compares correctly
    # against the tz-aware (UTC) completed_at column in Postgres.
    start_of_day = datetime.combine(target_date, datetime.min.time(), tzinfo=SHOP_TZ)
    end_of_day = datetime.combine(target_date, datetime.max.time(), tzinfo=SHOP_TZ)

    conditions = [
        TransactionModel.status == TransactionStatus.COMPLETED,
        TransactionModel.completed_at >= start_of_day,
        TransactionModel.completed_at <= end_of_day,
    ]
    if mine:
        conditions.append(TransactionModel.cashier_id == await _resolve_cashier_uid(db, current_user))

    result = await db.execute(select(TransactionModel).where(and_(*conditions)))
    transactions = result.scalars().all()

    # Calculate totals
    total_sales = sum(t.total for t in transactions)
    vat_total = sum(t.tax_amount for t in transactions)
    cash_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.CASH)
    visa_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.VISA)
    debit_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.DEBIT)
    twint_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.TWINT)
    bank_transfer_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.BANK_TRANSFER)
    crypto_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.CRYPTO)
    other_total = sum(t.total for t in transactions if t.payment_method == PaymentMethod.OTHER)

    # Promotional treats given free today: count + their cost (COGS, for Felix's tax).
    giveaway_count = 0
    giveaway_cost = Decimal("0.00")
    tx_ids = [t.id for t in transactions]
    if tx_ids:
        gv = await db.execute(
            select(LineItemModel.quantity, ProductModel.cost)
            .join(ProductModel, ProductModel.id == LineItemModel.product_id, isouter=True)
            .where(and_(LineItemModel.transaction_id.in_(tx_ids), LineItemModel.is_giveaway == True))
        )
        for qty, cost in gv.all():
            q = int(qty or 0)
            giveaway_count += q
            giveaway_cost += Decimal(str(cost or 0)) * q

    # Swiss VAT split (INC3): the two turnover streams the FTA wants booked apart —
    # standard-rated (8.1%: dine-in cafe + all retail/alcohol/tobacco) vs reduced-rated
    # (2.6%: takeaway cafe food/drink). Computed per-transaction from the line snapshots so
    # each sale's cart-wide discount is prorated correctly, then summed across the day.
    vat_standard = vat_reduced = turnover_standard = turnover_reduced = Decimal("0.00")
    # P3 N-rate: also accumulate the per-code streams so the closeout/reports VAT rows can LOOP
    # over any number of rates. For CH this is exactly {A, B} and reconciles to the scalars above.
    _streams_acc: dict = {}
    if tx_ids:
        # Piece C: the tenant's rate table drives the Z-report streams. CH shop w/ NULL vat_rates →
        # CH config table → the same A/B split (8.1/2.6) this loop produced before (byte-identical).
        _rate_table = await _tenant_rate_table(db)
        _money = {t.id: (t.total, t.subtotal) for t in transactions}
        _lrows = (await db.execute(
            select(LineItemModel.transaction_id, LineItemModel.vat_rate, LineItemModel.line_total)
            .where(LineItemModel.transaction_id.in_(tx_ids))
        )).all()
        from collections import defaultdict as _dd
        _bytx: dict = _dd(list)
        for _txid, _rate, _lt in _lrows:
            _bytx[_txid].append((_rate, _lt))
        for _txid, _lines in _bytx.items():
            _tot, _sub = _money.get(_txid, (Decimal("0"), Decimal("0")))
            _sp = split_vat(_lines, _tot, _sub, rate_table=_rate_table)
            vat_standard += _sp["vat_standard"]; vat_reduced += _sp["vat_reduced"]
            turnover_standard += _sp["turnover_standard"]; turnover_reduced += _sp["turnover_reduced"]
            for _code, _st in _sp["vat_streams"].items():
                _acc = _streams_acc.setdefault(_code, {
                    "code": _code, "label": _st["label"], "rate": _st["rate"],
                    "turnover": Decimal("0.00"), "vat": Decimal("0.00")})
                _acc["turnover"] += _st["turnover"]; _acc["vat"] += _st["vat"]
    # Order standard (highest rate) first, matching the CH A→B reading order.
    vat_streams = sorted(_streams_acc.values(), key=lambda s: s["rate"], reverse=True)

    # Best sellers + units sold today (catalog products + custom lines, excl. free treats).
    # The leaderboard fills the once-empty "Top Seller" + gives items-sold for free.
    top_seller = None
    top_seller_quantity = None
    top_sellers: list[dict] = []
    items_sold = 0
    if tx_ids:
        name_expr = func.coalesce(ProductModel.name, LineItemModel.notes, "Item")
        rows = (await db.execute(
            select(name_expr.label("name"), func.sum(LineItemModel.quantity).label("qty"))
            .join(ProductModel, ProductModel.id == LineItemModel.product_id, isouter=True)
            .where(and_(
                LineItemModel.transaction_id.in_(tx_ids),
                LineItemModel.is_giveaway == False,
            ))
            .group_by(name_expr)
            .order_by(func.sum(LineItemModel.quantity).desc())
        )).all()
        items_sold = sum(int(r.qty or 0) for r in rows)
        top_sellers = [{"name": r.name, "quantity": int(r.qty)} for r in rows[:3]]
        if top_sellers:
            top_seller = top_sellers[0]["name"]
            top_seller_quantity = top_sellers[0]["quantity"]

    # Average basket.
    n = len(transactions)
    average_sale = (Decimal(str(total_sales)) / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if n else Decimal("0.00")

    # Busiest hour (by transaction count) — a velocity hint.
    busiest_hour = None
    if transactions:
        from collections import Counter
        hrs = Counter(t.completed_at.hour for t in transactions if t.completed_at)
        if hrs:
            h = hrs.most_common(1)[0][0]
            busiest_hour = f"{h:02d}:00–{(h + 1) % 24:02d}:00"

    # Per-cashier takings today, resolved to names (BL-83: cashier_id = users.id).
    cashier_performance: dict = {}
    _raw: dict = {}
    for t in transactions:
        if t.cashier_id:
            _raw[t.cashier_id] = _raw.get(t.cashier_id, Decimal("0")) + Decimal(str(t.total))
    if _raw:
        urows = await db.execute(
            select(UserModel.id, UserModel.first_name, UserModel.username).where(UserModel.id.in_(_raw.keys())))
        nm = {uid: (first or uname) for uid, first, uname in urows.all()}
        cashier_performance = {(nm.get(cid) or str(cid)[:8]): amt for cid, amt in _raw.items()}

    return DailySummary(
        top_seller=top_seller,
        top_seller_quantity=top_seller_quantity,
        top_sellers=top_sellers,
        items_sold=items_sold,
        average_sale=average_sale,
        busiest_hour=busiest_hour,
        cashier_performance=cashier_performance,
        date=target_date.isoformat(),
        total_transactions=len(transactions),
        total_sales=Decimal(str(total_sales)),
        vat_total=Decimal(str(vat_total)),
        vat_standard=vat_standard,
        vat_reduced=vat_reduced,
        turnover_standard=turnover_standard,
        turnover_reduced=turnover_reduced,
        vat_streams=vat_streams,
        cash_total=Decimal(str(cash_total)),
        visa_total=Decimal(str(visa_total)),
        debit_total=Decimal(str(debit_total)),
        twint_total=Decimal(str(twint_total)),
        bank_transfer_total=Decimal(str(bank_transfer_total)),
        crypto_total=Decimal(str(crypto_total)),
        other_total=Decimal(str(other_total)),
        giveaway_count=giveaway_count,
        giveaway_cost=giveaway_cost,
    )


@router.get("/reports/daily-summary.csv")
async def get_daily_summary_csv(
    report_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Daily sales as a Banana Accounting 'Income & Expenses' CSV -- one quoted line per payment
    method that took money. Felix imports it straight into Banana instead of re-typing totals by
    hand. Account + VatCode are intentionally left blank: Felix maps them to his chart of accounts
    in Banana's import dialog (we pre-fill his real codes once he hands them over)."""
    import csv as _csv
    import io as _io

    summary = await get_daily_summary(report_date=report_date, db=db, current_user=current_user)
    by_method = [
        ("Cash", summary.cash_total),
        ("TWINT", summary.twint_total),
        ("Visa", summary.visa_total),
        ("Debit", summary.debit_total),
        ("Bank transfer", summary.bank_transfer_total),
        ("Crypto", summary.crypto_total),
        ("Other", summary.other_total),
    ]
    buf = _io.StringIO()
    writer = _csv.writer(buf, quoting=_csv.QUOTE_ALL)
    # Two extra columns (Turnover, VAT) carry the VAT-summary NUMBERS in their own cells — the
    # accounting rows leave them blank, so Banana's import (which maps Income/Expenses) is
    # untouched, but Felix sees real number columns in the file + the on-screen viewer.
    writer.writerow(["Date", "Description", "Income", "Expenses", "Account", "VatCode", "Turnover", "VAT"])
    for label, amount in by_method:
        if amount and amount > 0:
            writer.writerow([summary.date, f"POS daily sales - {label}", f"{amount:.2f}", "", "", "", "", ""])
    # Promotional treats given free -- the cost is an expense (COGS) for tax.
    if summary.giveaway_cost and summary.giveaway_cost > 0:
        writer.writerow([summary.date,
                         f"POS giveaways (treats) x{summary.giveaway_count} - cost",
                         "", f"{summary.giveaway_cost:.2f}", "", "", "", ""])

    # --- VAT SUMMARY (BL-20 follow-up — proposal for Felix) ---------------------------------
    # Reference only — the numbers sit in the Turnover/VAT columns (Income/Expenses stay blank),
    # so they never touch Banana's income/expense sum on import. Per-country aware (CH: 8.1% /
    # 2.6%; streams come from the same resolver the receipt + closeout use). If Felix wants it
    # out of the accounting file we split it to its own report; if it's perfect, it stays.
    writer.writerow(["", "— VAT SUMMARY (reference only, not imported) —", "", "", "", "", "", ""])
    writer.writerow([summary.date, "Total sales incl. VAT", "", "", "", "", f"{summary.total_sales:.2f}", ""])
    writer.writerow([summary.date, "VAT total (contained in sales)", "", "", "", "", "", f"{summary.vat_total:.2f}"])
    streams = summary.vat_streams or []
    if streams:
        for s in streams:
            rate, label = s.get("rate"), (s.get("label") or "")
            turn, vat = float(s.get("turnover") or 0), float(s.get("vat") or 0)
            writer.writerow([summary.date, f"VAT {rate}% ({label})", "", "", "", str(rate),
                             f"{turn:.2f}", f"{vat:.2f}"])
    else:
        # Fallback to the CH standard/reduced split if the per-code streams aren't populated.
        if summary.turnover_standard or summary.vat_standard:
            writer.writerow([summary.date, "VAT standard (8.1%)", "", "", "", "8.1",
                             f"{summary.turnover_standard:.2f}", f"{summary.vat_standard:.2f}"])
        if summary.turnover_reduced or summary.vat_reduced:
            writer.writerow([summary.date, "VAT reduced (2.6%)", "", "", "", "2.6",
                             f"{summary.turnover_reduced:.2f}", f"{summary.vat_reduced:.2f}"])

    filename = f"banana-{summary.date}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ================================================================
# PRODUCT-SALES + CUSTOMER DRILL-DOWNS (Felix day-one wishlist, read-only)
# Windows onto data we already capture: line items already carry product +
# qty + line_total; transactions already carry customer_id. No new writes.
# See docs/BANCO-DAY-ONE-WISHLIST.md. Manager/admin only.
# ================================================================

# Manager-tier guard reused across the drill-down reports.
_REPORT_ROLES = ["👔️ pos-manager", "🛠️ pos-developer", "👑️ pos-admin"]


def _parse_report_range(date_from: Optional[str], date_to: Optional[str]):
    """Resolve an inclusive [from, to] day range in the SHOP's timezone (defaults to
    today). Returns (d_from, d_to, start_dt, end_dt) — the datetimes are tz-aware so
    they compare correctly against the UTC completed_at column, same as daily-summary."""
    today = datetime.now(SHOP_TZ).date()
    d_from = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else today
    d_to = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else d_from
    if d_to < d_from:
        d_from, d_to = d_to, d_from
    start = datetime.combine(d_from, datetime.min.time(), tzinfo=SHOP_TZ)
    end = datetime.combine(d_to, datetime.max.time(), tzinfo=SHOP_TZ)
    return d_from, d_to, start, end


@router.get("/reports/product-sales")
async def get_product_sales(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(_REPORT_ROLES)),
):
    """What actually sold over a date range — per product, by quantity AND revenue.

    Answers Felix's most-likely first question ('what did I sell this week?'). Read-only
    aggregate over completed sales' line items; giveaways excluded from revenue. Each row
    drills to 'who bought it' via /reports/product-sales/{product_id}. Custom (off-catalog)
    lines have no product_id and group by their name — they show but don't drill."""
    d_from, d_to, start, end = _parse_report_range(date_from, date_to)

    tx_rows = (await db.execute(
        select(TransactionModel.id).where(and_(
            TransactionModel.status == TransactionStatus.COMPLETED,
            TransactionModel.completed_at >= start,
            TransactionModel.completed_at <= end,
        ))
    )).all()
    tx_ids = [r[0] for r in tx_rows]
    if not tx_ids:
        return {"date_from": d_from.isoformat(), "date_to": d_to.isoformat(),
                "products": [], "categories": [],
                "totals": {"qty_sold": 0, "revenue": 0.0, "vat": 0.0, "product_count": 0}}

    name_expr = func.coalesce(ProductModel.name, LineItemModel.notes, "Item")
    cat_expr = func.coalesce(ProductModel.category, "Uncategorized")
    rows = (await db.execute(
        select(
            LineItemModel.product_id.label("product_id"),
            name_expr.label("name"),
            cat_expr.label("category"),
            func.sum(LineItemModel.quantity).label("qty"),
            func.sum(LineItemModel.line_total).label("revenue"),
            func.coalesce(func.sum(LineItemModel.vat_amount), 0).label("vat"),
            func.count(func.distinct(LineItemModel.transaction_id)).label("txns"),
        )
        .join(ProductModel, ProductModel.id == LineItemModel.product_id, isouter=True)
        .where(and_(
            LineItemModel.transaction_id.in_(tx_ids),
            LineItemModel.is_giveaway == False,
        ))
        .group_by(LineItemModel.product_id, name_expr, cat_expr)
        .order_by(func.sum(LineItemModel.line_total).desc())
    )).all()

    products = []
    cat_tot: dict = {}
    tot_qty = 0
    tot_rev = Decimal("0.00")
    tot_vat = Decimal("0.00")
    for r in rows:
        rev = Decimal(str(r.revenue or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        vat = Decimal(str(r.vat or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        qty = int(r.qty or 0)
        products.append({
            "product_id": str(r.product_id) if r.product_id else None,
            "name": r.name,
            "category": r.category,
            "qty_sold": qty,
            "revenue": float(rev),
            "vat": float(vat),
            "txn_count": int(r.txns or 0),
        })
        tot_qty += qty
        tot_rev += rev
        tot_vat += vat
        c = cat_tot.setdefault(r.category, {"qty_sold": 0, "revenue": Decimal("0.00")})
        c["qty_sold"] += qty
        c["revenue"] += rev

    from src.services.catalog_taxonomy import category_emoji
    categories = sorted(
        [{"category": k, "emoji": category_emoji(k),
          "qty_sold": v["qty_sold"], "revenue": float(v["revenue"])}
         for k, v in cat_tot.items()],
        key=lambda x: x["revenue"], reverse=True)

    return {
        "date_from": d_from.isoformat(),
        "date_to": d_to.isoformat(),
        "products": products,
        "categories": categories,
        "totals": {"qty_sold": tot_qty, "revenue": float(tot_rev),
                   "vat": float(tot_vat), "product_count": len(products)},
    }


@router.get("/reports/product-sales/{product_id}")
async def get_product_sales_detail(
    product_id: UUID,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(_REPORT_ROLES)),
):
    """Who bought this product in the window — one row per sale it appeared in
    (time, cashier, customer, qty, line total). The drill behind a product-sales row."""
    d_from, d_to, start, end = _parse_report_range(date_from, date_to)

    rows = (await db.execute(
        select(
            TransactionModel.id,
            TransactionModel.transaction_number,
            TransactionModel.completed_at,
            TransactionModel.cashier_id,
            TransactionModel.customer_id,
            LineItemModel.quantity,
            LineItemModel.line_total,
        )
        .join(TransactionModel, TransactionModel.id == LineItemModel.transaction_id)
        .where(and_(
            LineItemModel.product_id == product_id,
            LineItemModel.is_giveaway == False,
            TransactionModel.status == TransactionStatus.COMPLETED,
            TransactionModel.completed_at >= start,
            TransactionModel.completed_at <= end,
        ))
        .order_by(TransactionModel.completed_at.desc())
    )).all()

    # Resolve cashier + customer display names in batch (BL-83: cashier_id = users.id).
    cashier_ids = {r.cashier_id for r in rows if r.cashier_id}
    customer_ids = {r.customer_id for r in rows if r.customer_id}
    cashier_nm: dict = {}
    if cashier_ids:
        urows = await db.execute(select(UserModel.id, UserModel.first_name, UserModel.username)
                                 .where(UserModel.id.in_(cashier_ids)))
        cashier_nm = {uid: (first or uname) for uid, first, uname in urows.all()}
    customer_nm: dict = {}
    if customer_ids:
        crows = await db.execute(select(CustomerModel.id, CustomerModel.handle, CustomerModel.real_name)
                                 .where(CustomerModel.id.in_(customer_ids)))
        customer_nm = {cid: (handle or real or "Member") for cid, handle, real in crows.all()}

    prod_name = (await db.execute(
        select(ProductModel.name).where(ProductModel.id == product_id))).scalar_one_or_none()

    sales = [{
        "transaction_id": str(r.id),
        "transaction_number": r.transaction_number,
        "time": r.completed_at.isoformat() if r.completed_at else None,
        "cashier_name": cashier_nm.get(r.cashier_id, "—") if r.cashier_id else "—",
        "customer_name": customer_nm.get(r.customer_id) if r.customer_id else None,
        "qty": int(r.quantity or 0),
        "line_total": float(Decimal(str(r.line_total or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
    } for r in rows]

    return {
        "product_id": str(product_id),
        "product_name": prod_name or "Item",
        "date_from": d_from.isoformat(),
        "date_to": d_to.isoformat(),
        "sales": sales,
        "total_qty": sum(s["qty"] for s in sales),
        "total_revenue": float(sum((Decimal(str(s["line_total"])) for s in sales), Decimal("0.00"))),
    }


@router.get("/reports/category-sales")
async def get_category_sales_detail(
    category: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(_REPORT_ROLES)),
):
    """Who bought items in this category in the window — one row per sale a product
    of that category appeared in. The drill behind a 'By category' pill. Same shape
    as the product drill so the buyer-card panel can render it unchanged."""
    d_from, d_to, start, end = _parse_report_range(date_from, date_to)

    rows = (await db.execute(
        select(
            TransactionModel.id,
            TransactionModel.transaction_number,
            TransactionModel.completed_at,
            TransactionModel.cashier_id,
            TransactionModel.customer_id,
            LineItemModel.quantity,
            LineItemModel.line_total,
        )
        .join(TransactionModel, TransactionModel.id == LineItemModel.transaction_id)
        .join(ProductModel, ProductModel.id == LineItemModel.product_id)
        .where(and_(
            ProductModel.category == category,
            LineItemModel.is_giveaway == False,
            TransactionModel.status == TransactionStatus.COMPLETED,
            TransactionModel.completed_at >= start,
            TransactionModel.completed_at <= end,
        ))
        .order_by(TransactionModel.completed_at.desc())
    )).all()

    cashier_ids = {r.cashier_id for r in rows if r.cashier_id}
    customer_ids = {r.customer_id for r in rows if r.customer_id}
    cashier_nm: dict = {}
    if cashier_ids:
        urows = await db.execute(select(UserModel.id, UserModel.first_name, UserModel.username)
                                 .where(UserModel.id.in_(cashier_ids)))
        cashier_nm = {uid: (first or uname) for uid, first, uname in urows.all()}
    customer_nm: dict = {}
    if customer_ids:
        crows = await db.execute(select(CustomerModel.id, CustomerModel.handle, CustomerModel.real_name)
                                 .where(CustomerModel.id.in_(customer_ids)))
        customer_nm = {cid: (handle or real or "Member") for cid, handle, real in crows.all()}

    sales = [{
        "transaction_id": str(r.id),
        "transaction_number": r.transaction_number,
        "time": r.completed_at.isoformat() if r.completed_at else None,
        "cashier_name": cashier_nm.get(r.cashier_id, "—") if r.cashier_id else "—",
        "customer_name": customer_nm.get(r.customer_id) if r.customer_id else None,
        "qty": int(r.quantity or 0),
        "line_total": float(Decimal(str(r.line_total or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
    } for r in rows]

    from src.services.catalog_taxonomy import category_emoji
    return {
        "category": category,
        "emoji": category_emoji(category),
        "product_name": category,
        "date_from": d_from.isoformat(),
        "date_to": d_to.isoformat(),
        "sales": sales,
        "total_qty": sum(s["qty"] for s in sales),
        "total_revenue": float(sum((Decimal(str(s["line_total"])) for s in sales), Decimal("0.00"))),
    }


# A product is "half-baked" if it SOLD but is still missing the two things a cashier's lean
# quick-add can't be trusted to fill: a real category (not the "On the fly" placeholder / blank)
# and a cost (no cost = margin-blind). These are the objective gaps that keep an item in the
# cleanup queue; 18+ and photo are surfaced for review but don't gate (a manager confirms them
# while they're in there). This is the safety net that makes the lean quick-add safe — nothing a
# cashier rings in a rush falls through permanently.
_HALFBAKED_CATEGORIES = ("On the fly", "On The Fly", "on the fly")

# BL-98 — the ENRICHMENT (bench) gaps. The cockpit has two MODES over the same shape:
#
#   mode=sold  — the original safety net: products that SOLD but are still half-baked.
#                Reactive. Gates on category + cost (what a cashier's lean quick-add misses).
#   mode=bench — the migration workbench: EVERY active product that isn't finished, sold or
#                not. Proactive. Gates on the four things a master-data record needs to be
#                real: a photo, a description, a true category, and a cost.
#
# NOTE we deliberately do NOT gate on `product_class`: it is NOT NULL with default "standard",
# so every row always has one — gating on it would flag nothing. The class is decided by
# `catalog_taxonomy.classify` at enrich time, and 18+ is surfaced here for REVIEW, not re-keyed.
#
# The gap clause lives in SQL (not a Python filter) so the batch, the "remaining" count and the
# "done / total" progress counter are all computed from ONE definition and can never disagree.


def _bench_category_expr():
    """Trimmed category, '' when NULL — the value the gap test and the ordering both use."""
    return func.coalesce(func.trim(ProductModel.category), "")


def _bench_gap_clause():
    """A product is UNFINISHED (on the bench) if it's missing any of the four. One definition,
    reused by the item query AND the counts — so the counter can never drift from the list."""
    cat = _bench_category_expr()
    return or_(
        func.coalesce(func.trim(ProductModel.image_url), "") == "",     # no photo
        func.coalesce(func.trim(ProductModel.description), "") == "",   # no description
        cat == "",                                                       # no category
        func.lower(cat).in_([c.lower() for c in _HALFBAKED_CATEGORIES]),  # placeholder category
        ProductModel.cost.is_(None),                                     # margin-blind
    )


@router.get("/catalog/cleanup-queue")
async def get_cleanup_queue(
    mode: str = "sold",
    limit: int = 20,
    offset: int = 0,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """The catalog cockpit — manager/admin. TWO MODES, same card, same inline fix:

    • mode=sold  (default) — SOLD-but-half-baked. The reactive safety net: nothing a cashier
      rings in a rush falls through permanently. Busiest gaps first. Unpaginated (naturally small).

    • mode=bench (BL-98) — the ENRICHMENT QUEUE. The migration workbench: hand me the next N
      unfinished products (photo / description / category / cost), sold or not, ordered so you
      work a SHELF at a time. Returns the done/total counter that replaces the paper binder.

    Cashier never edits the catalog/cost — they ring it in; the manager sets it up here."""
    if mode == "bench":
        return await _bench_queue(db, limit=limit, offset=offset, category=category)

    # ---- mode=sold (original) ------------------------------------------------------------
    # Units + revenue + last-sold per real product, over ALL completed sales (giveaways excluded).
    sold = (await db.execute(
        select(
            LineItemModel.product_id.label("pid"),
            func.sum(LineItemModel.quantity).label("qty"),
            func.sum(LineItemModel.line_total).label("revenue"),
            func.max(TransactionModel.completed_at).label("last_sold"),
            func.count(func.distinct(LineItemModel.transaction_id)).label("txns"),
        )
        .join(TransactionModel, TransactionModel.id == LineItemModel.transaction_id)
        .where(and_(
            TransactionModel.status == TransactionStatus.COMPLETED,
            LineItemModel.product_id.isnot(None),
            LineItemModel.is_giveaway == False,
        ))
        .group_by(LineItemModel.product_id)
    )).all()
    if not sold:
        return {"items": [], "count": 0}

    sold_by_pid = {r.pid: r for r in sold}
    products = (await db.execute(
        select(ProductModel).where(and_(
            ProductModel.id.in_(list(sold_by_pid.keys())),
            ProductModel.is_active == True,
        ))
    )).scalars().all()

    from src.services.catalog_taxonomy import category_emoji
    items = []
    for p in products:
        cat = (p.category or "").strip()
        gap_category = (cat == "") or (cat in _HALFBAKED_CATEGORIES)
        gap_cost = p.cost is None
        if not (gap_category or gap_cost):
            continue  # fully set up — not in the queue
        s = sold_by_pid[p.id]
        items.append({
            "product_id": str(p.id),
            "name": p.name,
            "sku": p.sku,
            "category": p.category,
            "price": float(p.price) if p.price is not None else None,
            "cost": float(p.cost) if p.cost is not None else None,
            "is_age_restricted": bool(p.is_age_restricted),
            "product_class": p.product_class,
            "image_url": p.image_url,
            "qty_sold": int(s.qty or 0),
            "revenue": float(Decimal(str(s.revenue or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "txn_count": int(s.txns or 0),
            "last_sold": s.last_sold.isoformat() if s.last_sold else None,
            "gaps": {
                "category": gap_category,
                "cost": gap_cost,
                "photo": not p.image_url,   # soft — shown, not gated
            },
        })
    # Busiest gaps first: most units sold = most urgent to tidy.
    items.sort(key=lambda x: (x["qty_sold"], x["revenue"]), reverse=True)
    return {"items": items, "count": len(items), "mode": "sold"}


async def _bench_queue(db: AsyncSession, *, limit: int, offset: int, category: Optional[str]):
    """BL-98 ENRICHMENT QUEUE — the migration workbench (back office, not the till).

    Hands back the next `limit` UNFINISHED products plus the progress counter. Ordered by
    category then name, so a batch is a SHELF: you pull twenty bongs off the shelf, work them,
    and the queue hands you the next twenty from the same place. Uncategorised items sort first
    (they need the most work). Optional `category` narrows it to one shelf.

    The `done / total` counter this returns is the number that replaces the paper binder —
    it is a QUERY, so it is always true, where a hand-filed binder rots the day a price changes.
    """
    limit = max(1, min(limit, 100))     # a bench holds a batch, not a catalog
    offset = max(0, offset)

    scope = [ProductModel.is_active == True]
    if category:
        scope.append(func.lower(_bench_category_expr()) == category.strip().lower())

    gap = _bench_gap_clause()

    total = (await db.execute(
        select(func.count()).select_from(ProductModel).where(and_(*scope))
    )).scalar_one()
    remaining = (await db.execute(
        select(func.count()).select_from(ProductModel).where(and_(*scope, gap))
    )).scalar_one()

    rows = (await db.execute(
        select(ProductModel)
        .where(and_(*scope, gap))
        .order_by(_bench_category_expr().asc(), ProductModel.name.asc())
        .limit(limit).offset(offset)
    )).scalars().all()

    items = []
    for p in rows:
        cat = (p.category or "").strip()
        items.append({
            "product_id": str(p.id),
            "name": p.name,
            "sku": p.sku,
            "barcode": p.barcode,
            "category": p.category,
            "description": p.description,
            "price": float(p.price) if p.price is not None else None,
            "cost": float(p.cost) if p.cost is not None else None,
            "is_age_restricted": bool(p.is_age_restricted),
            "product_class": p.product_class,
            "image_url": p.image_url,
            # Same shape the sold-mode card already renders, so the UI reuses one template.
            "qty_sold": 0,
            "revenue": 0.0,
            "txn_count": 0,
            "last_sold": None,
            "gaps": {
                "category": (cat == "") or (cat in _HALFBAKED_CATEGORIES),
                "cost": p.cost is None,
                "photo": not (p.image_url or "").strip(),
                "description": not (p.description or "").strip(),
            },
        })

    return {
        "items": items,
        "count": len(items),
        "mode": "bench",
        "total": int(total),                        # every active product in scope
        "remaining": int(remaining),                # still unfinished
        "done": int(total) - int(remaining),        # the counter: done / total
        "limit": limit,
        "offset": offset,
        "category": category,
    }


@router.get("/customers/{customer_id}/summary")
async def get_customer_summary(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(_REPORT_ROLES)),
):
    """One customer's at-a-glance: tier, lifetime value, visit stats, and what they
    usually buy. Read-only over the data we already write (transactions carry customer_id;
    the customer record carries tier + lifetime_spend). The detail behind the Customer
    column that currently dead-ends. Full purchase list = /transactions?customer_id=."""
    cust = (await db.execute(
        select(CustomerModel).where(CustomerModel.id == customer_id))).scalar_one_or_none()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    txs = (await db.execute(
        select(TransactionModel).where(and_(
            TransactionModel.customer_id == customer_id,
            TransactionModel.status == TransactionStatus.COMPLETED,
        )).order_by(TransactionModel.completed_at.desc())
    )).scalars().all()

    visit_count = len(txs)
    spent = sum((Decimal(str(t.total)) for t in txs), Decimal("0.00"))
    avg_basket = (spent / visit_count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if visit_count else Decimal("0.00")
    dates = [t.completed_at for t in txs if t.completed_at]
    first_seen = min(dates).isoformat() if dates else None
    last_seen = max(dates).isoformat() if dates else None

    top_items: list = []
    tx_ids = [t.id for t in txs]
    if tx_ids:
        name_expr = func.coalesce(ProductModel.name, LineItemModel.notes, "Item")
        irows = (await db.execute(
            select(name_expr.label("name"), func.sum(LineItemModel.quantity).label("qty"))
            .join(ProductModel, ProductModel.id == LineItemModel.product_id, isouter=True)
            .where(and_(LineItemModel.transaction_id.in_(tx_ids), LineItemModel.is_giveaway == False))
            .group_by(name_expr).order_by(func.sum(LineItemModel.quantity).desc())
        )).all()
        top_items = [{"name": r.name, "qty": int(r.qty or 0)} for r in irows[:5]]

    return {
        "id": str(cust.id),
        "handle": cust.handle,
        "real_name": cust.real_name,
        "loyalty_tier": cust.loyalty_tier.value if cust.loyalty_tier else None,
        "tier_discount_percent": cust.tier_discount_percent,
        "lifetime_spend": float(Decimal(str(cust.lifetime_spend or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "credits_balance": cust.credits_balance,
        "crack_level": cust.crack_level.value if cust.crack_level else None,
        "is_vip": cust.is_vip,
        "first_seen": first_seen,
        "last_seen": last_seen,
        "visit_count": visit_count,
        "spend_in_system": float(spent.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "avg_basket": float(avg_basket),
        "top_items": top_items,
    }


# ================================================================
# STORE SETTINGS ENDPOINTS
# ================================================================

@router.get("/settings/{store_number}", response_model=StoreSettingsRead)
async def get_store_settings(
    store_number: int = 1,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """
    Get store settings for a specific store number (any POS role).

    Used by frontend to:
    - Get current VAT rate
    - Display company info
    - Load discount limits
    - Show customer loyalty tiers
    """
    result = await db.execute(
        select(StoreSettingsModel).where(StoreSettingsModel.store_number == store_number)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(status_code=404, detail=f"Store #{store_number} not found")

    # Piece C: the editor pre-fills from the EFFECTIVE rate table. A CH shop with no stored table
    # (vat_rates NULL) gets the CH config default (8.1/2.6) to edit — but nothing is persisted until
    # the user actually saves. resolve_regime returns the stored table when present, else CH default.
    read = StoreSettingsRead.model_validate(settings)
    if not read.vat_rates:
        read.vat_rates = resolve_regime(settings)["vat_rates"]
    return read


@router.put("/settings/{store_number}", response_model=StoreSettingsRead)
async def update_store_settings(
    store_number: int,
    settings_update: StoreSettingsUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_manager_or_admin()),
):
    """
    Update store settings (manager or admin).

    A MANAGER may edit everything EXCEPT the discount limits — a manager must not be able to
    raise their own or a cashier's discount cap (self-cap risk), so those two fields are
    ADMIN-ONLY and stripped server-side for a manager (not just hidden in the UI). Everything
    else (company info, tax table, receipt, hours, graphics) is manager-editable. Admin: all.
    """
    result = await db.execute(
        select(StoreSettingsModel).where(StoreSettingsModel.store_number == store_number)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(status_code=404, detail=f"Store #{store_number} not found")

    # Update only provided fields
    update_data = settings_update.model_dump(exclude_unset=True)

    # Discount caps are ADMIN-ONLY (self-cap risk). A manager can save the rest of the settings,
    # but any attempt to change the discount limits is dropped here — the seal is on the SERVER,
    # not just the disabled UI field. (A manager's normal save resends the current values, which
    # are simply ignored; only an admin's change persists.)
    _roles = current_user.get("user_roles", []) or []
    _is_admin = any("pos-admin" in r for r in _roles)
    if not _is_admin:
        _admin_only = ("cashier_max_discount", "manager_max_discount",
                       "loyalty_tier1_threshold", "loyalty_tier1_discount",
                       "loyalty_tier2_threshold", "loyalty_tier2_discount",
                       "loyalty_tier3_threshold", "loyalty_tier3_discount")
        _dropped = [f for f in _admin_only if f in update_data]
        for f in _dropped:
            update_data.pop(f, None)
        if _dropped:
            logger.info(f"Settings save by non-admin {current_user.get('preferred_username')} — "
                        f"discount/loyalty fields ignored (admin-only): {_dropped}")

    # Piece C: the N-rate VAT table is stored as a JSON string. Validate the MENU server-side
    # (≥1 row, exactly 1 default, unique non-blank codes, numeric rates 0–100), then serialise. A CH
    # shop that never touches the Tax editor never sends this key → column stays NULL → byte-identical.
    # NOTE: this manages the rate LIST only; class→rate ASSIGNMENT (which product is 8.1/2.6, or 22/
    # 10/5/4 for IT) is a SEPARATE deferred layer — not decided here.
    if "vat_rates" in update_data:
        rows = update_data.pop("vat_rates")
        if rows is None:
            settings.vat_rates = None  # explicit clear → engine falls back to CH config default
        else:
            settings.vat_rates = _validate_and_serialize_vat_rates(rows)
            # Mirror the default row's rate into the legacy scalar so vat_rate stays the standard rate.
            _default_row = next((r for r in rows if r.get("default")), rows[0] if rows else None)
            if _default_row is not None:
                try:
                    settings.vat_rate = Decimal(str(_default_row["rate"]))
                except Exception:
                    pass

    for field, value in update_data.items():
        setattr(settings, field, value)

    settings.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(settings)

    logger.info(f"Store #{store_number} settings updated by {current_user['username']}")

    # Return the effective table so the editor re-fills cleanly (stored table, else CH config default).
    read = StoreSettingsRead.model_validate(settings)
    if not read.vat_rates:
        read.vat_rates = resolve_regime(settings)["vat_rates"]
    return read


# ================================================================
# SYSTEM PULSE -> the live shop card behind the 📊 in the status bar
# ================================================================
# Replaces a dead /health/dashboard link. One auth'd call returns a snapshot a
# cashier/manager actually cares about: today's takings, members, low stock, open
# drawers, catalog size -- plus the real build stamp + a DB heartbeat.

@router.get("/system/pulse")
async def system_pulse(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Live shop snapshot for the status-bar card. Best-effort: any sub-stat that
    errors degrades to None rather than failing the whole card."""
    db_ok = True
    today = None
    try:
        today = await get_daily_summary(db=db, current_user=current_user)
    except Exception:
        db_ok = False

    async def _count(stmt) -> Optional[int]:
        try:
            return int((await db.execute(stmt)).scalar() or 0)
        except Exception:
            return None

    members = await _count(select(func.count()).select_from(CustomerModel))
    catalog = await _count(
        select(func.count()).select_from(ProductModel).where(ProductModel.is_active == True))
    open_drawers = await _count(
        select(func.count()).select_from(CashShiftModel).where(
            CashShiftModel.status == CashShiftStatus.OPEN))

    settings = get_settings()
    return {
        "ok": True,
        "db": "ok" if db_ok else "fail",
        "shop": getattr(settings, "STORE_NAME", None) or "Artemis Store",
        "today": {
            "sales": float(today.total_sales) if today else None,
            "transactions": today.total_transactions if today else None,
            "vat": float(today.vat_total) if today else None,
            "giveaways": today.giveaway_count if today else None,
        },
        "members": members,
        "catalog": catalog,
        "open_drawers": open_drawers,
        "build": {
            "version": get_version(),
            "sha": get_git_sha(),
            "env": getattr(settings, "HX_ENVIRONMENT", "") or "",
        },
    }


# ================================================================
# IN-APP FEEDBACK -> Backlog board (the seatback card, built into the till)
# ================================================================
# A cashier reports a bug/idea from inside the POS; it lands as a real item on
# the SAME backlog board (/backlog) the La Piazza 💬 button feeds. The POS token
# (kc-pos-realm-dev) can't call the bottega feedback endpoint (different realm),
# so this is the POS-native twin -- same BacklogItemModel, tagged for Banco/POS.

class POSFeedback(BaseModel):
    kind: str = "other"      # bug | idea | other
    severity: str = "annoying"  # blocking | annoying | cosmetic  -> backlog priority
    title: str
    body: str = ""
    screenshot: Optional[str] = None       # base64 data-URL (image/*) of the screen
    attachments: Optional[list] = None     # user-attached files [{name,type,data}] -- images & PDFs
    meta: Optional[dict] = None            # auto-collected browser/screen/path context
    diagnostics: Optional[list] = None     # console/network breadcrumbs from the page


# Cap an attached screenshot so a runaway data-URL can't bloat the shared DB
# (~2.2 MB image after base64). Bigger than that -> drop the image, keep the report.
_MAX_SHOT_CHARS = 3_000_000
# User-attached files (device picker / mobile camera). PDFs + images only, each
# capped, and a small ceiling on count + total so a report can't bloat the DB.
_ATTACH_PREFIXES = ("data:image/", "data:application/pdf")
_MAX_ATTACH_CHARS = 6_000_000     # ~4.4 MB per file after base64 (PDFs run bigger)
_MAX_ATTACH_COUNT = 5             # at most this many files per report
_MAX_ATTACH_TOTAL = 18_000_000    # ~13 MB total across all files


def _clean_attachments(raw: list | None) -> list:
    """Keep only well-formed image/PDF data-URLs, within the per-file/count/total
    caps. Malformed or oversized entries are silently dropped -- the report still
    files. Returns a list of {name, type, data} dicts."""
    if not isinstance(raw, list) or not raw:
        return []
    out, total = [], 0
    for a in raw:
        if not isinstance(a, dict):
            continue
        data = a.get("data")
        if not (isinstance(data, str) and data.startswith(_ATTACH_PREFIXES)):
            continue
        if len(data) > _MAX_ATTACH_CHARS or total + len(data) > _MAX_ATTACH_TOTAL:
            continue
        total += len(data)
        name = str(a.get("name") or "attachment")[:200]
        mime = data.split(";", 1)[0][5:] or "application/octet-stream"  # strip "data:"
        out.append({"name": name, "type": mime, "data": data})
        if len(out) >= _MAX_ATTACH_COUNT:
            break
    return out
# One-tap severity -> backlog priority (so the board sorts itself; default MEDIUM).
_SEVERITY_PRIORITY = {
    "blocking": BacklogPriority.HIGH,
    "annoying": BacklogPriority.MEDIUM,
    "cosmetic": BacklogPriority.LOW,
}
_MAX_DIAG = 25  # cap how many breadcrumbs we fold in (the buffer is small anyway)
# Only these context keys are folded into the description (whitelist -- no surprises).
_META_LABELS = [
    ("path", "Screen"), ("referrer", "Came from"), ("app", "POS build"),
    ("user", "User"), ("userAgent", "Browser"), ("platform", "Platform"),
    ("viewport", "Viewport"), ("screen", "Screen size"), ("dpr", "Pixel ratio"),
    ("language", "Locale"), ("tz", "Timezone"), ("online", "Online"),
    ("when", "Client time"),
]


def _format_meta(meta: dict | None) -> str:
    """Render the auto-collected context as a readable block for the board."""
    if not isinstance(meta, dict):
        return ""
    lines = []
    for key, label in _META_LABELS:
        val = meta.get(key)
        if val is None or val == "":
            continue
        lines.append(f"{label}: {str(val)[:300]}")
    return ("\n\n🖥️ Context (auto-collected)\n" + "\n".join(lines)) if lines else ""


def _format_diagnostics(diag: list | None) -> str:
    """Render the console/network breadcrumbs -- the half of a bug a screenshot
    can't show. Each entry is {t: error|warn|net, m: message, ts: epoch_ms}."""
    if not isinstance(diag, list) or not diag:
        return ""
    icons = {"error": "❌", "warn": "⚠️", "net": "🌐"}
    lines = []
    for e in diag[-_MAX_DIAG:]:
        if not isinstance(e, dict):
            continue
        t = str(e.get("t", "")).lower()
        msg = str(e.get("m", "")).replace("\n", " ").strip()[:300]
        if not msg:
            continue
        lines.append(f"{icons.get(t, '•')} [{t or '?'}] {msg}")
    return ("\n\n🔎 Console & network (last events)\n" + "\n".join(lines)) if lines else ""


@router.post("/feedback")
async def pos_feedback(
    f: POSFeedback,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """File a bug/idea from the till onto the shared Backlog board (/backlog).

    Optionally carries an auto-captured screenshot + browser/screen context so a
    report arrives with its own forensics."""
    title = (f.title or "").strip()
    if len(title) < 3:
        raise HTTPException(status_code=400, detail="Give it a short title (3+ characters)")
    user = current_user.get("username") or current_user.get("preferred_username", "unknown")
    kind = (f.kind or "other").lower()
    if kind not in ("bug", "idea", "other"):
        kind = "other"
    item_type = BacklogItemType.BUG_FIX if kind == "bug" else BacklogItemType.BUSINESS_OPS
    severity = (f.severity or "annoying").lower()
    if severity not in _SEVERITY_PRIORITY:
        severity = "annoying"
    priority = _SEVERITY_PRIORITY[severity]

    # next BL number -- same shared sequence as backlog_router / bottega feedback
    next_number = (await db.execute(
        select(func.coalesce(func.max(BacklogItemModel.item_number), 0)))).scalar() + 1

    body = (f.body or "").strip()
    desc = (f"{body}\n\n— filed from Banco POS by {user}" if body
            else f"Filed from Banco POS by {user}")
    desc += _format_meta(f.meta)
    desc += _format_diagnostics(f.diagnostics)

    # Validate + bound the screenshot: must be an image data-URL, under the size cap.
    shot = f.screenshot
    has_shot = False
    if shot and isinstance(shot, str) and shot.startswith("data:image/") and len(shot) <= _MAX_SHOT_CHARS:
        has_shot = True
    elif shot:
        shot = None  # malformed or oversized -> drop the image, still file the report

    # User-attached files (device picker / mobile camera) -- images and PDFs.
    attachments = _clean_attachments(f.attachments)
    if attachments:
        names = ", ".join(a["name"] for a in attachments)
        desc += f"\n\n📎 Attachments ({len(attachments)})\n{names}"

    item = BacklogItemModel(
        item_number=next_number, title=title[:200], description=desc,
        item_type=item_type, application=HelixApplication.HELIXNET,
        priority=priority, created_by=user,
        tags=f"banco,feedback,pos,{kind},{severity}",
        screenshot_data=shot if has_shot else None,
        attachments=json.dumps(attachments) if attachments else None)
    db.add(item)
    await db.commit()
    logger.info(f"BL-{next_number:03d} filed from Banco POS by {user}: {title} "
                f"(severity={severity}, screenshot={has_shot}, attachments={len(attachments)})")
    return {"ok": True, "item_number": next_number, "ref": f"BL-{next_number:03d}",
            "screenshot": has_shot, "attachments": len(attachments),
            "severity": severity, "priority": priority.value}


def _decode_data_url(data_url):
    import base64 as _b64, re as _re
    m = _re.match(r"data:(image/[^;]+);base64,(.*)", data_url or "", _re.S)
    if not m:
        return None, None
    try:
        return _b64.b64decode(m.group(2)), m.group(1)
    except Exception:
        return None, None


@router.post("/feedback/triage")
async def triage_pending_feedback(
    limit: int = 5,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "👑️ pos-admin"])),
):
    """Hypercare PoC-2 — run the AI triage brain over feedback tickets that haven't been
    triaged yet, and write each clean version back as a BacklogActivity (dual-version:
    original untouched). The per-env cadence cron just curls this every N minutes.

    Runs INSIDE the app (working async session) — unlike a standalone script. Idempotent:
    a ticket that already has an `ai-triage` activity is skipped, so no re-triage/double-work."""
    from src.db.models.backlog_model import (BacklogActivityModel, BacklogActivityType,
                                             BacklogStatus)
    from src.db.models.pos_notification_model import POSNotificationModel
    from src.services.feedback_triage import triage_feedback

    # BL-011: triage tickets that (a) have NEVER been triaged, OR (b) were reopened / had detail
    # added by the reporter AFTER the last triage — so a reopen/comment RE-READS the spec instead
    # of staying frozen. Select COLUMNS, not the ORM entity — screenshot_data is deferred, and
    # lazy-loading it on an entity does sync IO in async context (MissingGreenlet).
    from sqlalchemy import func, or_
    _A = BacklogActivityModel
    _last_triage = (select(func.max(_A.created_at))
                    .where(_A.item_id == BacklogItemModel.id, _A.actor == "ai-triage")
                    .correlate(BacklogItemModel).scalar_subquery())
    _never = ~(select(_A.id).where(_A.item_id == BacklogItemModel.id, _A.actor == "ai-triage")
               .correlate(BacklogItemModel).exists())
    _newer_input = (select(_A.id)
                    .where(_A.item_id == BacklogItemModel.id,
                           _A.new_value.in_(["reporter-note", "reopened", "disputed"]),
                           _A.created_at > _last_triage)
                    .correlate(BacklogItemModel).exists())
    rows = (await db.execute(
        select(BacklogItemModel.id, BacklogItemModel.item_number, BacklogItemModel.title,
               BacklogItemModel.description, BacklogItemModel.screenshot_data,
               BacklogItemModel.created_by)
        .where(BacklogItemModel.tags.ilike("%feedback%"), or_(_never, _newer_input))
        .order_by(BacklogItemModel.created_at.desc())
        .limit(max(1, min(int(limit or 5), 25))))).all()

    # Which selected rows already have a triage (→ re-triage), + the reporter's follow-up text.
    prior_triage: set = set()
    extra_ctx: dict = {}
    _ids = [r.id for r in rows]
    if _ids:
        for a in (await db.execute(
                select(_A.item_id, _A.actor, _A.new_value, _A.comment)
                .where(_A.item_id.in_(_ids)))).all():
            if a.actor == "ai-triage":
                prior_triage.add(a.item_id)
            elif a.new_value in ("reporter-note", "reopened", "disputed") and a.comment:
                _txt = (a.comment or "").replace("📝 Reporter added: ", "").strip()
                if _txt:
                    extra_ctx.setdefault(a.item_id, []).append(_txt)

    # Dedup candidates: OPEN feedback tickets the new one might duplicate (number → row).
    cand_rows = (await db.execute(
        select(BacklogItemModel.id, BacklogItemModel.item_number, BacklogItemModel.title)
        .where(BacklogItemModel.tags.ilike("%feedback%"),
               BacklogItemModel.status.in_([BacklogStatus.PENDING,
                                            BacklogStatus.IN_PROGRESS])))).all()
    cand_by_num = {c.item_number: c for c in cand_rows}

    out = []
    merged_nums: set = set()   # archived-as-dup this run → never offer them as a canonical
    for r in rows:
        retriage = r.id in prior_triage   # BL-011: reopened / detail-added → re-read, don't re-dedup
        shot, mime = _decode_data_url(r.screenshot_data)
        desc = r.description or ""
        if retriage and extra_ctx.get(r.id):
            desc += ("\n\nREPORTER FOLLOW-UP (they reopened or added detail — re-read this and "
                     "UPDATE your understanding):\n- " + "\n- ".join(extra_ctx[r.id]))
        existing = [] if retriage else [{"n": c.item_number, "title": c.title} for c in cand_rows
                    if c.item_number != r.item_number and c.item_number not in merged_nums]
        res = await triage_feedback(
            title=r.title, description=desc, metadata=None,
            screenshot=shot, screenshot_mime=mime or "image/png", existing=existing)
        clean = res["clean"]
        dup = clean.get("duplicate_of") or 0
        is_dup = (not retriage and isinstance(dup, int) and dup > 0 and dup in cand_by_num
                  and dup != r.item_number and dup not in merged_nums)

        if is_dup:
            # MERGE: archive this one, breadcrumb the canonical, tell the reporter it's linked.
            # The merge marker is an `ai-triage` activity (so it counts as triaged → idempotent)
            # whose new_value `dup-of-N` is how the UIs detect a merged ticket. The breadcrumb on
            # the canonical uses actor `ai-dedup` so it never collides with triage detection.
            canonical = cand_by_num[dup]
            await db.execute(update(BacklogItemModel)
                             .where(BacklogItemModel.id == r.id)
                             .values(status=BacklogStatus.ARCHIVED))
            db.add(BacklogActivityModel(
                item_id=r.id, activity_type=BacklogActivityType.COMMENT, actor="ai-triage",
                old_value=(r.title or "")[:200], new_value=f"dup-of-{dup}",
                comment=json.dumps({"ai": res["ai"], "model": res["model"], "duplicate_of": dup,
                                    "original": {"title": r.title, "description": r.description},
                                    "clean": clean, "vision": res.get("vision")},
                                   ensure_ascii=False)))
            db.add(BacklogActivityModel(
                item_id=canonical.id, activity_type=BacklogActivityType.COMMENT, actor="ai-dedup",
                comment=f"🔁 Also reported by {r.created_by or 'someone'} (was BL-{r.item_number:03d})."))
            if r.created_by and r.created_by not in ("unknown", "ai-triage"):
                db.add(POSNotificationModel(
                    recipient=r.created_by, kind="dedup", item_number=r.item_number,
                    title="👀 Already on our radar",
                    body="Good catch — this was already reported. We've linked your report to it "
                         "and we'll let you know the moment it's fixed.",
                    link="/pos/my-tickets"))
            merged_nums.add(r.item_number)
            out.append({"item_number": r.item_number, "ai": res["ai"],
                        "clean_title": clean.get("title"), "duplicate_of": dup})
            continue

        # NORMAL: store the dual-version triage + ring "we're on it".
        # old/new_value are varchar(200) → short titles; the FULL payload lives in `comment` (Text).
        db.add(BacklogActivityModel(
            item_id=r.id, activity_type=BacklogActivityType.COMMENT, actor="ai-triage",
            old_value=(r.title or "")[:200],
            new_value=(clean.get("title") or "")[:200],
            comment=json.dumps({
                "ai": res["ai"], "model": res["model"],
                "original": {"title": r.title, "description": r.description},
                "clean": clean, "vision": res.get("vision"),
            }, ensure_ascii=False)))
        if r.created_by and r.created_by not in ("unknown", "ai-triage"):
            ct = (clean.get("title") or r.title or "your feedback")[:160]
            db.add(POSNotificationModel(
                recipient=r.created_by,
                kind="re-triaged" if retriage else "triaged", item_number=r.item_number,
                title="🔄 We re-read your update" if retriage else "🛠️ We're on it",
                body=(f"“{ct}” — we took another look and updated how we understand it. Tap to see."
                      if retriage else
                      f"“{ct}” — thanks, we're looking into it now. Tap to see how we understood it."),
                link="/pos/my-tickets"))
        out.append({"item_number": r.item_number, "ai": res["ai"], "retriage": retriage,
                    "clean_title": clean.get("title"), "type": clean.get("type"),
                    "severity": clean.get("severity"), "confidence": clean.get("confidence"),
                    "decipherable": clean.get("decipherable")})
    await db.commit()
    logger.info("Hypercare triage: processed %d pending feedback ticket(s)", len(out))
    return {"triaged": len(out), "items": out}


@router.get("/feedback/queue")
async def hypercare_queue(
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "👑️ pos-admin"])),
):
    """The Hypercare COCKPIT queue — feedback tickets with their AI triage (raw → cleaned),
    status, reporter, and a scorecard. Read-only; the cockpit page renders this."""
    from src.db.models.backlog_model import BacklogActivityModel
    rows = (await db.execute(
        select(BacklogItemModel.id, BacklogItemModel.item_number, BacklogItemModel.title,
               BacklogItemModel.description, BacklogItemModel.status, BacklogItemModel.priority,
               BacklogItemModel.created_by, BacklogItemModel.created_at,
               (BacklogItemModel.screenshot_data.isnot(None)).label("has_shot"))
        .where(BacklogItemModel.tags.ilike("%feedback%"))
        .order_by(BacklogItemModel.created_at.desc())
        .limit(max(1, min(int(limit or 50), 200))))).all()

    ids = [r.id for r in rows]
    triage: dict = {}
    merged: dict = {}
    if ids:
        acts = (await db.execute(
            select(BacklogActivityModel.item_id, BacklogActivityModel.comment,
                   BacklogActivityModel.new_value, BacklogActivityModel.created_at)
            .where(BacklogActivityModel.item_id.in_(ids),
                   BacklogActivityModel.actor == "ai-triage")
            .order_by(BacklogActivityModel.created_at.desc()))).all()
        for a in acts:
            if a.new_value and a.new_value.startswith("dup-of-") and a.item_id not in merged:
                try:
                    merged[a.item_id] = int(a.new_value.rsplit("-", 1)[-1])
                except Exception:
                    pass
            if a.item_id not in triage:   # keep only the latest triage per item
                try:
                    triage[a.item_id] = {"data": json.loads(a.comment),
                                         "at": a.created_at.isoformat() if a.created_at else None}
                except Exception:
                    pass

    items = []
    for r in rows:
        t = triage.get(r.id)
        items.append({
            "item_number": r.item_number, "raw_title": r.title, "raw_description": r.description,
            "status": r.status.value if r.status else None,
            "priority": r.priority.value if r.priority else None,
            "reporter": r.created_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "has_screenshot": bool(r.has_shot),
            "triaged": (t or {}).get("data"), "triaged_at": (t or {}).get("at"),
            "merged_into": merged.get(r.id),
        })
    triaged_n = sum(1 for i in items if i["triaged"])
    undec = sum(1 for i in items if i["triaged"]
                and i["triaged"].get("clean", {}).get("decipherable") is False)
    return {"total": len(items), "triaged": triaged_n, "untriaged": len(items) - triaged_n,
            "undecipherable": undec, "items": items}


@router.post("/feedback/{item_number}/done")
async def mark_feedback_fixed(
    item_number: int,
    payload: dict = Body(default={}),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "👑️ pos-admin"])),
):
    """Manager marks a feedback ticket FIXED → status=done + the reporter gets a 'please
    confirm it's fixed' notification. The reporter then closes their OWN ticket."""
    from src.db.models.backlog_model import (BacklogActivityModel, BacklogActivityType,
                                             BacklogStatus)
    from src.db.models.pos_notification_model import POSNotificationModel
    actor = current_user.get("username") or current_user.get("preferred_username", "manager")
    row = (await db.execute(
        select(BacklogItemModel.id, BacklogItemModel.title, BacklogItemModel.created_by)
        .where(BacklogItemModel.item_number == item_number,
               BacklogItemModel.tags.ilike("%feedback%")))).first()
    if not row:
        raise HTTPException(status_code=404, detail="No such feedback ticket")
    commit = (payload.get("commit") or "").strip()[:80]
    await db.execute(update(BacklogItemModel)
                     .where(BacklogItemModel.id == row.id)
                     .values(status=BacklogStatus.DONE))
    db.add(BacklogActivityModel(
        item_id=row.id, activity_type=BacklogActivityType.STATUS_CHANGE, actor=actor,
        new_value="done",
        comment="🔧 Fixed" + (f" in {commit}" if commit else "") + " — awaiting reporter confirmation."))
    if row.created_by and row.created_by not in ("unknown", "ai-triage"):
        db.add(POSNotificationModel(
            recipient=row.created_by, kind="shipped", item_number=item_number,
            title="✅ Fixed — please take a look",
            body=f"We fixed “{(row.title or 'your report')[:120]}”. Tap to check it and confirm.",
            link="/pos/my-tickets"))
    # Fan-out: also tell anyone whose duplicate was merged into this ticket.
    dups = (await db.execute(
        select(BacklogItemModel.created_by, BacklogItemModel.item_number)
        .join(BacklogActivityModel, BacklogActivityModel.item_id == BacklogItemModel.id)
        .where(BacklogActivityModel.new_value == f"dup-of-{item_number}"))).all()
    for d in dups:
        if d.created_by and d.created_by not in ("unknown", "ai-triage"):
            db.add(POSNotificationModel(
                recipient=d.created_by, kind="shipped", item_number=d.item_number,
                title="✅ Fixed — please take a look",
                body="The issue you flagged was just fixed (we'd linked it with others who hit "
                     "it too). Tap to check it out.",
                link="/pos/my-tickets"))
    await db.commit()
    return {"ok": True}


@router.post("/feedback/{item_number}/reject")
async def reject_feedback(
    item_number: int,
    payload: dict = Body(default={}),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_roles(["👔️ pos-manager", "👑️ pos-admin"])),
):
    """Manager rejects a ticket (can't reproduce / works as intended / not a real ask). The
    reporter is asked to CONFIRM the rejection or DISPUTE it — never a silent close."""
    from src.db.models.backlog_model import BacklogActivityModel, BacklogActivityType
    from src.db.models.pos_notification_model import POSNotificationModel
    actor = current_user.get("username") or current_user.get("preferred_username", "manager")
    reason = (payload.get("reason") or "").strip() or \
        "We looked into it and don't think it needs a change."
    row = (await db.execute(
        select(BacklogItemModel.id, BacklogItemModel.title, BacklogItemModel.created_by)
        .where(BacklogItemModel.item_number == item_number,
               BacklogItemModel.tags.ilike("%feedback%")))).first()
    if not row:
        raise HTTPException(status_code=404, detail="No such feedback ticket")
    db.add(BacklogActivityModel(
        item_id=row.id, activity_type=BacklogActivityType.STATUS_CHANGE, actor=actor,
        new_value="rejected", comment=reason[:1000]))
    if row.created_by and row.created_by not in ("unknown", "ai-triage"):
        db.add(POSNotificationModel(
            recipient=row.created_by, kind="rejected", item_number=item_number,
            title="🤔 About your report — a quick check",
            body=f"We looked at “{(row.title or 'your report')[:120]}” and don't think it needs "
                 "a change. Tap to see why — confirm, or tell us we got it wrong.",
            link="/pos/my-tickets"))
    await db.commit()
    return {"ok": True}


@router.post("/feedback/mine/{item_number}/accept-reject")
async def accept_rejection(
    item_number: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Reporter agrees with the rejection → closes the ticket (no change needed)."""
    from src.db.models.backlog_model import (BacklogActivityModel, BacklogActivityType,
                                             BacklogStatus)
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    row = await _my_feedback_item(db, me, item_number)
    if not row:
        raise HTTPException(status_code=404, detail="Not your ticket")
    await db.execute(update(BacklogItemModel)
                     .where(BacklogItemModel.id == row.id)
                     .values(status=BacklogStatus.ARCHIVED))
    db.add(BacklogActivityModel(
        item_id=row.id, activity_type=BacklogActivityType.STATUS_CHANGE, actor=me,
        new_value="reject-confirmed", comment="👍 Reporter agreed no change was needed."))
    await db.commit()
    return {"ok": True}


@router.post("/feedback/mine/{item_number}/dispute")
async def dispute_rejection(
    item_number: int,
    payload: dict = Body(default={}),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Reporter disagrees with the rejection → back to the team with their reason."""
    from src.db.models.backlog_model import (BacklogActivityModel, BacklogActivityType,
                                             BacklogStatus)
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    note = (payload.get("note") or "").strip()
    row = await _my_feedback_item(db, me, item_number)
    if not row:
        raise HTTPException(status_code=404, detail="Not your ticket")
    await db.execute(update(BacklogItemModel)
                     .where(BacklogItemModel.id == row.id)
                     .values(status=BacklogStatus.IN_PROGRESS))
    db.add(BacklogActivityModel(
        item_id=row.id, activity_type=BacklogActivityType.STATUS_CHANGE, actor=me,
        new_value="disputed",
        comment="↩️ Reporter disagrees with the rejection" + (f": {note[:800]}" if note else ".")))
    await db.commit()
    return {"ok": True}


@router.post("/feedback/mine/{item_number}/cancel")
async def cancel_my_ticket(
    item_number: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Reporter withdraws their own report ('never mind' / not needed any more)."""
    from src.db.models.backlog_model import (BacklogActivityModel, BacklogActivityType,
                                             BacklogStatus)
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    row = await _my_feedback_item(db, me, item_number)
    if not row:
        raise HTTPException(status_code=404, detail="Not your ticket")
    await db.execute(update(BacklogItemModel)
                     .where(BacklogItemModel.id == row.id)
                     .values(status=BacklogStatus.ARCHIVED))
    db.add(BacklogActivityModel(
        item_id=row.id, activity_type=BacklogActivityType.STATUS_CHANGE, actor=me,
        new_value="reporter-cancelled", comment="✕ Reporter withdrew this report."))
    await db.commit()
    return {"ok": True}


@router.get("/notifications")
async def my_notifications(
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The reporter BELL — a user's own in-app notifications + unread count. Any POS user
    sees ONLY their own (recipient = their username)."""
    from src.db.models.pos_notification_model import POSNotificationModel
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    rows = (await db.execute(
        select(POSNotificationModel.id, POSNotificationModel.kind, POSNotificationModel.title,
               POSNotificationModel.body, POSNotificationModel.item_number,
               POSNotificationModel.link, POSNotificationModel.read_at,
               POSNotificationModel.created_at)
        .where(POSNotificationModel.recipient == me)
        .order_by(POSNotificationModel.created_at.desc())
        .limit(max(1, min(int(limit or 20), 50))))).all()
    unread = (await db.execute(
        select(func.count()).select_from(POSNotificationModel)
        .where(POSNotificationModel.recipient == me,
               POSNotificationModel.read_at.is_(None)))).scalar() or 0
    items = [{
        "id": str(r.id), "kind": r.kind, "title": r.title, "body": r.body,
        "item_number": r.item_number, "link": r.link,
        "read": r.read_at is not None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rows]
    return {"unread": int(unread), "items": items}


@router.post("/notifications/read")
async def mark_notifications_read(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Mark ALL of the current user's notifications as read (bell opened)."""
    from src.db.models.pos_notification_model import POSNotificationModel
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    await db.execute(
        update(POSNotificationModel)
        .where(POSNotificationModel.recipient == me, POSNotificationModel.read_at.is_(None))
        .values(read_at=datetime.now(timezone.utc)))
    await db.commit()
    return {"ok": True}


# ===== "My tickets" — the friendly, no-jargon view of a user's OWN feedback (PoC-3) =========
def _friendly_stage(status: str, has_triage: bool) -> dict:
    """Map the internal status → a plain-language journey step (1..4) for a non-techie."""
    s = (status or "pending").lower()
    if s == "archived":
        return {"step": 4, "label": "Closed", "emoji": "✅",
                "blurb": "All sorted — thank you for helping make this better!"}
    if s == "done":
        return {"step": 4, "label": "Fixed!", "emoji": "🎉",
                "blurb": "We fixed it — please take a look and let us know it's good."}
    if s == "in_progress":
        return {"step": 3, "label": "Being fixed", "emoji": "🔧",
                "blurb": "Someone's working on this right now."}
    if s == "blocked":
        return {"step": 3, "label": "On hold", "emoji": "⏳",
                "blurb": "Paused for a moment — we haven't forgotten it."}
    if has_triage:
        return {"step": 2, "label": "We understand it", "emoji": "👀",
                "blurb": "We've read it and we're looking into it."}
    return {"step": 1, "label": "Received", "emoji": "📨",
            "blurb": "Thanks! We've got your message."}


# Plain-language translation of ONE activity-log row → a timeline event (or None to skip).
# The append-only activity chain IS the audit trail; this just renders it as a human story.
_TL_MAP = {
    "done":               ("🔧", "Marked fixed"),
    "closed-confirmed":   ("🎉", "You closed it — fixed"),
    "rejected":           ("🤔", "We took a look — no change needed"),
    "reject-confirmed":   ("👍", "You agreed — closed"),
    "disputed":           ("↩️", "You sent it back"),
    "reporter-cancelled": ("✕", "You withdrew it"),
    "confirmed":          ("✅", "You confirmed our understanding"),
    "reporter-note":      ("✏️", "You added detail"),
    "reopened":           ("↩️", "You sent it back — the fix didn't work"),
}


def _timeline_event(actor, new_value, comment, created_at, *, linked=False):
    nv = new_value or ""
    at = created_at.isoformat() if created_at else None

    def ev(icon, text, detail=""):
        return {"icon": icon, "text": text, "detail": (detail or "")[:200], "at": at}

    if actor == "ai-dedup":
        return None  # internal breadcrumb on the canonical — not the reporter's story
    if actor == "ai-triage":
        if nv.startswith("dup-of-"):
            return ev("🔁", f"Linked to report #{nv.rsplit('-', 1)[-1]}",
                      "Same issue — joined to the earlier report")
        clean_title = ""
        try:
            clean_title = (json.loads(comment).get("clean") or {}).get("title", "")
        except Exception:
            pass
        return ev("👀", "We understood it", clean_title)
    if nv in _TL_MAP:
        if linked and nv == "done":
            return ev("✅", "The linked issue was fixed — you're all set")
        icon, text = _TL_MAP[nv]
        detail = ""
        if nv == "rejected":
            detail = comment or ""
        elif nv == "reporter-note":
            detail = (comment or "").replace("📝 Reporter added: ", "")
        return ev(icon, text, detail)
    return None


def _decode_any_data_url(data_url):
    """data:<mime>;base64,<payload>  →  (bytes, mime).  Handles images AND PDFs."""
    import base64 as _b64
    import re as _re
    m = _re.match(r"data:([^;]+);base64,(.*)", data_url or "", _re.S)
    if not m:
        return None, None
    try:
        return _b64.b64decode(m.group(2)), m.group(1)
    except Exception:
        return None, None


async def _my_feedback_item(db, me, item_number):
    """Fetch ONE feedback item that belongs to `me` (id + status), or None."""
    row = (await db.execute(
        select(BacklogItemModel.id, BacklogItemModel.status)
        .where(BacklogItemModel.item_number == item_number,
               BacklogItemModel.created_by == me,
               BacklogItemModel.tags.ilike("%feedback%")))).first()
    return row


@router.get("/feedback/mine/{item_number}/timeline")
async def my_ticket_timeline(
    item_number: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The full story of ONE of my tickets — report → resolution — in plain language, built
    straight from the append-only activity log (plus the canonical's "fixed" milestone if this
    report was linked to an earlier one, so a linked report visibly resolves). Reporter sees
    only their own; read-only."""
    from src.db.models.backlog_model import BacklogActivityModel
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    row = (await db.execute(
        select(BacklogItemModel.id, BacklogItemModel.item_number, BacklogItemModel.title,
               BacklogItemModel.created_at,
               (BacklogItemModel.screenshot_data.isnot(None)).label("has_shot"),
               BacklogItemModel.attachments)
        .where(BacklogItemModel.item_number == item_number,
               BacklogItemModel.created_by == me,
               BacklogItemModel.tags.ilike("%feedback%")))).first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    # What they attached to the original report — screenshot first (idx 0), then files.
    # Metadata only (names/types); the bytes are served lazily by /attachment/{idx}.
    media = []
    if row.has_shot:
        media.append({"idx": 0, "name": "Screenshot", "is_image": True})
    try:
        base = 1 if row.has_shot else 0
        for i, a in enumerate(json.loads(row.attachments or "[]")):
            media.append({"idx": base + i, "name": a.get("name") or f"file {i + 1}",
                          "is_image": str(a.get("type", "")).startswith("image/")})
    except Exception:
        pass

    events = [{"icon": "📨", "text": "You reported it", "detail": (row.title or "")[:200],
               "at": row.created_at.isoformat() if row.created_at else None, "media": media}]

    acts = (await db.execute(
        select(BacklogActivityModel.actor, BacklogActivityModel.new_value,
               BacklogActivityModel.comment, BacklogActivityModel.created_at)
        .where(BacklogActivityModel.item_id == row.id)
        .order_by(BacklogActivityModel.created_at.asc()))).all()
    linked_to = None
    fixed_at = closed_at = None  # SLA milestones (acts are asc → first match = earliest)
    for a in acts:
        nv = a.new_value or ""
        if a.actor == "ai-triage" and nv.startswith("dup-of-"):
            try:
                linked_to = int(nv.rsplit("-", 1)[-1])
            except Exception:
                pass
        if nv == "done" and fixed_at is None:
            fixed_at = a.created_at
        if nv in ("closed-confirmed", "reject-confirmed") and closed_at is None:
            closed_at = a.created_at
        e = _timeline_event(a.actor, a.new_value, a.comment, a.created_at)
        if e:
            events.append(e)

    # If this report was linked, append the EARLIER report's resolution so it visibly resolves.
    if linked_to:
        canon_id = (await db.execute(
            select(BacklogItemModel.id)
            .where(BacklogItemModel.item_number == linked_to))).scalar_one_or_none()
        if canon_id:
            cacts = (await db.execute(
                select(BacklogActivityModel.actor, BacklogActivityModel.new_value,
                       BacklogActivityModel.comment, BacklogActivityModel.created_at)
                .where(BacklogActivityModel.item_id == canon_id,
                       BacklogActivityModel.new_value == "done")
                .order_by(BacklogActivityModel.created_at.asc()))).all()
            for a in cacts:
                if a.new_value == "done" and fixed_at is None:
                    fixed_at = a.created_at  # linked report heals when the canonical was fixed
                e = _timeline_event(a.actor, a.new_value, a.comment, a.created_at, linked=True)
                if e:
                    events.append(e)

    events.sort(key=lambda x: x["at"] or "")
    from src.services.ticket_timing import ticket_timing
    timing = ticket_timing(row.created_at, fixed_at, closed_at,
                           now=datetime.now(timezone.utc))
    return {"item_number": row.item_number, "events": events, "timing": timing}


@router.get("/feedback/mine/{item_number}/attachment/{idx}")
async def my_ticket_attachment(
    item_number: int, idx: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Serve ONE attachment from my report as real bytes (so <img> shows it and PDFs open).
    Order matches the timeline: screenshot is idx 0, then files. Reporter-owned only."""
    from fastapi import Response
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    row = (await db.execute(
        select(BacklogItemModel.screenshot_data, BacklogItemModel.attachments)
        .where(BacklogItemModel.item_number == item_number,
               BacklogItemModel.created_by == me,
               BacklogItemModel.tags.ilike("%feedback%")))).first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    blobs = []
    if row.screenshot_data:
        blobs.append(row.screenshot_data)
    try:
        blobs.extend(a["data"] for a in json.loads(row.attachments or "[]") if a.get("data"))
    except Exception:
        pass
    if idx < 0 or idx >= len(blobs):
        raise HTTPException(status_code=404, detail="Attachment not found")
    data, mime = _decode_any_data_url(blobs[idx])
    if data is None:
        raise HTTPException(status_code=415, detail="Unreadable attachment")
    return Response(content=data, media_type=mime or "application/octet-stream",
                    headers={"Content-Disposition": "inline", "Cache-Control": "private, max-age=300"})


@router.get("/feedback/mine/{item_number}/resolution")
async def my_ticket_resolution(
    item_number: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """A plain-language RESOLUTION for a resolved ticket — what was reported, what we decided,
    what we did (commit), and the outcome — in 3-4 sentences anyone can skim. Generated once by
    the AI from the activity log, then cached as an `ai-resolution` activity. {resolved:false}
    until the ticket actually reaches an end (fixed, no-change-needed, or withdrawn)."""
    import re as _re
    from src.db.models.backlog_model import BacklogActivityModel, BacklogActivityType
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    row = (await db.execute(
        select(BacklogItemModel.id, BacklogItemModel.title, BacklogItemModel.status,
               BacklogItemModel.created_by, BacklogItemModel.created_at)
        .where(BacklogItemModel.item_number == item_number,
               BacklogItemModel.created_by == me,
               BacklogItemModel.tags.ilike("%feedback%")))).first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    acts = (await db.execute(
        select(BacklogActivityModel.actor, BacklogActivityModel.new_value,
               BacklogActivityModel.comment, BacklogActivityModel.created_at)
        .where(BacklogActivityModel.item_id == row.id)
        .order_by(BacklogActivityModel.created_at.asc()))).all()

    # SLA on screen: how fast did the loop heal it? (acts asc → first match = earliest)
    from src.services.ticket_timing import ticket_timing
    fixed_at = closed_at = None
    for a in acts:
        if a.new_value == "done" and fixed_at is None:
            fixed_at = a.created_at
        if a.new_value in ("closed-confirmed", "reject-confirmed") and closed_at is None:
            closed_at = a.created_at
    timing = ticket_timing(row.created_at, fixed_at, closed_at,
                           now=datetime.now(timezone.utc))

    # Only a TRUE ending earns a resolution — fixed-but-awaiting-confirm is not closed yet, and
    # summarising it early makes the AI over-claim a close that hasn't happened.
    terminal = {"closed-confirmed", "reject-confirmed", "reporter-cancelled"}
    is_resolved = (row.status or "").lower() == "archived" \
        or any(a.new_value in terminal for a in acts)
    if not is_resolved:
        return {"resolved": False, "timing": timing}
    for a in acts:                                   # already written? serve the cached one
        if a.actor == "ai-resolution" and a.comment:
            return {"resolved": True, "text": a.comment, "cached": True, "timing": timing}

    # Build the ordered story beats for the brain.
    lines = ['Reported by %s: "%s"' % (row.created_by or "a teammate", (row.title or "").strip())]
    for a in acts:
        nv = a.new_value or ""
        if a.actor == "ai-triage" and nv.startswith("dup-of-"):
            lines.append("Linked to earlier report #%s (same issue)." % nv.rsplit("-", 1)[-1])
        elif a.actor == "ai-triage":
            try:
                ct = (json.loads(a.comment).get("clean") or {}).get("title")
                if ct:
                    lines.append('We understood it as: "%s"' % ct)
            except Exception:
                pass
        elif nv == "confirmed":
            lines.append("The reporter confirmed we understood it correctly.")
        elif nv == "reporter-note":
            lines.append("The reporter added more detail.")
        elif nv == "done":
            m = _re.search(r"Fixed in ([0-9a-f]{6,40})", a.comment or "")
            lines.append("Fixed in commit %s." % m.group(1) if m else "Marked fixed.")
        elif nv == "rejected":
            lines.append(("We decided no change was needed: " + (a.comment or "")).strip())
        elif nv == "closed-confirmed":
            lines.append("The reporter checked it and closed the ticket — confirmed good.")
        elif nv == "reject-confirmed":
            lines.append("The reporter agreed no change was needed and closed it.")
        elif nv == "reporter-cancelled":
            lines.append("The reporter withdrew the report.")
        elif nv == "reopened":
            lines.append("An earlier fix didn't work, so it went back to the team.")

    from src.services.feedback_triage import summarize_resolution
    res = await summarize_resolution(lines)
    db.add(BacklogActivityModel(
        item_id=row.id, activity_type=BacklogActivityType.COMMENT, actor="ai-resolution",
        new_value="resolution", comment=(res["text"] or "")[:4000]))
    await db.commit()
    return {"resolved": True, "text": res["text"], "ai": res["ai"], "cached": False, "timing": timing}


@router.get("/feedback/mine")
async def my_tickets(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """A user's OWN feedback, in plain language: what they said, how we understood it, what
    stage it's at, and whether they've confirmed. No severities, no jargon."""
    from src.db.models.backlog_model import BacklogActivityModel
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    rows = (await db.execute(
        select(BacklogItemModel.id, BacklogItemModel.item_number, BacklogItemModel.title,
               BacklogItemModel.description, BacklogItemModel.status, BacklogItemModel.created_at)
        .where(BacklogItemModel.created_by == me, BacklogItemModel.tags.ilike("%feedback%"))
        .order_by(BacklogItemModel.created_at.desc()).limit(50))).all()
    ids = [r.id for r in rows]
    triage, confirmed, closed, merged = {}, set(), set(), {}
    cancelled = set()                      # reporter withdrew it
    reject_state, reject_reason = {}, {}   # item_id -> pending|confirmed|disputed
    if ids:
        acts = (await db.execute(
            select(BacklogActivityModel.item_id, BacklogActivityModel.actor,
                   BacklogActivityModel.new_value, BacklogActivityModel.comment,
                   BacklogActivityModel.created_at)
            .where(BacklogActivityModel.item_id.in_(ids))
            .order_by(BacklogActivityModel.created_at.desc()))).all()
        for a in acts:
            # Reject lifecycle: the NEWEST reject-related activity per item wins.
            if a.item_id not in reject_state and a.new_value in (
                    "rejected", "reject-confirmed", "disputed"):
                if a.new_value == "rejected":
                    reject_state[a.item_id] = "pending"; reject_reason[a.item_id] = a.comment or ""
                elif a.new_value == "reject-confirmed":
                    reject_state[a.item_id] = "confirmed"
                else:
                    reject_state[a.item_id] = "disputed"
            if a.actor == "ai-triage":
                if a.new_value and a.new_value.startswith("dup-of-") and a.item_id not in merged:
                    try:
                        merged[a.item_id] = int(a.new_value.rsplit("-", 1)[-1])
                    except Exception:
                        pass
                if a.item_id not in triage:
                    try:
                        triage[a.item_id] = json.loads(a.comment).get("clean", {})
                    except Exception:
                        triage[a.item_id] = {}
            elif a.actor == me and a.new_value in ("confirmed", "reporter-note"):
                confirmed.add(a.item_id)   # adding detail IS a reply → stop re-asking
            elif a.actor == me and a.new_value == "closed-confirmed":
                closed.add(a.item_id)
            elif a.actor == me and a.new_value == "reporter-cancelled":
                cancelled.add(a.item_id)
    items = []
    for r in rows:
        cl = triage.get(r.id)
        # A merged duplicate is its own friendly state — never "Closed/Done".
        if r.id in merged:
            items.append({
                "item_number": r.item_number, "you_said": r.title,
                "understood": (cl or {}).get("title") if cl else None,
                "stage": {"step": 2, "label": "Known issue", "emoji": "🔁",
                          "blurb": "Someone reported this first, so it's already on our list. "
                                   "Nothing more you need to do — we'll let you know right here "
                                   "the moment it's fixed."},
                "needs_confirm": False, "confirmed": False, "needs_confirm_fix": False,
                "closed": False, "merged_into": merged[r.id],
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
            continue
        # A rejection awaiting the reporter's call — confirm it, or dispute it.
        if reject_state.get(r.id) == "pending":
            items.append({
                "item_number": r.item_number, "you_said": r.title,
                "understood": (cl or {}).get("title") if cl else None,
                "kind": None, "severity": None,
                "stage": {"step": 2, "label": "Reviewed", "emoji": "🤔",
                          "blurb": "We took a look and don't think this one needs a change."},
                "needs_confirm": False, "confirmed": False, "needs_confirm_fix": False,
                "rejected_pending": True, "reject_reason": reject_reason.get(r.id),
                "closed": False, "closed_kind": None, "merged_into": None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
            continue
        status_val = r.status.value if r.status else "pending"
        is_done = status_val == "done"               # fixed, awaiting reporter's OK
        reject_closed = reject_state.get(r.id) == "confirmed"
        is_cancelled = r.id in cancelled
        is_closed = status_val == "archived" or r.id in closed or is_cancelled
        st = _friendly_stage(
            "archived" if (r.id in closed or reject_closed or is_cancelled) else status_val,
            cl is not None)
        items.append({
            "item_number": r.item_number,
            "you_said": r.title,
            "understood": (cl or {}).get("title") if cl else None,
            "kind": (cl or {}).get("type") if cl else None,
            "severity": (cl or {}).get("severity") if cl else None,
            "stage": st,
            "needs_confirm": cl is not None and r.id not in confirmed and not is_done and not is_closed,
            "confirmed": r.id in confirmed,
            "needs_confirm_fix": is_done and not is_closed,   # 🎉 "we fixed it, confirm?"
            "rejected_pending": False, "reject_reason": None,
            "closed": is_closed,
            "closed_kind": ("cancelled" if is_cancelled
                            else "rejected" if reject_closed else "fixed"),
            "merged_into": None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    done_n = sum(1 for i in items if i["closed"])
    open_n = len(items) - done_n
    return {"open": open_n, "done": done_n, "items": items}


@router.post("/feedback/mine/{item_number}/confirm")
async def confirm_my_ticket(
    item_number: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The confirm-back loop: 'yes, that's what I meant'. Recorded as the reporter's own activity."""
    from src.db.models.backlog_model import BacklogActivityModel, BacklogActivityType
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    row = await _my_feedback_item(db, me, item_number)
    if not row:
        raise HTTPException(status_code=404, detail="Not your ticket")
    db.add(BacklogActivityModel(
        item_id=row.id, activity_type=BacklogActivityType.COMMENT, actor=me,
        new_value="confirmed", comment="✅ Reporter confirmed the AI's understanding is correct."))
    await db.commit()
    return {"ok": True}


@router.post("/feedback/mine/{item_number}/note")
async def add_note_to_my_ticket(
    item_number: int,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """'Not quite — here's more.' The reporter adds a clarifying note to their own ticket."""
    from src.db.models.backlog_model import BacklogActivityModel, BacklogActivityType
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    note = (payload.get("note") or "").strip()
    if not note:
        raise HTTPException(status_code=400, detail="Empty note")
    row = await _my_feedback_item(db, me, item_number)
    if not row:
        raise HTTPException(status_code=404, detail="Not your ticket")
    db.add(BacklogActivityModel(
        item_id=row.id, activity_type=BacklogActivityType.COMMENT, actor=me,
        new_value="reporter-note", comment="📝 Reporter added: " + note[:1000]))
    await db.commit()
    return {"ok": True}


@router.post("/feedback/mine/{item_number}/close")
async def close_my_ticket(
    item_number: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The reporter confirms the fix is good and CLOSES their own ticket → status=archived."""
    from src.db.models.backlog_model import (BacklogActivityModel, BacklogActivityType,
                                             BacklogStatus)
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    row = await _my_feedback_item(db, me, item_number)
    if not row:
        raise HTTPException(status_code=404, detail="Not your ticket")
    if (row.status.value if row.status else "") != "done":
        raise HTTPException(status_code=409, detail="Ticket isn't marked fixed yet")
    await db.execute(update(BacklogItemModel)
                     .where(BacklogItemModel.id == row.id)
                     .values(status=BacklogStatus.ARCHIVED))
    db.add(BacklogActivityModel(
        item_id=row.id, activity_type=BacklogActivityType.STATUS_CHANGE, actor=me,
        new_value="closed-confirmed",
        comment="🎉 Reporter confirmed the fix is good and closed the ticket."))
    await db.commit()
    return {"ok": True}


@router.post("/feedback/mine/{item_number}/reopen")
async def reopen_my_ticket(
    item_number: int,
    payload: dict = Body(default={}),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The reporter says 'still not right' → back to In progress, with their note for the team."""
    from src.db.models.backlog_model import (BacklogActivityModel, BacklogActivityType,
                                             BacklogStatus)
    me = current_user.get("username") or current_user.get("preferred_username", "unknown")
    note = (payload.get("note") or "").strip()
    row = await _my_feedback_item(db, me, item_number)
    if not row:
        raise HTTPException(status_code=404, detail="Not your ticket")
    await db.execute(update(BacklogItemModel)
                     .where(BacklogItemModel.id == row.id)
                     .values(status=BacklogStatus.IN_PROGRESS))
    db.add(BacklogActivityModel(
        item_id=row.id, activity_type=BacklogActivityType.STATUS_CHANGE, actor=me,
        new_value="reopened",
        comment="↩️ Reporter says it's not fixed yet" + (f": {note[:800]}" if note else ".")))
    await db.commit()
    return {"ok": True}


# ================================================================
# CASH SHIFT -- per-cashier drawer accountability (the lockbox loop)
# ================================================================
# Open with a counted float -> ring sales (tied to cashier_id) -> record any
# non-sale cash (paid-in/out) -> close by counting the drawer. The system shows
# expected vs counted, flags variance beyond the tolerance, and the open/close
# timestamps double as shift hours. Each cashier owns their own drawer.

async def _resolve_cashier_uid(db: AsyncSession, current_user: dict) -> str:
    """The cashier's STABLE users.id (as a string) — the single identity used for
    transactions.cashier_id, cash-shift ownership and every per-cashier report.

    Why this exists: transactions.cashier_id is a hard FK to users.id, and SEEDED demo
    cashiers carry a fixed PK (e.g. Pam = 0000…0001) while storing their Keycloak sub in
    keycloak_id. The raw sub (_uid) therefore does NOT equal users.id for them, so keying
    some writes on the sub and others on users.id silently de-syncs the drawer ("My Day"
    shows the sale, the drawer doesn't count it). Resolving by id THEN keycloak_id and
    returning users.id keeps EVERY cashier-scoped query pointing at the same value, on every
    env, with no data migration. Self-provisions a row for a never-seeded login (id == sub).
    """
    sub = current_user.get("sub")
    try:
        cid = UUID(str(sub)) if sub else None
    except (ValueError, TypeError):
        cid = None
    if cid is None:                      # no usable sub — never key on None
        return current_user.get("preferred_username", "unknown")
    user = await db.get(UserModel, cid)
    if user is None:
        user = (await db.execute(
            select(UserModel).where(UserModel.keycloak_id == cid)
        )).scalar_one_or_none()
    if user is not None:
        return str(user.id)
    # Never provisioned on THIS env — create with id == keycloak_id == sub (the convention).
    uname = (current_user.get("preferred_username") or str(cid)[:8]).strip().lower()
    clash = (await db.execute(
        select(UserModel).where(func.lower(UserModel.username) == uname)
    )).scalar_one_or_none()
    if clash:                            # username taken by a different id — vary the name
        uname = f"{uname}-{str(cid)[:8]}"
    db.add(UserModel(
        id=cid, keycloak_id=cid, username=uname, email=f"{uname}@pos.local",
        first_name=current_user.get("given_name"), last_name=current_user.get("family_name"),
    ))
    await db.flush()
    return str(cid)


def _uname(current_user: dict) -> str:
    return current_user.get("preferred_username", current_user.get("username", "Unknown"))


async def _max_discount_pct(db: AsyncSession, current_user: dict) -> Decimal:
    """Per-role manual-discount ceiling, read LIVE from the store's settings so a shop tunes
    each role from the admin-only Settings screen (the value the till actually enforces).
    Admin/developer is always unlimited (100%). Falls back to cashier 10% / manager 25% when
    the store or a value isn't set, so a missing row never blocks nor over-opens a sale."""
    roles = (current_user.get("user_roles")
             or current_user.get("realm_access", {}).get("roles", []) or [])
    if any(("admin" in r or "developer" in r) for r in roles):
        return Decimal("100")
    store = None
    try:
        store = await get_active_store_settings(db)
    except Exception:
        logger.warning("discount cap: store-settings load failed; using role defaults", exc_info=True)
    if any("manager" in r for r in roles):
        val = store.manager_max_discount if store is not None else None
        return val if val is not None else Decimal("25")
    val = store.cashier_max_discount if store is not None else None
    return val if val is not None else Decimal("10")


@router.get("/discount-cap")
async def get_my_discount_cap(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The manual-discount ceiling for the CURRENT user, LIVE from the store settings — the exact
    value the checkout guard enforces (_max_discount_pct). The till reads THIS instead of a
    hardcoded 10/25, so the cap + label can never drift from what the server allows (the
    phantom-setting bug: an admin raised the cap in Settings but the till stayed stuck at 10)."""
    cap = await _max_discount_pct(db, current_user)
    return {"max_discount_pct": float(cap)}


async def _open_shift_for(db: AsyncSession, user_id: str) -> Optional[CashShiftModel]:
    return (await db.execute(select(CashShiftModel).where(
        CashShiftModel.user_id == user_id,
        CashShiftModel.status == CashShiftStatus.OPEN,
    ))).scalar_one_or_none()


async def _tenant_currency(db: AsyncSession) -> str:
    """The tenant's cash currency for drawer counting (CH fallback on any blip).

    PHASE 1 (Go-Italian): the drawer count must validate face values against the
    tenant's OWN currency set (a EUR 500 note / 1c coin is real money). Never raises —
    degrades to CHF exactly like /config, so a Swiss till is byte-identical.
    """
    try:
        store = await get_active_store_settings(db)
        return resolve_regime(store).get("currency", "CHF")
    except Exception:
        logger.warning("shift: currency source failed; CHF fallback", exc_info=True)
        return "CHF"


async def _shift_sales(db: AsyncSession, user_id: str, start: datetime, end: datetime) -> dict:
    """Sum THIS cashier's takings in the shift window. Only CASH touches the drawer;
    card/twint/debit are reported but never counted. Refunds reduce the expected cash."""
    rows = (await db.execute(select(TransactionModel).where(
        TransactionModel.cashier_id == user_id,
        TransactionModel.completed_at >= start,
        TransactionModel.completed_at <= end,
    ))).scalars().all()
    cash_sales = card_sales = cash_refunds = Decimal("0")
    count = 0
    for t in rows:
        total = Decimal(str(t.total or 0))
        if t.status == TransactionStatus.COMPLETED:
            count += 1
            if t.payment_method == PaymentMethod.CASH:
                cash_sales += total
            else:
                card_sales += total
        elif t.status == TransactionStatus.REFUNDED and t.payment_method == PaymentMethod.CASH:
            cash_refunds += total
    return {"cash_sales": money(cash_sales), "card_sales": money(card_sales),
            "cash_refunds": money(cash_refunds), "count": count}


class OpenShiftReq(BaseModel):
    opening_float: Optional[str] = None     # explicit total, OR
    opening_denoms: Optional[dict] = None   # a {face: count} grid (preferred)
    register_id: Optional[str] = None


class PaidReq(BaseModel):
    kind: str           # paid_in | paid_out
    amount: str
    reason: str = ""


class CloseShiftReq(BaseModel):
    counted_cash: Optional[str] = None      # explicit total, OR
    closing_denoms: Optional[dict] = None   # a {face: count} grid
    note: str = ""


@router.post("/shift/open")
async def open_cash_shift(
    req: OpenShiftReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Start your drawer: count the float in. One open shift per cashier."""
    user_id, username = await _resolve_cashier_uid(db, current_user), _uname(current_user)
    if await _open_shift_for(db, user_id):
        raise HTTPException(status_code=400,
            detail="You already have an open cash shift. Close it first.")
    currency = await _tenant_currency(db)
    opening = denoms_total(req.opening_denoms, currency) if req.opening_denoms else money(req.opening_float or 0)
    shift = CashShiftModel(
        user_id=user_id, username=username, store_number=1,
        register_id=req.register_id, opening_float=opening,
        opening_denoms=json.dumps(req.opening_denoms) if req.opening_denoms else None)
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    logger.info(f"Cash shift OPEN: {username} float={opening}")
    return {"ok": True, "shift_id": str(shift.id), "opening_float": str(opening),
            "opened_at": shift.opened_at.isoformat()}


@router.post("/shift/paid")
async def shift_paid_in_out(
    req: PaidReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Record non-sale cash moving in/out of the drawer (with a reason) so the
    drawer can still balance at close."""
    user_id, username = await _resolve_cashier_uid(db, current_user), _uname(current_user)
    shift = await _open_shift_for(db, user_id)
    if not shift:
        raise HTTPException(status_code=404, detail="No open cash shift to adjust.")
    kind = (req.kind or "").lower()
    if kind not in ("paid_in", "paid_out"):
        raise HTTPException(status_code=400, detail="kind must be paid_in or paid_out")
    amount = money(req.amount or 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero.")
    reason = (req.reason or "").strip()
    if len(reason) < 2:
        raise HTTPException(status_code=400, detail="Give a short reason for the cash movement.")
    mv = CashMovementModel(
        shift_id=shift.id,
        kind=CashMovementKind.PAID_IN if kind == "paid_in" else CashMovementKind.PAID_OUT,
        amount=amount, reason=reason[:300], actor=username)
    db.add(mv)
    if kind == "paid_in":
        shift.paid_in_total = money(Decimal(str(shift.paid_in_total or 0)) + amount)
    else:
        shift.paid_out_total = money(Decimal(str(shift.paid_out_total or 0)) + amount)
    await db.commit()
    logger.info(f"Cash {kind}: {username} {amount} ({reason})")
    return {"ok": True, "paid_in_total": str(shift.paid_in_total),
            "paid_out_total": str(shift.paid_out_total)}


@router.get("/shift/current")
async def current_cash_shift(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The caller's open drawer with the live expected-cash-so-far (or open:false)."""
    user_id = await _resolve_cashier_uid(db, current_user)
    shift = await _open_shift_for(db, user_id)
    if not shift:
        return {"open": False}
    now = datetime.now(timezone.utc)
    s = await _shift_sales(db, user_id, shift.opened_at, now)
    exp = expected_cash(shift.opening_float, s["cash_sales"],
                        shift.paid_in_total, shift.paid_out_total, s["cash_refunds"])
    return {
        "open": True, "shift_id": str(shift.id),
        "opened_at": shift.opened_at.isoformat(),
        "opening_float": str(money(shift.opening_float)),
        "cash_sales": str(s["cash_sales"]), "card_sales": str(s["card_sales"]),
        "cash_refunds": str(s["cash_refunds"]),
        "paid_in_total": str(money(shift.paid_in_total)),
        "paid_out_total": str(money(shift.paid_out_total)),
        "expected_cash": str(exp), "transaction_count": s["count"],
        "tolerance": str(money(shift.tolerance)),
    }


@router.post("/shift/close")
async def close_cash_shift(
    req: CloseShiftReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """Count the drawer out. Computes expected vs counted; a variance beyond the
    tolerance needs a note. Open->close timestamps are the shift hours."""
    user_id, username = await _resolve_cashier_uid(db, current_user), _uname(current_user)
    shift = await _open_shift_for(db, user_id)
    if not shift:
        raise HTTPException(status_code=404, detail="No open cash shift to close.")
    now = datetime.now(timezone.utc)
    s = await _shift_sales(db, user_id, shift.opened_at, now)
    currency = await _tenant_currency(db)
    counted = denoms_total(req.closing_denoms, currency) if req.closing_denoms else money(req.counted_cash or 0)
    exp = expected_cash(shift.opening_float, s["cash_sales"],
                        shift.paid_in_total, shift.paid_out_total, s["cash_refunds"])
    res = close_result(exp, counted, Decimal(str(shift.tolerance)))
    note = (req.note or "").strip()
    if not res["within_tolerance"] and not note:
        raise HTTPException(status_code=400,
            detail=f"Off by {currency} {res['variance']}. Add a note to close the shift.")

    shift.cash_sales = s["cash_sales"]; shift.card_sales = s["card_sales"]
    shift.cash_refunds = s["cash_refunds"]; shift.transaction_count = s["count"]
    shift.counted_cash = counted
    shift.closing_denoms = json.dumps(req.closing_denoms) if req.closing_denoms else None
    shift.expected_cash = res["expected"]; shift.variance = res["variance"]
    shift.within_tolerance = res["within_tolerance"]
    shift.variance_note = note or None
    shift.status = CashShiftStatus.CLOSED; shift.closed_at = now
    await db.commit()

    hours = (now - shift.opened_at).total_seconds() / 3600.0
    logger.info(f"Cash shift CLOSE: {username} expected={res['expected']} counted={counted} "
                f"variance={res['variance']} within={res['within_tolerance']}")
    return _shift_report(shift, hours)


def _shift_report(shift: CashShiftModel, hours: float | None = None) -> dict:
    """The one-page per-cashier shift report payload (used by close + /shift/last)."""
    if hours is None and shift.closed_at:
        hours = (shift.closed_at - shift.opened_at).total_seconds() / 3600.0
    return {
        "ok": True, "shift_id": str(shift.id),
        "username": shift.username,
        "opening_float": str(money(shift.opening_float)),
        "cash_sales": str(money(shift.cash_sales or 0)),
        "card_sales": str(money(shift.card_sales or 0)),
        "cash_refunds": str(money(shift.cash_refunds or 0)),
        "paid_in_total": str(money(shift.paid_in_total)),
        "paid_out_total": str(money(shift.paid_out_total)),
        "expected_cash": str(money(shift.expected_cash or 0)),
        "counted_cash": str(money(shift.counted_cash or 0)),
        "variance": str(money(shift.variance or 0)),
        "within_tolerance": bool(shift.within_tolerance),
        "short": (Decimal(str(shift.variance or 0)) < 0),
        "tolerance": str(money(shift.tolerance)),
        "variance_note": shift.variance_note,
        "transaction_count": shift.transaction_count,
        "opened_at": shift.opened_at.isoformat(),
        "closed_at": shift.closed_at.isoformat() if shift.closed_at else None,
        "hours": round(hours, 2) if hours is not None else None,
    }


@router.get("/shift/last")
async def last_cash_shift(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The caller's most recent CLOSED shift -- so the report screen survives a reload."""
    shift = (await db.execute(select(CashShiftModel).where(
        CashShiftModel.user_id == await _resolve_cashier_uid(db, current_user),
        CashShiftModel.status == CashShiftStatus.CLOSED,
    ).order_by(CashShiftModel.closed_at.desc()).limit(1))).scalar_one_or_none()
    if not shift:
        return {"ok": False}
    return _shift_report(shift)


@router.get("/shift/{shift_id}/transactions")
async def shift_transactions(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(require_any_pos_role()),
):
    """The itemized daily log for one shift -- every transaction the cashier rang in
    the shift window, with its line items. This is what Pam hands Felix: 'I sold
    exactly these N transactions, here is every item.' Owner sees their own; a
    manager/admin can review anyone's."""
    shift = (await db.execute(select(CashShiftModel).where(
        CashShiftModel.id == shift_id))).scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    roles = (current_user.get("user_roles")
             or current_user.get("realm_access", {}).get("roles", []) or [])
    is_mgr = any(("manager" in r or "admin" in r or "developer" in r) for r in roles)
    if shift.user_id != await _resolve_cashier_uid(db, current_user) and not is_mgr:
        raise HTTPException(status_code=403, detail="Not your shift.")

    end = shift.closed_at or datetime.now(timezone.utc)
    txs = (await db.execute(select(TransactionModel).where(
        TransactionModel.cashier_id == shift.user_id,
        TransactionModel.completed_at >= shift.opened_at,
        TransactionModel.completed_at <= end,
        TransactionModel.status.in_([TransactionStatus.COMPLETED, TransactionStatus.REFUNDED]),
    ).order_by(TransactionModel.completed_at.asc()))).scalars().all()

    tx_ids = [t.id for t in txs]
    items_by_tx: dict = {}
    if tx_ids:
        lis = (await db.execute(select(LineItemModel).where(
            LineItemModel.transaction_id.in_(tx_ids)))).scalars().all()
        pids = {it.product_id for it in lis if it.product_id is not None}
        names: dict = {}
        if pids:
            names = {p.id: p.name for p in (await db.execute(
                select(ProductModel).where(ProductModel.id.in_(pids)))).scalars().all()}
        for it in lis:
            items_by_tx.setdefault(it.transaction_id, []).append({
                "name": names.get(it.product_id) or (it.notes if it.product_id is None else "Item"),
                "quantity": it.quantity,
                "unit_price": str(money(it.unit_price)),
                "line_total": str(money(it.line_total)),
                "is_giveaway": bool(it.is_giveaway),
            })

    out = []
    item_count = 0
    for t in txs:
        items = items_by_tx.get(t.id, [])
        item_count += sum(i["quantity"] for i in items if not i["is_giveaway"])
        out.append({
            "number": t.transaction_number,
            "time": t.completed_at.isoformat() if t.completed_at else None,
            "payment_method": t.payment_method.value if t.payment_method else None,
            "status": t.status.value,
            "total": str(money(t.total)),
            "items": items,
        })
    return {"shift_id": str(shift.id), "username": shift.username,
            "transaction_count": len(out), "item_count": item_count, "transactions": out}


# ================================================================
# HTML WEB UI ROUTES (Sprint 4 - Pam's Interface)
# ================================================================

@html_router.get("/pos/sw.js", include_in_schema=False)
async def pos_service_worker():
    """Serve the Banco POS service worker from /pos so its scope covers every /pos page.
    The `Service-Worker-Allowed: /pos` header lets a SW served at /pos/sw.js claim the
    broader /pos scope (including the /pos login). PWA Phase 0."""
    from fastapi.responses import FileResponse
    sw_path = Path(__file__).parent.parent / "static" / "pos" / "sw.js"
    return FileResponse(
        sw_path,
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/pos", "Cache-Control": "no-cache"},
    )


@html_router.get("/pos", response_class=HTMLResponse, name="pos_login")
async def pos_login(request: Request):
    """
    POS Login Page - Entry point for POS system

    Uses Keycloak OAuth2 Authorization Code Flow:
    1. Redirects to Keycloak for authentication
    2. User enters credentials (pam/helix_pass, felix/helix_pass, etc.)
    3. Keycloak redirects back with authorization code
    4. Frontend exchanges code for JWT token
    5. Token stored in sessionStorage
    6. Redirects to dashboard

    No authentication required (this is the login page)
    """
    return templates.TemplateResponse("pos/login.html", {
        "request": request,
        "environment": getattr(get_settings(), "HX_ENVIRONMENT", "") or "",
    })


@html_router.get("/pos/callback")
async def pos_oauth_callback(request: Request, code: str = None, error: str = None):
    """
    OAuth2 Callback - Server-side token exchange (avoids CORS issues)

    Flow:
    1. Keycloak redirects here with ?code=...
    2. Server exchanges code for token (no CORS - server-to-server)
    3. Redirects to dashboard with token in URL fragment
    4. Frontend picks up token and stores it

    This solves the CORS issue where browser can't POST to Keycloak directly.
    """
    import httpx
    from fastapi.responses import RedirectResponse

    if error:
        logger.error(f"OAuth callback error: {error}")
        return RedirectResponse(url="/pos?error=" + error)

    if not code:
        logger.warning("OAuth callback without code")
        return RedirectResponse(url="/pos?error=no_code")

    # Keycloak config
    # IMPORTANT: Use internal Docker URL for server-to-server calls
    keycloak_internal_url = "http://keycloak:8080"
    realm = get_settings().POS_REALM   # env-driven — per-env realm split (was hardcoded -dev)
    client_id = "helix_pos_web"

    # Build redirect_uri - MUST match EXACTLY what browser sent to Keycloak
    # request.base_url gives internal URL, but browser used external https URL
    # So we need to reconstruct it from the request headers

    # Get the original host from X-Forwarded headers (set by Traefik)
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "helix.local")

    # Build the exact redirect_uri that the browser sent to Keycloak
    redirect_uri = f"{forwarded_proto}://{forwarded_host}/pos/callback"

    logger.info(f"Token exchange redirect_uri: {redirect_uri}")

    # Use internal URL for the actual HTTP call (no DNS issues inside Docker)
    token_endpoint = f"{keycloak_internal_url}/realms/{realm}/protocol/openid-connect/token"

    try:
        # Server-to-server token exchange (no CORS issues)
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "code": code,
                    "redirect_uri": redirect_uri
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return RedirectResponse(url="/pos?error=token_exchange_failed")

            tokens = response.json()
            access_token = tokens.get("access_token")

            if not access_token:
                logger.error("No access_token in response")
                return RedirectResponse(url="/pos?error=no_token")

            # Redirect to dashboard with the tokens in the URL fragment (never sent to
            # the server). Include the refresh_token + expires_in so the till can refresh
            # silently and NEVER hard-logout the cashier mid-sale.
            refresh_token = tokens.get("refresh_token", "")
            expires_in = tokens.get("expires_in", 300)
            logger.info("OAuth callback successful, redirecting to dashboard")
            frag = f"#token={access_token}&refresh={refresh_token}&expires_in={expires_in}"
            return RedirectResponse(url=f"/pos/dashboard{frag}")

    except Exception as e:
        logger.error(f"Token exchange exception: {e}")
        return RedirectResponse(url="/pos?error=token_exchange_error")


@html_router.post("/pos/refresh")
async def pos_token_refresh(request: Request):
    """Silent token refresh -- server-to-server (no CORS, mirrors /pos/callback).

    The till POSTs its refresh_token here when the access token is near/at expiry.
    We exchange it with Keycloak for a fresh access (+ rotated refresh) token so the
    cashier is NEVER hard-logged-out mid-sale. No auth dependency: the access token
    is expired by definition -- the refresh_token IS the credential."""
    import httpx
    from fastapi.responses import JSONResponse

    body = await request.json()
    refresh_token = body.get("refresh_token")
    if not refresh_token:
        return JSONResponse(status_code=400, content={"detail": "missing refresh_token"})

    keycloak_internal_url = "http://keycloak:8080"
    realm = get_settings().POS_REALM   # env-driven — per-env realm split (was hardcoded -dev)
    client_id = "helix_pos_web"
    token_endpoint = f"{keycloak_internal_url}/realms/{realm}/protocol/openid-connect/token"

    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if response.status_code != 200:
            logger.info(f"Token refresh rejected: {response.status_code}")
            return JSONResponse(status_code=401, content={"detail": "refresh_failed"})
        tokens = response.json()
        return JSONResponse(content={
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token", refresh_token),
            "expires_in": tokens.get("expires_in", 300),
        })
    except Exception as e:
        logger.error(f"Token refresh exception: {e}")
        return JSONResponse(status_code=500, content={"detail": "refresh_error"})


@html_router.get("/pos/hypercare", response_class=HTMLResponse, name="pos_hypercare")
async def pos_hypercare(request: Request):
    """The Hypercare Cockpit — Angel's command center for AI-triaged feedback (the API
    behind it, /feedback/queue + /feedback/triage, is manager/admin gated)."""
    return templates.TemplateResponse("pos/hypercare.html", {"request": request})


@html_router.get("/pos/my-tickets", response_class=HTMLResponse, name="pos_my_tickets")
async def pos_my_tickets(request: Request):
    """The friendly, no-jargon view of a user's OWN feedback — where the bell sends them.
    Any logged-in POS user; the API (/feedback/mine) returns only their own."""
    return templates.TemplateResponse("pos/my_tickets.html", {"request": request})


@html_router.get("/pos/dashboard", response_class=HTMLResponse, name="pos_dashboard")
async def pos_dashboard(request: Request):
    """
    POS Dashboard - Role-based landing page

    Shows different actions based on user's POS roles:
    - Cashiers (Pam): New Sale, Product Catalog, Close Shift
    - Managers (Ralph/Felix): + Sales Reports, All Transactions
    - Admins (Felix): + User Management, Settings

    Real-time stats (fetched via API):
    - Today's sales total
    - Transaction count
    - Current shift time

    Authentication: Client-side JWT validation (token in sessionStorage)
    """
    return templates.TemplateResponse("pos/dashboard.html", {"request": request})


@html_router.get("/pos/my-day", response_class=HTMLResponse, name="pos_my_day")
async def pos_my_day(request: Request):
    """
    My Day — the employee-facing daily checkup (timesheet + living day view).

    Felix's spreadsheet, made a no-brainer on a phone: see your hours and sales so far,
    then close out your day (start/finish/lunch → hours) in one tap. Rides the existing
    HR engine (/api/v1/hr/*). Auth is client-side JWT like the other POS screens; the HR
    API resolves the employee from the token (with a demo-safe username/email bridge).
    """
    return templates.TemplateResponse("pos/my_day.html", {"request": request})


@html_router.get("/pos/scan", response_class=HTMLResponse, name="pos_scan")
async def pos_scan(request: Request):
    """
    Product Scan & Cart Management - Primary sales interface

    Solves Pam's workflow problem:
    - 3000 products in catalog
    - Most items don't have barcodes
    - Can't remember all codes
    - Needs simple, foolproof workflow

    Three input modes:

    1. BARCODE MODE (default):
       - Auto-focus input field
       - Enter to scan and add
       - For items with barcodes

    2. SEARCH MODE:
       - Fuzzy search by name/description
       - Handles typos
       - For quick lookups

    3. CATALOG MODE (items WITHOUT barcodes):
       Category-based classification:
       - Growing Supplies: A (>CHF 250), B (CHF 21-50), C (<CHF 20)
       - Decorations: A (>CHF 250), B (CHF 21-50), C (<CHF 20)
       - Miscellaneous: A (>CHF 250), B (CHF 21-50), C (<CHF 20)

       Pam workflow:
       1. Customer asks "how much is this?"
       2. Item has no barcode
       3. Pam selects category (e.g., "Growing - B Items")
       4. Enters price (e.g., CHF 35.00)
       5. Optional description
       6. Item added to cart
       7. Felix reviews catalog items later and adds barcodes

    Features:
    - Live cart with quantity adjustment
    - Remove items
    - Discount validation (Cashiers max 10%, Managers unlimited)
    - Swiss VAT calculation (7.7%)
    - Real-time totals
    """
    return templates.TemplateResponse("pos/scan.html", {"request": request})


@html_router.get("/pos/catalog", response_class=HTMLResponse, name="pos_catalog")
async def pos_catalog(request: Request):
    """Catalog management dashboard (BL-88) — manager/admin CRUD over products.

    Surfaces the create / update / soft-delete that already exist in the API:
    search, edit price/stock/picture/reorder fields, discontinue + reactivate,
    create new. Roles are enforced by the API endpoints (manager/admin); this
    page just renders the screen.
    """
    return templates.TemplateResponse("pos/catalog.html", {"request": request})


# Suppliers whose products wear the ARTISAN framing on the postcard ("Handmade",
# "made with love"). A wholesale DISTRIBUTOR must never read "Handmade · FourTwenty" on a
# pack of rolling papers. Signal = the supplier's adapter_type: local makers are hand-onboarded
# ('manual', e.g. Ecolution) or authored in-system ('incms', e.g. Mama Cynthia); everything
# imported (magento/tamar/csv) or a bare wholesale row is a distributor → neutral card.
# TODO: promote to an explicit suppliers.is_maker flag when the schema next moves.
_MAKER_ADAPTER_TYPES = {"manual", "incms"}


async def _supplier_is_maker(db, supplier_name: str | None) -> bool:
    """Does this product's supplier get the 'Handmade / made with love' framing? Matched by
    NAME (product.supplier_name is denormalized; receiving mints LZ- SKUs so the prefix isn't
    reliable). Unknown/missing supplier → False (neutral card — the safe default)."""
    if not supplier_name:
        return False
    at = (await db.execute(
        select(SupplierModel.adapter_type).where(SupplierModel.name == supplier_name)
    )).scalar_one_or_none()
    return (at or "").strip().lower() in _MAKER_ADAPTER_TYPES


def _postcard_store_footer(store, origin: str) -> dict | None:
    """Flatten a StoreSettingsModel into the postcard's footer dict (name / hours / address /
    phone / logo), or None if there's no store row. The card's CTA + this footer turn a
    shared maker card into foot traffic back to the counter. Address is assembled from the
    line/city/postal fields; a relative logo path is made absolute for the shared preview."""
    if store is None:
        return None
    line1 = ", ".join(p for p in (store.address_line1, store.address_line2) if p)
    citely = " ".join(x for x in (store.postal_code, store.city) if x)
    address = ", ".join(x for x in (line1, citely) if x)
    logo = store.receipt_logo_url or None
    if logo and not logo.startswith(("http://", "https://")):
        logo = origin + (logo if logo.startswith("/") else "/" + logo)
    return {
        "name": store.store_name,
        "hours": store.opening_hours,
        "address": address or None,
        "phone": store.phone,
        "logo": logo,
    }


@html_router.get("/pos/products/{product_id}/postcard", response_class=HTMLResponse, name="product_postcard")
async def product_postcard(
    product_id: str,
    request: Request,
    lang: str = "de",
    db: AsyncSession = Depends(get_db_session),
):
    """The postcard maker: any product → a beautiful, printable, SHAREABLE card — its image,
    story (in `lang`, via BL-36), price, maker, a QR to itself, and a serial that can't be
    copied. Public by design (the whole point is to share it). The card themes to the product's
    own colour when it carries one (Mama Cynthia's balms are colour-coded)."""
    import hashlib
    from src.db.models.product_model import ProductModel
    from src.services.product_translations import ensure_description
    from src.services.short_links import ensure_short_code

    product = await db.get(ProductModel, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    desc = await ensure_description(db, product, lang)
    attrs = product.attributes or {}
    # A serial that's stable per product+revision and looks official — Angel's "can't be copied".
    serial = product.sku + "-" + hashlib.sha1(
        f"{product.sku}|{product.updated_at}".encode()).hexdigest()[:6].upper()
    proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    origin = f"{proto}://{host}"
    # Carry the CURRENT language on the share/QR link so a shared card opens in the language the
    # sharer chose (not the server default). Without ?lang= the recipient always landed in German.
    share_url = f"{origin}/pos/products/{product_id}/postcard?lang={lang}"
    # The QR encodes the SHORT url (/p/{code}?lang=) so it stays low-density → scannable printed small.
    # Falls back to the full url if a code couldn't be minted. (Share + QR use it; og:url stays full+lang.)
    code = await ensure_short_code(db, product_id)
    qr_url = f"{origin}/p/{code}?lang={lang}" if code else share_url

    # og:image must be an ABSOLUTE, publicly-fetchable URL — the WhatsApp/iMessage/Telegram
    # scraper fetches it server-side to build the rich share preview. Mama Cynthia's photos are
    # already absolute (hotlinked from her site); Banco-hosted images get the origin prefixed.
    img = product.image_url or ""
    if img and not img.startswith(("http://", "https://")):
        img = origin + (img if img.startswith("/") else "/" + img)
    og_image = img or None
    body = (desc.get("description") or product.description or "").strip()
    og_description = (body[:277] + "…") if len(body) > 280 else body

    # Store footer — the CLOSE: turn every shared card into a "come get it" at Felix's counter.
    # Built from the shop's own store_settings (name/hours/address/phone/logo) so it's real data,
    # never hardcoded. None → the card falls back to the plain brand line.
    store = await get_active_store_settings(db)
    store_ctx = _postcard_store_footer(store, origin)
    is_maker = await _supplier_is_maker(db, product.supplier_name)

    return templates.TemplateResponse("pos/postcard.html", {
        "request": request,
        "name": desc.get("name") or product.name,   # translated name → title matches the language
        "description": desc.get("description") or product.description or "",
        "provenance": desc.get("provenance"),
        "price": f"{float(product.price):.2f}" if product.price is not None else None,
        "currency": "CHF",
        "image_url": product.image_url,
        "supplier": product.supplier_name,
        "colour": (attrs.get("colour") or "").lower(),
        "serial": serial,
        "share_url": share_url,
        "qr_url": qr_url,
        "lang": lang,
        "og_image": og_image,
        "og_description": og_description,
        "store": store_ctx,
        "is_maker": is_maker,
    })


@html_router.get("/pos/products/{product_id}/postcard-sheet", response_class=HTMLResponse, name="product_postcard_sheet")
async def product_postcard_sheet(
    product_id: str,
    request: Request,
    lang: str = "de",
    db: AsyncSession = Depends(get_db_session),
):
    """4-UP print sheet (Angel's Format C standard): four of the product's postcard on one A4,
    cut marks + a Banksy-beat serial per card (01/04 … 04/04, each tied to a per-sheet run id so
    no two prints are ever the same — provenance, not surveillance). One horizontal + one
    vertical cut = four cards."""
    import hashlib
    import secrets
    from src.db.models.product_model import ProductModel
    from src.services.product_translations import ensure_description
    from src.services.short_links import ensure_short_code

    product = await db.get(ProductModel, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    desc = await ensure_description(db, product, lang)
    attrs = product.attributes or {}
    run = secrets.token_hex(2).upper()                    # per-sheet run id (Banksy provenance)
    base_serial = hashlib.sha1(f"{product.sku}|{product.updated_at}".encode()).hexdigest()[:4].upper()
    proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    origin = f"{proto}://{host}"
    share_url = f"{origin}/pos/products/{product_id}/postcard?lang={lang}"
    code = await ensure_short_code(db, product_id)        # short QR → scannable printed small
    qr_url = f"{origin}/p/{code}?lang={lang}" if code else share_url   # carry lang through the QR
    cards = [{"n": i, "serial": f"{product.sku}·{base_serial}·{run}-{i:02d}/04"} for i in range(1, 5)]
    store_ctx = _postcard_store_footer(await get_active_store_settings(db), origin)
    is_maker = await _supplier_is_maker(db, product.supplier_name)

    return templates.TemplateResponse("pos/postcard-sheet.html", {
        "request": request,
        "name": desc.get("name") or product.name,   # translated name → title matches the language
        "description": desc.get("description") or product.description or "",
        "price": f"{float(product.price):.2f}" if product.price is not None else None,
        "currency": "CHF",
        "image_url": product.image_url,
        "supplier": product.supplier_name,
        "colour": (attrs.get("colour") or "").lower(),
        "share_url": share_url,
        "qr_url": qr_url,
        "lang": lang,
        "cards": cards,
        "store": store_ctx,
        "is_maker": is_maker,
    })


@html_router.get("/p/{code}", name="short_link")
async def short_link(code: str, lang: str = "", db: AsyncSession = Depends(get_db_session)):
    """Short QR target: /p/{code} → the product's postcard. The QR encodes THIS (few characters →
    low-density → scans reliably printed small on a label). Carries ?lang= through so a shared card
    opens in the language the sharer chose. Each hit bumps the product's scan counter (the QR is
    trackable — free analytics), then 302s to the full card. Public by design."""
    from fastapi.responses import RedirectResponse
    from src.services.short_links import resolve_and_bump

    product_id = await resolve_and_bump(db, code)
    if not product_id:
        raise HTTPException(status_code=404, detail="Unknown code")
    target = f"/pos/products/{product_id}/postcard"
    if lang in ("de", "en", "fr", "it"):
        target += f"?lang={lang}"
    return RedirectResponse(url=target, status_code=302)


@html_router.get("/pos/receiving", response_class=HTMLResponse, name="pos_receiving")
async def pos_receiving(request: Request):
    """Receiving / goods-in (BL-91) — scan an item, type the count, stock goes up.

    Lean restock screen: reuses the shared PosScanner + the lazy-create path, builds
    a receiving list, then POSTs the batch to /api/v1/pos/receiving (manager/admin).
    """
    return templates.TemplateResponse("pos/receiving.html", {"request": request})


@html_router.get("/pos/suppliers", response_class=HTMLResponse, name="pos_suppliers")
async def pos_suppliers(request: Request):
    """Supplier Registry admin screen — list + add/edit suppliers (import sources).

    Each supplier carries a unique SKU prefix (TAM-, FTW-, …). Manager/admin manage
    the list; it feeds the receiving 'pick a supplier' dropdown.
    """
    return templates.TemplateResponse("pos/suppliers.html", {"request": request})


@html_router.get("/pos/reorder", response_class=HTMLResponse, name="pos_reorder")
async def pos_reorder(request: Request):
    """BL-21/22 — the Order Book: the digital reorder pencil-list. Velocity suggestions +
    order-state (to_order → on_order → received) + per-line supplier pick. Manager-gated
    client-side; the mutating API is role-gated server-side."""
    return templates.TemplateResponse("pos/reorder.html", {"request": request})


@html_router.get("/pos/checkout", response_class=HTMLResponse, name="pos_checkout")
async def pos_checkout(request: Request):
    """
    Checkout & Payment - Final transaction confirmation

    Displays:
    - Order summary (all cart items)
    - Price breakdown:
      * Subtotal
      * Discount (if applied)
      * VAT (7.7%)
      * Total

    Payment method selection:
    - Cash (adds to cash drawer)
    - Card (terminal payment - Visa/Mastercard)
    - Mobile (TWINT/Apple Pay/etc)

    Dry-run preview shows what will happen:
    - Cash drawer: +CHF amount (or 0 for card/mobile)
    - Inventory: List of deductions
    - Receipt: Will print
    - Daily total: +CHF amount

    Actions:
    - Cancel: Return to scan
    - Edit Cart: Return to scan
    - Confirm & Complete: Process transaction

    API workflow:
    1. POST /api/v1/pos/transactions (create empty transaction)
    2. POST /api/v1/pos/transactions/{id}/items (add each item)
    3. POST /api/v1/pos/transactions/{id}/checkout (finalize with payment)
    """
    return templates.TemplateResponse("pos/checkout.html", {"request": request})


@html_router.get("/pos/closeout", response_class=HTMLResponse, name="pos_closeout")
async def pos_closeout(request: Request):
    """
    Close Shift / End of Day - Pam's shift closure

    Problem: Pam takes 90 minutes to close shift (paper-based)
    Solution: Automated calculations, visual guidance

    Auto-calculated shift summary:
    - Cashier name (from JWT token)
    - Shift time (start - current)
    - Total transactions
    - Total sales (CHF)
    - Cash sales breakdown
    - Card/Mobile sales breakdown

    Cash drawer count workflow:
    1. Enter notes amount (CHF)
    2. Enter coins amount (CHF)
    3. System calculates total
    4. Shows difference vs expected
    5. Visual feedback:
       - Green check: Perfect match
       - Yellow warning: Difference detected

    Adjustment options:
    - No adjustment: Close immediately
    - Add note: Explain discrepancy (e.g., "Customer returned item")
    - Request manager approval: Escalate to Felix/Ralph

    Goal: Reduce Pam's 90-minute close to <10 minutes

    API call:
    - GET /api/v1/pos/reports/daily-summary (fetch today's stats)
    """
    return templates.TemplateResponse("pos/closeout.html", {"request": request})


@html_router.get("/pos/shift", response_class=HTMLResponse, name="pos_shift")
async def pos_shift(request: Request):
    """My Drawer -- per-cashier cash shift: open with a counted float, paid-in/out,
    close by counting out (expected vs counted, variance, one-page report)."""
    return templates.TemplateResponse("pos/shift.html", {"request": request})


@html_router.get("/pos/cash-count", response_class=HTMLResponse, name="pos_cash_count")
async def pos_cash_count(request: Request):
    """
    Cash Drawer Count - End of Day Reconciliation

    Felix's daily ritual: Count the drawer, verify against POS totals.
    Features denomination-by-denomination counting (Swiss Francs).

    Swiss Franc Denominations:
    - Notes: 200, 100, 50, 20, 10 CHF
    - Coins: 5, 2, 1 CHF, 50/20/10/5 Rappen

    Workflow:
    1. Enter cashier name
    2. Count each denomination
    3. System calculates total
    4. Compare against expected (from POS)
    5. Route variance (bonus/slush/review)
    6. Submit and print summary

    Variance Rules:
    - Perfect (0): +1 bonus point for cashier
    - Small over (<0.50): Goes to cashier bonus pool
    - Small under (<0.50): Goes to slush fund
    - Large variance: Manager review required

    URL: https://helix.local/pos/cash-count
    """
    return templates.TemplateResponse("pos/cash_count.html", {"request": request})


@html_router.get("/pos/customer-lookup", response_class=HTMLResponse, name="pos_customer_lookup")
async def pos_customer_lookup(request: Request):
    """
    Customer Lookup - Find CRACK profiles for checkout recognition

    The "Larry/Poppie" problem solved:
    - Customer walks in, says "I'm Poppie"
    - Cashier searches by handle, Instagram, email, or phone
    - Profile loads with tier discount, credits, CRACK level
    - Apply to checkout for personalized pricing

    Features:
    - Search by handle, @instagram, email, phone
    - Profile card with loyalty tier (Bronze→Diamond)
    - CRACK level display (Seedling→Oracle)
    - Credits balance and redeemable vouchers
    - Favorites and suggestions
    - Birthday/tier alerts
    - Quick-add new customer form
    - Recent customers grid

    Workflow:
    1. Search "poppie" or "@poppie_420"
    2. See Larry's profile (Gold tier, 247 credits)
    3. Click "Use for Checkout"
    4. Redirect to scan with 15% discount applied

    URL: https://helix.local/pos/customer-lookup
    """
    return templates.TemplateResponse("pos/customer_lookup.html", {"request": request})


@html_router.get("/pos/kb-approvals", response_class=HTMLResponse, name="pos_kb_approvals")
async def pos_kb_approvals(request: Request):
    """
    KB Approvals - Owner's knowledge contribution review

    "Knowledge is the gold" - KB-001

    CRACKs write KBs (Knowledge Base articles) about:
    - Recipes (CBD tanning butter, coconut extract method)
    - Protocols (Purple Power Sleep Protocol)
    - Guides (Grinder Maintenance 101)
    - Lab reports (tested formulas)

    Owner Approval Workflow:
    1. CRACK submits KB
    2. Owner sends to other CRACKs for review
    3. CRACKs rate and recommend (or flag concerns)
    4. Owner sees review summary
    5. 1-click approve or batch "Select All"
    6. Credits awarded to author

    Credit Calculation:
    - Base: 100 credits
    - With images: +25
    - With video: +50
    - With BOM/Recipe: +75
    - With lab report: +100
    - Featured bonus: +250

    Features:
    - Pending/In Review/Approved tabs
    - Quality badges (images, video, BOM, lab)
    - JH chapter reference display
    - CRACK review summary
    - Batch select and approve
    - Preview modal with full content
    - Feature KB button (+250 bonus)

    URL: https://helix.local/pos/kb-approvals
    """
    return templates.TemplateResponse("pos/kb_approvals.html", {"request": request})


@html_router.get("/pos/receipt/{transaction_id}", response_class=HTMLResponse, name="pos_receipt")
async def pos_receipt(request: Request, transaction_id: UUID):
    """
    Receipt View & Print - Display completed transaction receipt

    A4-optimized printable receipt for customer.
    Auto-loads transaction data and store settings.

    Features:
    - Company header (logo, name, address, VAT number)
    - Transaction details (date, time, cashier, receipt#)
    - Line items table
    - Totals breakdown (subtotal, discount, VAT, total)
    - Payment method
    - PAID watermark
    - Print button (window.print())
    - Reprint anytime

    Used for:
    - Auto-display after checkout
    - Reprint from transaction history
    - Closeout review (Pam checks all receipts)
    - Customer requests copy

    Pam's workflow:
    1. Complete transaction → receipt auto-displays
    2. Click Print → browser print dialog
    3. Customer gets receipt
    4. Receipt saved in history for reprint

    Felix's workflow (at closeout):
    1. Review all receipts
    2. Spot errors (e.g., CHF 25 should be CHF 250)
    3. Call Pam for explanation
    4. Note for Banana journal entry
    """
    return templates.TemplateResponse("pos/receipt.html", {"request": request})


@html_router.get("/p/{product_id}", name="banco_permalink")
async def banco_permalink(product_id: UUID, db: AsyncSession = Depends(get_db_session)):
    """Banco-owned permalink — the receipt-QR target (Wire 2 of the community loop).

    It's known at SALE time (just the product id), so the QR can print on the receipt before the
    shop ever showcases the item. When scanned it 302s to the La Piazza listing IF the shop has
    showcased it, otherwise to La Piazza's door (discover + join the community). Decoupled from
    publish timing — the printed QR never goes stale. PUBLIC by design (it's a redirect, no data)."""
    from fastapi.responses import RedirectResponse
    base = get_settings().SQUARE_PUBLIC_URL.rstrip("/")
    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()
    target = f"{base}/items/{product.lapiazza_slug}" if (product and product.lapiazza_slug) else base
    return RedirectResponse(target, status_code=302)


@html_router.get("/join", name="banco_join_lapiazza")
async def banco_join_lapiazza():
    """Banco-owned 'join La Piazza' permalink — the single QR printed on every receipt (Wire 2).
    A ONE-WAY funnel: it 302s the buyer to La Piazza so they discover + join the community. By
    design there is NO tie-back to HelixPOS — the till does loyalty internally, La Piazza is the
    community, and this QR is just the door between them. Banco-owned so the destination can change
    without reprinting receipts. PUBLIC (redirect, no data)."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(get_settings().SQUARE_PUBLIC_URL.rstrip("/"), status_code=302)


@html_router.get("/pos/products", response_class=HTMLResponse, name="pos_products")
async def pos_products(request: Request):
    """
    Product Catalog Browser - Browse all products

    Future features:
    - Category filters
    - Search bar
    - Sort by name/price/category
    - Quick add to cart

    For now: Redirects to scan page
    """
    return templates.TemplateResponse("pos/scan.html", {"request": request})


@html_router.get("/pos/search", response_class=HTMLResponse, name="pos_search")
async def pos_search(request: Request):
    """
    Fast Product Search - Instant search with 7,442+ products

    Features:
    - Fuzzy name search (trigram similarity)
    - Instant barcode lookup (<5ms)
    - Category filtering
    - Full-text search (German language)
    - Product images
    - Add to cart functionality

    Barcode Scanner Support:
    - Auto-detects fast sequential input
    - Instant product lookup on scan
    - Auto-adds to cart on exact match

    URL: https://helix-platform.local/pos/search
    """
    return templates.TemplateResponse("pos/search.html", {"request": request})


@html_router.get("/pos/reports", response_class=HTMLResponse, name="pos_reports")
async def pos_reports(request: Request):
    """
    Sales Reports - Manager/Admin analytics

    Future features:
    - Daily/Weekly/Monthly charts
    - Top products
    - Cashier performance
    - Payment method breakdown
    - Category analysis
    """
    return templates.TemplateResponse("pos/reports.html", {"request": request})


@html_router.get("/pos/reports/products", response_class=HTMLResponse, name="pos_product_sales")
async def pos_product_sales(request: Request):
    """Product Sales report (Felix day-one wishlist) - what sold by qty/revenue over a
    date range, tap a product to drill into who bought it. Manager/admin (the API endpoints
    enforce the role; this just serves the shell). See docs/BANCO-DAY-ONE-WISHLIST.md."""
    return templates.TemplateResponse("pos/product_sales.html", {"request": request})


@html_router.get("/pos/cleanup", response_class=HTMLResponse, name="pos_cleanup")
async def pos_cleanup(request: Request):
    """Sold-but-not-set-up cleanup cockpit (Felix/manager) — products a cashier quick-added that
    have SOLD but still need a category / cost / 18+ confirmed. Manager/admin (the /catalog/
    cleanup-queue + PUT /products endpoints enforce the role; this just serves the shell)."""
    return templates.TemplateResponse("pos/cleanup.html", {"request": request})


@html_router.get("/pos/transactions", response_class=HTMLResponse, name="pos_transactions")
async def pos_transactions(request: Request):
    """
    Transaction History - View all sales transactions

    Critical for Pam's closeout workflow:
    - Review all today's transactions
    - Click to view receipt
    - Reprint any receipt
    - Spot errors (e.g., CHF 25 should be CHF 250)

    Features:
    - Filter by date (default: today)
    - Filter by status (completed, open, voided)
    - Filter by payment method (cash, card, mobile)
    - Summary stats (count, total sales, cash vs card)
    - Click transaction to view receipt
    - Reprint button (opens in new tab)

    Manager features:
    - View all cashiers' transactions
    - Filter by cashier
    - Void transaction (with approval)

    Pam's workflow at closeout:
    1. Click "Transaction History" from dashboard
    2. Review all today's receipts
    3. Spot mistake: "That CHF 25 should be CHF 250!"
    4. Call Felix: "Hey boss, line 15 is wrong"
    5. Felix: "OK, note it for Banana adjustment"
    """
    return templates.TemplateResponse("pos/transactions.html", {"request": request})


@html_router.get("/pos/admin", response_class=HTMLResponse, name="pos_admin")
async def pos_admin(request: Request):
    """
    User Management - Admin role management

    Future features:
    - List all users
    - Assign/remove POS roles
    - View user activity
    - Enable/disable users

    For now: Placeholder
    """
    return templates.TemplateResponse("pos/dashboard.html", {"request": request})


@html_router.get("/pos/settings", response_class=HTMLResponse, name="pos_settings")
async def pos_settings(request: Request):
    """
    POS System Settings - Admin configuration

    Future features:
    - Tax rate settings
    - Receipt header/footer
    - Printer configuration
    - Category management

    Live: store identity, contact, VAT, receipt header/footer/logo, discount caps —
    editable by admin (Felix), shown on every receipt. Wired to GET/PUT /settings/{n}.
    """
    return templates.TemplateResponse("pos/settings.html", {"request": request})
