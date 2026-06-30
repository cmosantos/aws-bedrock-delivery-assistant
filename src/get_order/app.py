import os
from decimal import Decimal
from typing import Any

import boto3

ORDERS_TABLE = os.environ["ORDERS_TABLE"]
table = boto3.resource("dynamodb").Table(ORDERS_TABLE)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    order_id = str(event.get("order_id", "")).strip().upper()
    if not order_id:
        return {
            "statusCode": 400,
            "body": {
                "intent": "ORDER_STATUS",
                "reply": "Informe o codigo do pedido no formato PED-XXXXXXXX.",
            },
        }

    response = table.get_item(Key={"order_id": order_id}, ConsistentRead=True)
    order = response.get("Item")
    if not order:
        return {
            "statusCode": 404,
            "body": {
                "intent": "ORDER_STATUS",
                "reply": f"Nao encontrei o pedido {order_id}.",
            },
        }

    user_id = str(event.get("user_id", "anonymous"))
    if order.get("user_id") not in (user_id, "anonymous") and user_id != "anonymous":
        return {
            "statusCode": 403,
            "body": {
                "intent": "ORDER_STATUS",
                "reply": "Esse pedido pertence a outro usuario.",
            },
        }

    safe_order = _json_safe(order)
    return {
        "statusCode": 200,
        "body": {
            "intent": "ORDER_STATUS",
            "reply": f"O pedido {order_id} esta com o status {order['status']}.",
            "order": safe_order,
        },
    }
