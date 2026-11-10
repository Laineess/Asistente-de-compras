from __future__ import annotations

import unicodedata
from collections.abc import Mapping

from app.models import ProductOption, ProductQuery, SearchResult, Store
from app.providers.base import StoreProvider
from app.providers.mock_provider import MockProvider


def normalize_key(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.lower().split())


class ProductSearchService:
    def __init__(
        self,
        providers: Mapping[Store, StoreProvider] | None = None,
        fallback_providers: Mapping[Store, StoreProvider] | None = None,
    ) -> None:
        self._providers = dict(providers or {})
        self._fallback = dict(fallback_providers or {})

    def search(self, query: ProductQuery) -> SearchResult:
        opciones: list[ProductOption] = []
        errores: list[str] = []
        tiendas_con_mock: list[Store] = []

        for store in query.tiendas:
            provider = self._providers.get(store)
            store_options: list[ProductOption] = []

            if provider is not None:
                try:
                    store_options = provider.search(
                        query.producto,
                        limit=query.limite_por_tienda,
                    )
                except Exception as exc:
                    errores.append(f"{store.display_name}: {exc}")

            if not store_options:
                fallback = self._fallback.get(store) or MockProvider(store)
                store_options = fallback.search(
                    query.producto,
                    limit=query.limite_por_tienda,
                )
                tiendas_con_mock.append(store)
            elif len(store_options) < query.limite_por_tienda:
                fallback = self._fallback.get(store) or MockProvider(store)
                existing = {normalize_key(option.nombre) for option in store_options}
                extra = [
                    option
                    for option in fallback.search(
                        query.producto,
                        limit=query.limite_por_tienda,
                    )
                    if normalize_key(option.nombre) not in existing
                ]
                if extra:
                    missing = query.limite_por_tienda - len(store_options)
                    store_options.extend(extra[:missing])
                    tiendas_con_mock.append(store)

            opciones.extend(store_options)

        opciones = self._dedupe(opciones)
        opciones.sort(key=lambda option: (option.precio, option.comercio.value))

        return SearchResult(
            opciones=opciones,
            errores=errores,
            tiendas_con_mock=tiendas_con_mock,
        )

    @staticmethod
    def _dedupe(options: list[ProductOption]) -> list[ProductOption]:
        seen: dict[tuple[str, str], ProductOption] = {}
        for option in options:
            key = (normalize_key(option.nombre), option.comercio.value)
            current = seen.get(key)
            if current is None or len(option.resenas) > len(current.resenas):
                seen[key] = option
        return list(seen.values())
