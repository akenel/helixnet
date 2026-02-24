# File: src/services/isotto_preview_service.py
"""
ISOTTO Sport Preview Service -- Generates personalization preview PNGs.
Uses Puppeteer (scripts/generate-preview.js) to render garment mockups
with player names, numbers, and custom text overlaid.

"20 players, 20 names, 20 numbers. Perfect every time."
"""
import asyncio
import json
import logging
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.models.isotto_order_line_item_model import IsottoOrderLineItemModel
from src.db.models.isotto_catalog_model import IsottoCatalogProductModel

logger = logging.getLogger(__name__)

# Path to the Puppeteer preview generator script
PREVIEW_SCRIPT = Path(__file__).parent.parent.parent / "scripts" / "generate-preview.js"

# Output directory for preview PNGs
PREVIEW_OUTPUT_DIR = Path("/tmp/isotto-previews")


async def generate_preview(
    line_item: IsottoOrderLineItemModel,
    product: IsottoCatalogProductModel | None = None,
) -> str | None:
    """
    Generate a preview PNG for a single line item.
    Returns the output file path, or None on failure.
    """
    PREVIEW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PREVIEW_OUTPUT_DIR / f"{line_item.id}.png"

    data = {
        "product_name": product.name if product else "Custom Item",
        "color": line_item.color or "white",
        "size": line_item.size or "-",
        "name_text": line_item.name_text or "",
        "number_text": line_item.number_text or "",
        "text_color": line_item.text_color or "navy",
        "font_name": line_item.font_name or "Impact",
        "placement": line_item.artwork_placement or "back",
        "custom_text": line_item.custom_text or "",
    }

    try:
        proc = await asyncio.create_subprocess_exec(
            "node", str(PREVIEW_SCRIPT),
            "--data", json.dumps(data),
            "--output", str(output_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error(f"Preview generation failed for item {line_item.id}: {stderr.decode()}")
            return None

        result = json.loads(stdout.decode())
        if result.get("status") == "ok":
            logger.info(f"Preview generated for item {line_item.id}: {output_path}")
            return str(output_path)
        else:
            logger.error(f"Preview generation error: {result.get('message')}")
            return None

    except Exception as e:
        logger.error(f"Preview generation exception for item {line_item.id}: {e}")
        return None


async def generate_order_previews(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> dict:
    """
    Generate preview PNGs for all line items in an order.
    Returns a summary dict: {generated: N, failed: N, paths: [...]}
    """
    result = await db.execute(
        select(IsottoOrderLineItemModel)
        .where(IsottoOrderLineItemModel.order_id == order_id)
        .options(selectinload(IsottoOrderLineItemModel.catalog_product))
        .order_by(IsottoOrderLineItemModel.sort_order)
    )
    items = result.scalars().all()

    if not items:
        return {"generated": 0, "failed": 0, "paths": [], "message": "No line items found"}

    generated = 0
    failed = 0
    paths = []

    for item in items:
        product = item.catalog_product
        output_path = await generate_preview(item, product)

        if output_path:
            # Update the line item with the preview path
            item.preview_image_url = output_path
            generated += 1
            paths.append({"item_id": str(item.id), "name": item.name_text, "path": output_path})
        else:
            failed += 1

    await db.commit()

    logger.info(f"Order {order_id} previews: {generated} generated, {failed} failed")
    return {
        "generated": generated,
        "failed": failed,
        "total": len(items),
        "paths": paths,
    }
