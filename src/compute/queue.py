# File: src/compute/queue.py
# Purpose: LPCX RabbitMQ wiring. Durable queue `lpcx.jobs`, persistent messages.
# Used by the API (publisher) and the consumer (declares the same queue).

import json
import logging
import os

import aio_pika

logger = logging.getLogger("lpcx.queue")

AMQP_URL = (
    os.getenv("LPCX_AMQP_URL")
    or os.getenv("CELERY_BROKER_URL")
    or "amqp://helix_user:helix_pass@rabbitmq:5672/"
)
QUEUE_NAME = "lpcx.jobs"

_connection: aio_pika.RobustConnection | None = None
_channel: aio_pika.abc.AbstractChannel | None = None


async def _get_channel() -> aio_pika.abc.AbstractChannel:
    """Lazy robust connection + channel; auto-reconnects on broker blips."""
    global _connection, _channel
    if _channel is None or _channel.is_closed:
        _connection = await aio_pika.connect_robust(AMQP_URL)
        _channel = await _connection.channel()
        await _channel.declare_queue(QUEUE_NAME, durable=True)
        logger.info(f"LPCX queue ready: {QUEUE_NAME} @ {AMQP_URL.split('@')[-1]}")
    return _channel


async def publish_job(payload: dict) -> None:
    """Publish a job to the durable queue (persistent message -> survives broker restart)."""
    channel = await _get_channel()
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        ),
        routing_key=QUEUE_NAME,
    )
