# File: src/services/camper_telegram_service.py
"""
Camper & Tour Telegram Notification Service.
Lightweight bot API client for quick customer alerts.

Setup: Create bot via @BotFather, get token, save customer chat_ids.
For demo: stub that logs messages. Real bot needs token + chat_id.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Bot token from environment (set via docker-compose or .env)
BOT_TOKEN = os.environ.get("CAMPER_TELEGRAM_BOT_TOKEN", "")


async def send_telegram_message(chat_id: str, message: str) -> bool:
    """
    Send message via Telegram Bot API.
    Returns True if sent, False if failed or token not configured.
    """
    if not BOT_TOKEN:
        logger.info(f"[TELEGRAM STUB] To {chat_id}: {message}")
        return True  # Stub mode -- log and succeed

    try:
        import httpx
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
            })

        if response.status_code == 200:
            logger.info(f"Telegram message sent to {chat_id}")
            return True
        else:
            logger.error(f"Telegram API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Telegram send failed to {chat_id}: {e}")
        return False


async def notify_vehicle_ready(chat_id: str, customer_name: str, vehicle_plate: str) -> bool:
    """Quick alert: vehicle ready for pickup"""
    message = (
        f"<b>Camper &amp; Tour - Trapani</b>\n\n"
        f"Gentile {customer_name},\n"
        f"il suo veicolo <b>{vehicle_plate}</b> e pronto per il ritiro!\n\n"
        f"Ci contatti per concordare il ritiro.\n"
        f"Tel: +39 0923 534452"
    )
    return await send_telegram_message(chat_id, message)


async def notify_quote_ready(chat_id: str, customer_name: str, quote_number: str, total: str) -> bool:
    """Alert: quotation ready for review"""
    message = (
        f"<b>Camper &amp; Tour - Trapani</b>\n\n"
        f"Gentile {customer_name},\n"
        f"il preventivo <b>{quote_number}</b> e pronto.\n"
        f"Totale: <b>{total}</b> (IVA inclusa)\n\n"
        f"Ci contatti per confermare."
    )
    return await send_telegram_message(chat_id, message)


async def notify_deposit_received(chat_id: str, customer_name: str, amount: str) -> bool:
    """Alert: deposit received"""
    message = (
        f"<b>Camper &amp; Tour - Trapani</b>\n\n"
        f"Gentile {customer_name},\n"
        f"acconto di <b>{amount}</b> ricevuto.\n"
        f"I lavori inizieranno a breve!"
    )
    return await send_telegram_message(chat_id, message)
