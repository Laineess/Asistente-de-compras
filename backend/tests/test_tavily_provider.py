from decimal import Decimal

import pytest

from app.models import Store
from app.providers.tavily_provider import TavilyProvider


class FakeTavilyClient:
    def __init__(self, results: list[dict]) -> None:
        self.results = results
        self.calls: list[dict] = []

    def search(self, **kwargs):
        self.calls.append(kwargs)
        return {"results": self.results}


def make_provider(results: list[dict]) -> tuple[TavilyProvider, FakeTavilyClient]:
    client = FakeTavilyClient(results)
    return TavilyProvider(Store.walmart, "clave", client=client), client


def test_search_normalizes_tavily_results_and_filters_noise() -> None:
    provider, client = make_provider(
        [
            {
                "url": "https://www.walmart.com.mx/ip/laptop-hp/123",
                "title": "Laptop HP 15 | Walmart México",
                "content": (
                    "Laptop HP con 8 GB RAM. Excelente rendimiento. "
                    "La batería dura todo el día. 4.5 de 5 estrellas. "
                    "Precio $12,999.00 MXN."
                ),
                "score": 0.9,
            },
            {
                "url": "https://www.walmart.com.mx/ip/laptop-generica/456",
                "title": "Todas las laptops | Walmart",
                "content": "Precio $9,999.00 MXN.",
                "score": 0.8,
            },
            {
                "url": "https://www.walmart.com.mx/ip/funda/789",
                "title": "Funda para laptop",
                "content": "Precio $499.00 MXN.",
                "score": 0.7,
            },
            {
                "url": "https://www.walmart.com.mx/ip/sin-precio/000",
                "title": "Laptop sin precio",
                "content": "Sin precio disponible.",
                "score": 0.6,
            },
            {
                "url": "https://www.walmart.com.mx/browse/laptops",
                "title": "Laptop HP 14",
                "content": "Precio $10,000.00 MXN.",
                "score": 0.5,
            },
        ]
    )

    options = provider.search("laptop", limit=3)

    assert len(options) == 1
    option = options[0]
    assert option.nombre == "Laptop HP 15"
    assert option.comercio is Store.walmart
    assert option.precio == Decimal("12999.00")
    assert option.calificacion == 4.5
    assert option.fuente == "tavily"
    assert option.url == "https://www.walmart.com.mx/ip/laptop-hp/123"
    assert option.resenas[0].texto == "La batería dura todo el día."
    assert option.descripcion == "La batería dura todo el día."

    assert client.calls[0]["include_domains"] == ["walmart.com.mx"]
    assert client.calls[0]["max_results"] == 12
    assert "Laptop HP 15" not in client.calls[0]["query"]


def test_search_respects_limit_and_returns_empty_without_results() -> None:
    results = [
        {
            "url": "https://www.walmart.com.mx/ip/laptop-a/1",
            "title": "Laptop A",
            "content": "Precio $10,000.00 MXN. Buena calidad y buen rendimiento.",
            "score": 0.9,
        },
        {
            "url": "https://www.walmart.com.mx/ip/laptop-b/2",
            "title": "Laptop B",
            "content": "Precio $11,000.00 MXN. Buena calidad y buen rendimiento.",
            "score": 0.8,
        },
    ]
    provider, _ = make_provider(results)

    assert len(provider.search("laptop", limit=1)) == 1

    empty_provider, _ = make_provider([])
    assert empty_provider.search("laptop") == []


def test_provider_requires_key_or_client() -> None:
    with pytest.raises(ValueError):
        TavilyProvider(Store.walmart, "")

    provider = TavilyProvider(Store.walmart, "", client=FakeTavilyClient([]))
    assert provider.store is Store.walmart


def test_provider_helpers() -> None:
    provider = TavilyProvider(Store.walmart, "clave", client=FakeTavilyClient([]))

    assert provider._is_product_url("https://www.walmart.com.mx/ip/laptop/1")
    assert not provider._is_product_url("https://www.walmart.com.mx/browse")
    assert provider._is_generic_title("Todas las laptops")
    assert not provider._is_generic_title("Laptop HP 15")
    assert provider._is_accessory_only("laptop", "Funda para laptop")
    assert not provider._is_accessory_only("funda para laptop", "Funda para laptop")
