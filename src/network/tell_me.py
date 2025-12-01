# src/network/tell_me.py
"""
TELL ME Network Service

The heart of HelixNETWORK - connecting CRACKs to CRACKs.

Usage:
    from src.network import TellMeService

    service = TellMeService()

    # CRACK needs something
    request = service.broadcast_need(
        shop_id="blowup",
        product_query="Purple Power base ingredient",
        quantity=5,
        unit="kg"
    )

    # Another CRACK responds
    service.respond_to_need(
        request_id=request.id,
        shop_id="fourtwenty",
        product_sku="SKU-4421",
        price_per_unit=45.00,
        currency="CHF",
        available_quantity=10
    )
"""

import json
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List
import pika

# RabbitMQ connection settings (from docker-compose)
RABBITMQ_HOST = "rabbitmq"
RABBITMQ_USER = "helix_user"
RABBITMQ_PASS = "helix_pass"
RABBITMQ_VHOST = "/"

EXCHANGE_NAME = "helix.network"
QUEUE_REQUESTS = "tell_me.requests"
QUEUE_RESPONSES = "tell_me.responses"
QUEUE_ORDERS = "tell_me.orders"


@dataclass
class TellMeRequest:
    """A CRACK needs something"""
    id: str
    shop_id: str           # Who's asking (realm name)
    shop_name: str         # Display name
    product_query: str     # What they need (free text or SKU)
    quantity: float
    unit: str              # kg, units, liters, etc.
    urgency: str           # normal, urgent, asap
    notes: Optional[str]
    created_at: str
    expires_at: Optional[str]
    status: str            # open, fulfilled, expired, cancelled

    @classmethod
    def create(cls, shop_id: str, shop_name: str, product_query: str,
               quantity: float, unit: str = "units", urgency: str = "normal",
               notes: str = None):
        return cls(
            id=str(uuid.uuid4()),
            shop_id=shop_id,
            shop_name=shop_name,
            product_query=product_query,
            quantity=quantity,
            unit=unit,
            urgency=urgency,
            notes=notes,
            created_at=datetime.utcnow().isoformat(),
            expires_at=None,
            status="open"
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> 'TellMeRequest':
        return cls(**json.loads(data))


@dataclass
class TellMeResponse:
    """A CRACK offers what another needs"""
    id: str
    request_id: str        # Which request this responds to
    shop_id: str           # Who's offering
    shop_name: str
    product_sku: str       # Their product SKU
    product_name: str
    price_per_unit: float
    currency: str
    available_quantity: float
    lead_time: str         # "immediate", "1 day", "3 days", etc.
    notes: Optional[str]
    created_at: str
    status: str            # pending, accepted, rejected, expired

    @classmethod
    def create(cls, request_id: str, shop_id: str, shop_name: str,
               product_sku: str, product_name: str, price_per_unit: float,
               available_quantity: float, currency: str = "CHF",
               lead_time: str = "1 day", notes: str = None):
        return cls(
            id=str(uuid.uuid4()),
            request_id=request_id,
            shop_id=shop_id,
            shop_name=shop_name,
            product_sku=product_sku,
            product_name=product_name,
            price_per_unit=price_per_unit,
            currency=currency,
            available_quantity=available_quantity,
            lead_time=lead_time,
            notes=notes,
            created_at=datetime.utcnow().isoformat(),
            status="pending"
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> 'TellMeResponse':
        return cls(**json.loads(data))


@dataclass
class TellMeOrder:
    """A CRACK accepts an offer"""
    id: str
    request_id: str
    response_id: str
    buyer_shop_id: str
    buyer_shop_name: str
    seller_shop_id: str
    seller_shop_name: str
    product_sku: str
    product_name: str
    quantity: float
    unit: str
    price_per_unit: float
    total_price: float
    currency: str
    created_at: str
    status: str            # placed, confirmed, shipped, delivered, cancelled

    @classmethod
    def create(cls, request: TellMeRequest, response: TellMeResponse, quantity: float):
        total = quantity * response.price_per_unit
        return cls(
            id=str(uuid.uuid4()),
            request_id=request.id,
            response_id=response.id,
            buyer_shop_id=request.shop_id,
            buyer_shop_name=request.shop_name,
            seller_shop_id=response.shop_id,
            seller_shop_name=response.shop_name,
            product_sku=response.product_sku,
            product_name=response.product_name,
            quantity=quantity,
            unit=request.unit,
            price_per_unit=response.price_per_unit,
            total_price=total,
            currency=response.currency,
            created_at=datetime.utcnow().isoformat(),
            status="placed"
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> 'TellMeOrder':
        return cls(**json.loads(data))


class TellMeService:
    """
    The TELL ME Network Service

    Connects CRACKs across the HelixNETWORK.
    """

    def __init__(self, host: str = None):
        self.host = host or RABBITMQ_HOST
        self._connection = None
        self._channel = None

    def _get_connection(self):
        """Get or create RabbitMQ connection"""
        if self._connection is None or self._connection.is_closed:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            params = pika.ConnectionParameters(
                host=self.host,
                virtual_host=RABBITMQ_VHOST,
                credentials=credentials
            )
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()

            # Ensure exchange exists
            self._channel.exchange_declare(
                exchange=EXCHANGE_NAME,
                exchange_type='topic',
                durable=True
            )
        return self._channel

    def broadcast_need(self, shop_id: str, shop_name: str, product_query: str,
                       quantity: float, unit: str = "units",
                       urgency: str = "normal", notes: str = None) -> TellMeRequest:
        """
        CRACK broadcasts: "TELL ME - I need X"

        This goes to all connected shops in the network.
        """
        request = TellMeRequest.create(
            shop_id=shop_id,
            shop_name=shop_name,
            product_query=product_query,
            quantity=quantity,
            unit=unit,
            urgency=urgency,
            notes=notes
        )

        channel = self._get_connection()
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=f"tell_me.request.{shop_id}",
            body=request.to_json(),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent
                content_type='application/json'
            )
        )

        print(f"📢 TELL ME broadcast from {shop_name}: '{product_query}' x{quantity} {unit}")
        return request

    def respond_to_need(self, request_id: str, shop_id: str, shop_name: str,
                        product_sku: str, product_name: str, price_per_unit: float,
                        available_quantity: float, currency: str = "CHF",
                        lead_time: str = "1 day", notes: str = None) -> TellMeResponse:
        """
        CRACK responds: "I have what you need"
        """
        response = TellMeResponse.create(
            request_id=request_id,
            shop_id=shop_id,
            shop_name=shop_name,
            product_sku=product_sku,
            product_name=product_name,
            price_per_unit=price_per_unit,
            available_quantity=available_quantity,
            currency=currency,
            lead_time=lead_time,
            notes=notes
        )

        channel = self._get_connection()
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=f"tell_me.response.{shop_id}",
            body=response.to_json(),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )

        print(f"✋ Response from {shop_name}: {product_name} @ {currency} {price_per_unit}/{response.lead_time}")
        return response

    def place_order(self, request: TellMeRequest, response: TellMeResponse,
                    quantity: float) -> TellMeOrder:
        """
        CRACK accepts an offer: "I'll take it"
        """
        order = TellMeOrder.create(request, response, quantity)

        channel = self._get_connection()
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=f"tell_me.order.{response.shop_id}",
            body=order.to_json(),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )

        print(f"🤝 ORDER: {order.buyer_shop_name} → {order.seller_shop_name}")
        print(f"   {order.product_name} x{quantity} = {order.currency} {order.total_price}")
        return order

    def close(self):
        """Close connection"""
        if self._connection and not self._connection.is_closed:
            self._connection.close()


