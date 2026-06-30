from typing import Any

MENU = [
    {
        "id": "BURGER_CLASSIC",
        "name": "Burger Classic",
        "description": "Pao brioche, hamburguer bovino, queijo, alface, tomate e molho da casa.",
        "category": "hamburguer",
        "price": 29.90,
    },
    {
        "id": "BURGER_VEGGIE",
        "name": "Burger Veggie",
        "description": "Pao brioche, burger vegetal, queijo, alface, tomate e molho especial.",
        "category": "hamburguer",
        "price": 31.90,
    },
    {
        "id": "PIZZA_CALABRESA",
        "name": "Pizza de Calabresa",
        "description": "Pizza media com molho de tomate, mucarela, calabresa e cebola.",
        "category": "pizza",
        "price": 44.90,
    },
    {
        "id": "PIZZA_MARGHERITA",
        "name": "Pizza Margherita",
        "description": "Pizza media com molho de tomate, mucarela, tomate e manjericao.",
        "category": "pizza",
        "price": 42.90,
    },
    {
        "id": "FRIES",
        "name": "Batata Frita",
        "description": "Porcao individual de batatas crocantes.",
        "category": "acompanhamento",
        "price": 14.90,
    },
    {
        "id": "SODA_COLA",
        "name": "Refrigerante Cola",
        "description": "Lata de 350 ml.",
        "category": "bebida",
        "price": 7.00,
    },
    {
        "id": "JUICE_ORANGE",
        "name": "Suco de Laranja",
        "description": "Suco natural de laranja, 400 ml.",
        "category": "bebida",
        "price": 10.90,
    },
]


def lambda_handler(_event: dict[str, Any], _context: Any) -> dict[str, Any]:
    return {
        "restaurant": "Cloud Burger",
        "currency": "BRL",
        "delivery_time_minutes": {"min": 30, "max": 50},
        "items": MENU,
    }
