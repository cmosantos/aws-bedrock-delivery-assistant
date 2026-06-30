import json
import logging
import os
import re
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
USE_MOCK_BEDROCK = os.getenv("USE_MOCK_BEDROCK", "false").lower() == "true"
VALID_INTENTS = {"BROWSE_MENU", "CREATE_ORDER", "ORDER_STATUS", "HELP"}

bedrock_runtime = boto3.client("bedrock-runtime")

SYSTEM_PROMPT = """
Voce e o assistente virtual da lanchonete Cloud Burger.
Responda sempre em portugues do Brasil, de forma simpatica, objetiva e profissional.
Use exclusivamente os itens fornecidos no cardapio. Nunca invente produtos, precos ou disponibilidade.
Sua tarefa e identificar uma unica intencao:
- BROWSE_MENU: cliente quer conhecer cardapio, precos ou recomendacoes.
- CREATE_ORDER: cliente informou itens e quantidades suficientes para criar um pedido.
- ORDER_STATUS: cliente quer consultar um pedido e informou ou mencionou o codigo.
- HELP: saudacao, duvida geral ou mensagem sem dados suficientes.

Retorne SOMENTE JSON valido, sem markdown, no formato:
{
  "intent": "BROWSE_MENU|CREATE_ORDER|ORDER_STATUS|HELP",
  "reply": "resposta curta para o cliente",
  "items": [{"item_id": "ID_DO_CARDAPIO", "quantity": 1, "notes": "opcional"}],
  "order_id": "PED-XXXXXXXX ou string vazia",
  "suggestions": ["sugestao 1", "sugestao 2"]
}

Regras importantes:
- Nunca confirme preco total; o sistema calculara o valor com seguranca.
- Use apenas item_id existente no cardapio.
- Quantidade deve ser inteiro entre 1 e 10.
- Se faltar quantidade ou o item for ambiguo, use HELP e faca uma pergunta objetiva.
- Para ORDER_STATUS, extraia o codigo PED-XXXXXXXX quando existir.
""".strip()


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _normalize(result: dict[str, Any]) -> dict[str, Any]:
    intent = str(result.get("intent", "HELP")).upper()
    if intent not in VALID_INTENTS:
        intent = "HELP"

    normalized_items: list[dict[str, Any]] = []
    for item in result.get("items", []) if isinstance(result.get("items"), list) else []:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("item_id", "")).strip().upper()
        try:
            quantity = max(1, min(10, int(item.get("quantity", 1))))
        except (TypeError, ValueError):
            quantity = 1
        if item_id:
            normalized_items.append(
                {
                    "item_id": item_id,
                    "quantity": quantity,
                    "notes": str(item.get("notes", "")).strip()[:200],
                }
            )

    suggestions = result.get("suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = []

    return {
        "intent": intent,
        "reply": str(result.get("reply", "Como posso ajudar com seu pedido?")).strip()[:800],
        "items": normalized_items,
        "order_id": str(result.get("order_id", "")).strip().upper()[:40],
        "suggestions": [str(value)[:100] for value in suggestions[:3]],
    }


def _quantity_near_alias(message: str, alias: str) -> int:
    number_words = {
        "um": 1,
        "uma": 1,
        "dois": 2,
        "duas": 2,
        "tres": 3,
        "quatro": 4,
        "cinco": 5,
    }
    pattern = rf"(?:\b([1-9]|10)\b|\b({'|'.join(number_words)})\b)?\s*(?:unidades?\s+de\s+)?{re.escape(alias)}"
    match = re.search(pattern, message, flags=re.IGNORECASE)
    if not match:
        return 1
    if match.group(1):
        return int(match.group(1))
    if match.group(2):
        return number_words[match.group(2).lower()]
    return 1


def _mock_response(message: str, menu: list[dict[str, Any]]) -> dict[str, Any]:
    lower = message.lower()
    order_match = re.search(r"ped-[a-z0-9]{8}", lower, flags=re.IGNORECASE)
    if "status" in lower or ("pedido" in lower and order_match):
        return {
            "intent": "ORDER_STATUS",
            "reply": "Vou consultar esse pedido para voce.",
            "items": [],
            "order_id": order_match.group(0).upper() if order_match else "",
            "suggestions": [],
        }

    aliases = {
        "BURGER_CLASSIC": ["burger classic", "classic"],
        "BURGER_VEGGIE": ["burger veggie", "veggie", "burger vegetal"],
        "PIZZA_CALABRESA": ["pizza de calabresa", "pizza calabresa", "calabresa"],
        "PIZZA_MARGHERITA": ["pizza margherita", "margherita"],
        "FRIES": ["batata frita", "batata"],
        "SODA_COLA": ["refrigerante cola", "refrigerante"],
        "JUICE_ORANGE": ["suco de laranja", "suco"],
    }

    selected: list[dict[str, Any]] = []
    for item in menu:
        for alias in aliases.get(str(item.get("id")), []):
            if alias in lower:
                selected.append(
                    {
                        "item_id": item["id"],
                        "quantity": _quantity_near_alias(lower, alias),
                        "notes": "",
                    }
                )
                break

    if selected and any(word in lower for word in ("quero", "pedir", "pedido", "manda")):
        return {
            "intent": "CREATE_ORDER",
            "reply": "Perfeito. Vou validar os itens e registrar seu pedido.",
            "items": selected,
            "order_id": "",
            "suggestions": [],
        }

    if any(word in lower for word in ("cardapio", "menu", "preco", "opcoes")):
        names = ", ".join(item["name"] for item in menu[:4])
        return {
            "intent": "BROWSE_MENU",
            "reply": f"Temos estas opcoes em destaque: {names}.",
            "items": [],
            "order_id": "",
            "suggestions": ["Quero uma pizza", "Quero um hamburguer"],
        }

    return {
        "intent": "HELP",
        "reply": "Ola! Posso mostrar o cardapio, criar um pedido ou consultar um codigo de pedido.",
        "items": [],
        "order_id": "",
        "suggestions": ["Mostrar cardapio", "Consultar pedido"],
    }


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    message = str(event.get("message", "")).strip()
    menu = event.get("menu", [])

    if USE_MOCK_BEDROCK:
        return _normalize(_mock_response(message, menu))

    user_payload = {
        "mensagem_cliente": message,
        "cardapio": menu,
        "session_id": event.get("session_id"),
    }

    try:
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": json.dumps(
                                user_payload,
                                ensure_ascii=False,
                                separators=(",", ":"),
                            )
                        }
                    ],
                }
            ],
            inferenceConfig={
                "maxTokens": 700,
                "temperature": 0.1,
                "topP": 0.9,
            },
        )
        text = response["output"]["message"]["content"][0]["text"]
        return _normalize(_extract_json(text))
    except Exception:
        logger.exception("Bedrock inference failed for model %s", MODEL_ID)
        raise
