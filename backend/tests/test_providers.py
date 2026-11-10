from decimal import Decimal

from app.models import ProductQuery, Store
from app.providers.base import StoreProvider
from app.providers.mock_provider import MockProvider
from app.providers.service import ProductSearchService
from app.providers.tavily_provider import (
    clean_product_title,
    extract_price,
    extract_rating,
    extract_reviews,
)


class FailingProvider(StoreProvider):
    def __init__(self) -> None:
        super().__init__(Store.walmart)

    def search(self, query: str, limit: int = 3):
        raise RuntimeError("fuente caida")


def test_mock_provider_returns_catalog_matches() -> None:
    provider = MockProvider(Store.walmart)
    options = provider.search("laptop", limit=3)
    assert len(options) == 3
    assert all(option.comercio is Store.walmart for option in options)
    assert all(option.fuente == "mock" for option in options)
    assert all(len(option.resenas) >= 3 for option in options)


def test_mock_provider_generates_synthetic_options_for_unknown_query() -> None:
    provider = MockProvider(Store.costco)
    options = provider.search("producto inexistente xyz", limit=2)
    assert len(options) == 2
    assert all(
        "producto inexistente xyz" in option.nombre.lower() for option in options
    )
    assert all(len(option.resenas) >= 3 for option in options)


def test_service_falls_back_to_mock_when_provider_fails() -> None:
    service = ProductSearchService(
        providers={Store.walmart: FailingProvider()},
        fallback_providers={Store.walmart: MockProvider(Store.walmart)},
    )
    result = service.search(
        ProductQuery(producto="laptop", tiendas=[Store.walmart])
    )
    assert result.opciones
    assert result.tiendas_con_mock == [Store.walmart]
    assert result.errores
    assert all(option.comercio is Store.walmart for option in result.opciones)


def test_service_deduplicates_and_sorts_by_price() -> None:
    provider = MockProvider(Store.walmart)
    service = ProductSearchService(
        providers={Store.walmart: provider},
        fallback_providers={Store.walmart: provider},
    )
    result = service.search(
        ProductQuery(
            producto="laptop",
            tiendas=[Store.walmart],
            limite_por_tienda=5,
        )
    )
    precios = [option.precio for option in result.opciones]
    assert precios == sorted(precios)
    assert len(result.opciones) == len({option.nombre for option in result.opciones})


def test_extract_price() -> None:
    assert extract_price("Precio especial $12,999.00 MXN") == Decimal("12999.00")
    assert extract_price("sin precio") is None


def test_extract_rating_and_reviews() -> None:
    text = (
        "Muy buen producto. La batería dura todo el día. "
        "El teclado es cómodo. 4.5 de 5 estrellas."
    )
    assert extract_rating(text) == 4.5
    reviews = extract_reviews(text)
    assert 1 <= len(reviews) <= 3


def test_clean_product_title_removes_store_suffix() -> None:
    title = 'Apple MacBook Air 13" M5 16GB 512GB SSD | Costco México | Costco'
    assert clean_product_title(title) == 'Apple MacBook Air 13" M5 16GB 512GB SSD'