# Quick test function
def demo_tell_me_flow():
    """
    Demonstrate the TELL ME flow:

    1. BlowUp needs Purple Power base
    2. FourTwenty responds with offer
    3. BlowUp places order
    """
    print("\n" + "="*60)
    print("🌿 TELL ME Network Demo")
    print("="*60 + "\n")

    service = TellMeService(host="localhost")  # Use localhost for testing

    # Step 1: BlowUp broadcasts need
    print("STEP 1: BlowUp broadcasts need")
    print("-" * 40)
    request = service.broadcast_need(
        shop_id="blowup",
        shop_name="💨 BlowUp Littau",
        product_query="Purple Power base ingredient",
        quantity=5,
        unit="kg",
        urgency="normal",
        notes="For Sylvie's new batch - need by CW50"
    )
    print(f"   Request ID: {request.id[:8]}...")

    # Step 2: FourTwenty responds
    print("\nSTEP 2: FourTwenty responds")
    print("-" * 40)
    response = service.respond_to_need(
        request_id=request.id,
        shop_id="fourtwenty",
        shop_name="🌿 420 Wholesale",
        product_sku="SKU-4421",
        product_name="Purple Power Base Extract",
        price_per_unit=45.00,
        available_quantity=20,
        currency="CHF",
        lead_time="2 days",
        notes="Fresh batch, lab tested - see KB-030"
    )
    print(f"   Response ID: {response.id[:8]}...")

    # Step 3: BlowUp places order
    print("\nSTEP 3: BlowUp places order")
    print("-" * 40)
    order = service.place_order(request, response, quantity=5)
    print(f"   Order ID: {order.id[:8]}...")

    service.close()

    print("\n" + "="*60)
    print("✅ TELL ME Flow Complete - Share the JAM!")
    print("="*60 + "\n")

    return request, response, order


if __name__ == "__main__":
    demo_tell_me_flow()
