import uuid
from typing import Any

MAX_MESSAGE_LENGTH = 1000


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    message = event.get("message", "")
    errors: list[str] = []

    if not isinstance(message, str) or not message.strip():
        errors.append("O campo 'message' e obrigatorio.")
    elif len(message.strip()) > MAX_MESSAGE_LENGTH:
        errors.append(f"A mensagem deve ter no maximo {MAX_MESSAGE_LENGTH} caracteres.")

    user_id = event.get("user_id", "anonymous")
    if not isinstance(user_id, str) or not user_id.strip():
        user_id = "anonymous"

    session_id = event.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        session_id = str(uuid.uuid4())

    if errors:
        return {
            "valid": False,
            "errors": errors,
            "reply": "Revise os dados enviados e tente novamente.",
        }

    return {
        "valid": True,
        "message": message.strip(),
        "user_id": user_id.strip()[:120],
        "session_id": session_id.strip()[:120],
        "locale": str(event.get("locale", "pt-BR"))[:20],
        "source_ip": str(event.get("source_ip", "unknown"))[:64],
    }
