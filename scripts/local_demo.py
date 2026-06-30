#!/usr/bin/env python3
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
os.environ["USE_MOCK_BEDROCK"] = "true"
os.environ["LOCAL_MODE"] = "true"
os.environ.setdefault("ORDERS_TABLE", "delivery-assistant-orders-local")


def load_module(name: str, relative_path: str) -> ModuleType:
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    validate = load_module("validate_request", "src/validate_request/app.py")
    get_menu = load_module("get_menu", "src/get_menu/app.py")
    assistant = load_module("bedrock_assistant", "src/bedrock_assistant/app.py")
    create_order = load_module("create_order", "src/create_order/app.py")

    request = {
        "user_id": "cliente-local",
        "message": "Quero 2 Burger Classic e uma batata frita",
    }

    validation = validate.lambda_handler(request, None)
    if not validation["valid"]:
        print(json.dumps(validation, ensure_ascii=False, indent=2))
        return

    menu = get_menu.lambda_handler(validation, None)
    interpretation = assistant.lambda_handler(
        {
            "message": validation["message"],
            "user_id": validation["user_id"],
            "session_id": validation["session_id"],
            "menu": menu["items"],
        },
        None,
    )

    if interpretation["intent"] != "CREATE_ORDER":
        print(json.dumps(interpretation, ensure_ascii=False, indent=2))
        return

    result = create_order.lambda_handler(
        {
            "user_id": validation["user_id"],
            "session_id": validation["session_id"],
            "requested_items": interpretation["items"],
            "menu": menu["items"],
        },
        None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
