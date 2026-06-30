import importlib.util
import os
import unittest
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
os.environ["USE_MOCK_BEDROCK"] = "true"
os.environ["LOCAL_MODE"] = "true"
os.environ.setdefault("ORDERS_TABLE", "delivery-assistant-orders-local")


def load_module(name: str, relative_path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate = load_module("test_validate_request", "src/validate_request/app.py")
get_menu = load_module("test_get_menu", "src/get_menu/app.py")
assistant = load_module("test_bedrock_assistant", "src/bedrock_assistant/app.py")
create_order = load_module("test_create_order", "src/create_order/app.py")


class HandlerTests(unittest.TestCase):
    def test_validation_rejects_empty_message(self) -> None:
        result = validate.lambda_handler({"message": ""}, None)
        self.assertFalse(result["valid"])
        self.assertTrue(result["errors"])

    def test_validation_creates_session(self) -> None:
        result = validate.lambda_handler({"message": "Ola"}, None)
        self.assertTrue(result["valid"])
        self.assertTrue(result["session_id"])

    def test_menu_has_unique_ids(self) -> None:
        menu = get_menu.lambda_handler({}, None)["items"]
        ids = [item["id"] for item in menu]
        self.assertEqual(len(ids), len(set(ids)))

    def test_mock_assistant_identifies_order(self) -> None:
        menu = get_menu.lambda_handler({}, None)["items"]
        result = assistant.lambda_handler(
            {"message": "Quero 2 Burger Classic", "menu": menu},
            None,
        )
        self.assertEqual(result["intent"], "CREATE_ORDER")
        self.assertEqual(result["items"][0]["item_id"], "BURGER_CLASSIC")

    def test_create_order_calculates_total(self) -> None:
        menu = get_menu.lambda_handler({}, None)["items"]
        result = create_order.lambda_handler(
            {
                "user_id": "test-user",
                "session_id": "test-session",
                "requested_items": [
                    {"item_id": "BURGER_CLASSIC", "quantity": 2, "notes": ""}
                ],
                "menu": menu,
            },
            None,
        )
        self.assertEqual(result["statusCode"], 201)
        self.assertEqual(str(result["body"]["order"]["total"]), "59.80")

    def test_create_order_rejects_unknown_item(self) -> None:
        menu = get_menu.lambda_handler({}, None)["items"]
        result = create_order.lambda_handler(
            {
                "requested_items": [{"item_id": "INVENTED", "quantity": 1}],
                "menu": menu,
            },
            None,
        )
        self.assertEqual(result["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()
