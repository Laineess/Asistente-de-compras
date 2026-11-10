from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote_plus

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MOCK_DIR = PROJECT_ROOT / "backend" / "data" / "mock"

STORES = ["walmart", "costco", "sams"]

SEARCH_URLS = {
    "walmart": "https://www.walmart.com.mx/search?q={query}",
    "costco": "https://www.costco.com.mx/search?keyword={query}",
    "sams": "https://www.sams.com.mx/search?q={query}",
}

BASE_PRODUCTS = [
    {
        "nombre": "Laptop Lenovo IdeaPad 3 15.6\" Ryzen 5 8GB 512GB",
        "descripcion": (
            "Laptop para estudio y trabajo con AMD Ryzen 5, 8 GB de RAM y SSD de "
            "512 GB. Pantalla Full HD de 15.6 pulgadas."
        ),
        "tags": ["laptop", "computadora", "lenovo", "ideapad", "ryzen", "portatil"],
        "precios": {"walmart": 12999.00, "costco": 12499.00, "sams": 12799.00},
        "calificaciones": {"walmart": 4.3, "costco": 4.4, "sams": 4.2},
        "resenas": [
            {
                "autor": "Ana R.",
                "texto": (
                    "Buena laptop para la escuela; arranca rápido y la batería "
                    "aguanta la jornada."
                ),
                "calificacion": 4.5,
            },
            {
                "autor": "Luis M.",
                "texto": (
                    "La pantalla se ve bien, aunque el ventilador suena en tareas "
                    "pesadas."
                ),
                "calificacion": 4.0,
            },
            {
                "autor": "María G.",
                "texto": (
                    "Relación calidad-precio excelente para ofimática y clases en línea."
                ),
                "calificacion": 4.5,
            },
        ],
    },
    {
        "nombre": "Laptop HP Pavilion 15 Intel Core i5 8GB 512GB",
        "descripcion": (
            "Laptop HP con Intel Core i5, 8 GB de RAM, SSD de 512 GB y pantalla "
            "de 15.6 pulgadas."
        ),
        "tags": ["laptop", "computadora", "hp", "pavilion", "intel", "portatil"],
        "precios": {"walmart": 14999.00, "costco": 14499.00, "sams": 14799.00},
        "calificaciones": {"walmart": 4.4, "costco": 4.5, "sams": 4.3},
        "resenas": [
            {
                "autor": "Carlos P.",
                "texto": (
                    "Muy buena para trabajo; el teclado es cómodo y tiene buena autonomía."
                ),
                "calificacion": 4.5,
            },
            {
                "autor": "Sofía L.",
                "texto": (
                    "El diseño es elegante, aunque pesa un poco para llevarla diario."
                ),
                "calificacion": 4.0,
            },
            {
                "autor": "Diego H.",
                "texto": "Rápida para multitarea y videollamadas.",
                "calificacion": 4.5,
            },
        ],
    },
    {
        "nombre": "Laptop ASUS Vivobook 15 Intel Core i3 8GB 256GB",
        "descripcion": (
            "Laptop económica para tareas básicas con Intel Core i3, 8 GB de RAM "
            "y SSD de 256 GB."
        ),
        "tags": ["laptop", "computadora", "asus", "vivobook", "intel", "portatil"],
        "precios": {"walmart": 9999.00, "costco": 9499.00, "sams": 9799.00},
        "calificaciones": {"walmart": 4.0, "costco": 4.1, "sams": 3.9},
        "resenas": [
            {
                "autor": "Paola V.",
                "texto": "Cumple para la escuela y navegación; no esperes gaming.",
                "calificacion": 4.0,
            },
            {
                "autor": "Jorge T.",
                "texto": (
                    "Buena por el precio, aunque el almacenamiento se llena rápido."
                ),
                "calificacion": 3.5,
            },
            {
                "autor": "Elena C.",
                "texto": "Ligera y con buen teclado para escribir.",
                "calificacion": 4.0,
            },
        ],
    },
    {
        "nombre": "Smartphone Samsung Galaxy A55 5G 128GB",
        "descripcion": (
            "Teléfono Samsung con pantalla AMOLED, cámara de 50 MP y conectividad 5G."
        ),
        "tags": ["smartphone", "celular", "telefono", "samsung", "galaxy", "a55", "5g"],
        "precios": {"walmart": 8499.00, "costco": 8299.00, "sams": 8399.00},
        "calificaciones": {"walmart": 4.5, "costco": 4.6, "sams": 4.4},
        "resenas": [
            {
                "autor": "Fernanda S.",
                "texto": "Excelente cámara y pantalla; la batería dura todo el día.",
                "calificacion": 4.5,
            },
            {
                "autor": "Ricardo N.",
                "texto": (
                    "Buen rendimiento para el precio, aunque incluye cargador lento."
                ),
                "calificacion": 4.0,
            },
            {
                "autor": "Valeria D.",
                "texto": "Se siente premium y la pantalla se ve muy bien.",
                "calificacion": 4.5,
            },
        ],
    },
    {
        "nombre": "Audífonos Sony WH-CH720N Bluetooth con cancelación de ruido",
        "descripcion": (
            "Audífonos inalámbricos con cancelación de ruido, hasta 35 horas de "
            "batería y micrófono integrado."
        ),
        "tags": [
            "audifonos",
            "auriculares",
            "sony",
            "bluetooth",
            "cancelacion",
            "ruido",
        ],
        "precios": {"walmart": 2299.00, "costco": 2199.00, "sams": 2249.00},
        "calificaciones": {"walmart": 4.4, "costco": 4.5, "sams": 4.3},
        "resenas": [
            {
                "autor": "Andrés F.",
                "texto": "La cancelación de ruido funciona bien para el precio.",
                "calificacion": 4.5,
            },
            {
                "autor": "Lucía B.",
                "texto": "Cómodos por horas y con buena batería.",
                "calificacion": 4.0,
            },
            {
                "autor": "Tomás R.",
                "texto": (
                    "El sonido es equilibrado, aunque los graves podrían ser más potentes."
                ),
                "calificacion": 4.0,
            },
        ],
    },
    {
        "nombre": "Televisor LG 55\" 4K UHD Smart TV",
        "descripcion": (
            "Televisor LG de 55 pulgadas, resolución 4K, sistema webOS y control por voz."
        ),
        "tags": ["televisor", "tv", "lg", "4k", "smart", "pantalla"],
        "precios": {"walmart": 9999.00, "costco": 9499.00, "sams": 9799.00},
        "calificaciones": {"walmart": 4.6, "costco": 4.7, "sams": 4.5},
        "resenas": [
            {
                "autor": "Gabriela M.",
                "texto": "Imagen muy nítida y el sistema es fácil de usar.",
                "calificacion": 4.5,
            },
            {
                "autor": "Héctor J.",
                "texto": "Buena para streaming y consolas; el sonido es aceptable.",
                "calificacion": 4.0,
            },
            {
                "autor": "Patricia O.",
                "texto": "Excelente relación calidad-precio en 55 pulgadas.",
                "calificacion": 5.0,
            },
        ],
    },
]


def build_store_payload(store: str) -> dict:
    productos = []
    for product in BASE_PRODUCTS:
        productos.append(
            {
                "nombre": product["nombre"],
                "precio": product["precios"][store],
                "moneda": "MXN",
                "url": SEARCH_URLS[store].format(
                    query=quote_plus(product["nombre"])
                ),
                "descripcion": product["descripcion"],
                "calificacion": product["calificaciones"][store],
                "tags": product["tags"],
                "resenas": product["resenas"],
            }
        )
    return {"tienda": store, "productos": productos}


def main() -> None:
    MOCK_DIR.mkdir(parents=True, exist_ok=True)
    for store in STORES:
        path = MOCK_DIR / f"{store}.json"
        payload = build_store_payload(store)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Generado: {path}")


if __name__ == "__main__":
    main()
