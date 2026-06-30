import json
import logging
import os
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

stepfunctions = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json; charset=utf-8",
            "access-control-allow-origin": "*",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    raw_body = event.get("body")
    if raw_body is None:
        return event
    if isinstance(raw_body, dict):
        return raw_body
    if not isinstance(raw_body, str) or not raw_body.strip():
        return {}
    return json.loads(raw_body)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    logger.info("Request received")

    try:
        payload = _parse_body(event)
    except json.JSONDecodeError:
        return _response(400, {"reply": "O corpo da requisicao precisa ser um JSON valido."})

    request_context = event.get("requestContext", {})
    payload["source_ip"] = request_context.get("http", {}).get("sourceIp", "unknown")

    try:
        execution = stepfunctions.start_sync_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(payload, ensure_ascii=False),
        )
    except Exception:
        logger.exception("Could not start Step Functions execution")
        return _response(503, {"reply": "O assistente esta temporariamente indisponivel."})

    if execution.get("status") != "SUCCEEDED":
        logger.error(
            "Workflow failed: status=%s error=%s cause=%s",
            execution.get("status"),
            execution.get("error"),
            execution.get("cause"),
        )
        return _response(503, {"reply": "Nao foi possivel concluir o atendimento agora."})

    output = json.loads(execution.get("output", "{}"))
    status_code = int(output.get("statusCode", 200))
    body = output.get("body", output)

    return _response(status_code, body)
