import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

ORDERS_TABLE = os.getenv("ORDERS_TABLE", "delivery-assistant-orders-local")
LOCAL_MODE = os.getenv("LOCAL_MODE", "false").lower() == "true"
table = boto3.resource("dynamodb").Table(ORDERS_TABLE)


def _money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    requested_items = event.get("requested_items", [])
    menu = {item["id"]: item for item in event.get("menu", [])}

    if not requested_items:
        return {
            "statusCode": 400,
            "body": {
                "intent": "CREATE_ORDER",
                "reply": "Nao identifiquei itens suficientes para criar o pedido.",
            },
        }

    order_items: list[dict[str, Any]] = []
    total = Decimal("0.00")

    for requested in requested_items:
        item_id = str(requested.get("item_id", "")).upper()
        menu_item = menu.get(item_id)
        if not menu_item:
            return {
                "statusCode": 400,
                "body": {
                    "intent": "CREATE_ORDER",
                    "reply": f"O item {item_id or 'informado'} nao esta disponivel no cardapio.",
                },
            }

        quantity = max(1, min(10, int(requested.get("quantity", 1))))
        unit_price = _money(menu_item["price"])
        line_total = unit_price * quantity
        total += line_total
        order_items.append(
            {
                "item_id": item_id,
                "name": menu_item["name"],
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
                "notes": str(requested.get("notes", ""))[:200],
            }
        )

    now = datetime.now(timezone.utc)
    order_id = f"PED-{uuid.uuid4().hex[:8].upper()}"
    order = {
        "order_id": order_id,
        "user_id": str(event.get("user_id", "anonymous")),
        "session_id": str(event.get("session_id", "")),
        "status": "RECEIVED",
        "items": order_items,
        "total": total,
        "currency": "BRL",
        "created_at": now.isoformat(),
        "estimated_delivery_minutes": 40,
        "expires_at": int((now + timedelta(days=30)).timestamp()),
    }

    if not LOCAL_MODE:
        table.put_item(
            Item=order,
            ConditionExpression="attribute_not_exists(order_id)",
        )
    else:
        logger.info("LOCAL_MODE enabled. Order was not persisted: %s", order_id)

    return {
        "statusCode": 201,
        "body": {
            "intent": "CREATE_ORDER",
            "reply": (
                f"Pedido {order_id} recebido com sucesso. "
                f"Total: R$ {total:.2f}. Previsao aproximada: 40 minutos."
            ),
            "order": order,
        },
    }
