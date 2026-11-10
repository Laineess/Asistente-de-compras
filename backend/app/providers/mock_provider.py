from __future__ import annotations

import hashlib
import json
import unicodedata
from decimal import Decimal
from pathlib import Path

from app.models import ProductOption, ReviewSnippet, Store
from app.providers.base import StoreProvider

MOCK_DIR = Path(__file__).resolve().parents[2] / "data" / "mock"


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.lower().split())


class MockProvider(StoreProvider):
    def __init__(self, store: Store, data_dir: Path | None = None) -> None:
        super().__init__(store)
        self._data_dir = data_dir or MOCK_DIR
        self._products = self._load_products()

    def _load_products(self) -> list[dict]:
        path = self._data_dir / f"{self.store.value}.json"
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("productos", [])

    def search(self, query: str, limit: int = 3) -> list[ProductOption]:
        tokens = [token for token in normalize_text(query).split() if len(token) > 1]
        scored: list[tuple[int, dict]] = []

        for product in self._products:
            haystack = normalize_text(
                " ".join(
                    [
                        product.get("nombre", ""),
                        product.get("descripcion", ""),
                        " ".join(product.get("tags", [])),
                    ]
                )
            )
            score = sum(1 for token in tokens if token in haystack)
            if score:
                scored.append((score, product))

        if scored:
            scored.sort(key=lambda item: (-item[0], float(item[1].get("precio", 0))))
            return [
                self._to_option(product)
                for _, product in scored[:limit]
            ]

        return self._synthetic_options(query, limit)

    def _to_option(self, product: dict) -> ProductOption:
        resenas = [
            ReviewSnippet(
                autor=review.get("autor"),
                texto=review["texto"],
                calificacion=review.get("calificacion"),
            )
            for review in product.get("resenas", [])
        ]
        return ProductOption(
            nombre=product["nombre"],
            comercio=self.store,
            precio=Decimal(str(product["precio"])),
            moneda=product.get("moneda", "MXN"),
            url=product.get("url"),
            descripcion=product.get("descripcion"),
            calificacion=product.get("calificacion"),
            resenas=resenas,
            fuente="mock",
        )

    def _synthetic_options(self, query: str, limit: int) -> list[ProductOption]:
        normalized = normalize_text(query)
        digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()
        base = 1500 + (int(digest[:8], 16) % 8000)
        options: list[ProductOption] = []

        for index in range(limit):
            precio = Decimal(str(base + index * 350))
            calificacion = round(min(5.0, 4.0 + index * 0.15), 1)
            options.append(
                ProductOption(
                    nombre=f"{query.strip().title()} — opción {index + 1}",
                    comercio=self.store,
                    precio=precio,
                    moneda="MXN",
                    url=None,
                    descripcion=(
                        "Resultado simulado generado para la demo porque no hubo "
                        "coincidencias en el catálogo local."
                    ),
                    calificacion=calificacion,
                    resenas=[
                        ReviewSnippet(
                            autor=f"Comprador {index + 1}",
                            texto=(
                                f"Opinión simulada sobre {query.strip()}: buena relación "
                                "calidad-precio para la demostración."
                            ),
                            calificacion=4.0,
                        ),
                        ReviewSnippet(
                            autor=f"Comprador {index + 2}",
                            texto=(
                                "Dato de ejemplo; en producción provendría de reseñas reales "
                                "de la tienda."
                            ),
                            calificacion=4.5,
                        ),
                        ReviewSnippet(
                            autor=f"Comprador {index + 3}",
                            texto=(
                                "Reseña simulada con fines académicos para completar el "
                                "mínimo de tres opiniones."
                            ),
                            calificacion=3.5,
                        ),
                    ],
                    fuente="mock",
                )
            )

        return options
