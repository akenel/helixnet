# File: src/compute/consumer.py
# Purpose: LPCX dedicated aio-pika consumer. The brain's concurrency ceiling IS the
# prefetch_count (= LPCX_BRAIN_CAP slots); the durable queue is the FIFO wait line.
# Manual ack via message.process() = at-least-once. Run as its own process/container:
#     python -m src.compute.consumer

import asyncio
import json
import logging
import os
from uuid import UUID

import aio_pika

from src.compute.queue import AMQP_URL, QUEUE_NAME
from src.compute.runner import execute_job
from src.compute.fairness import fair_brain

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("lpcx.consumer")

# Prefetch HIGH so messages from ALL users get pulled (no head-of-line blocking);
# the FairBrain gate -- not prefetch -- enforces the global cap + per-user fairness.
PREFETCH = int(os.getenv("LPCX_PREFETCH", "500"))


async def _handle(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    # requeue=False: on unhandled error, drop rather than poison-loop (execute_job
    # already marks FAILED for its own errors).
    async with message.process(requeue=False):
        data = json.loads(message.body.decode())
        job_id = UUID(data["job_id"])
        owner = data["owner"]
        node = data.get("node", "lp-hetzner-0")
        brain_mode = data.get("brain_mode", "shared")
        byo_endpoint = data.get("byo_endpoint")
        byo_model = data.get("byo_model")

        if brain_mode == "byo":
            # BYO is off the shared brain -> no fairness gate, no global cap.
            await execute_job(job_id, owner, node, brain_mode, byo_endpoint, byo_model)
        else:
            # Wait for a fair slot (global cap + dynamic per-user cap), then run.
            async with fair_brain.slot(owner):
                await execute_job(job_id, owner, node, brain_mode, byo_endpoint, byo_model)


def _load_all_models() -> None:
    """Register the app's model set + configure mappers up front (fail fast), so this
    separate process has a valid registry before it touches the DB. Mirrors the app's
    import set (models/__init__) -- NOT a blanket import (some legacy modules redefine
    the same table)."""
    import src.db.models  # noqa: F401  -- triggers the canonical model set
    from sqlalchemy.orm import configure_mappers
    configure_mappers()
    logger.info("ORM models loaded + mappers configured")


async def main() -> None:
    _load_all_models()
    connection = await aio_pika.connect_robust(AMQP_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=PREFETCH)   # <- the ceiling
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.consume(_handle)
    logger.info(f"LPCX consumer up: queue={QUEUE_NAME} prefetch(slots)={PREFETCH}")
    await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
