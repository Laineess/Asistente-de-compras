from decimal import Decimal

import pytest

from app.models import Store
from app.providers.tavily_provider import (
    TavilyProvider,
    extract_price,
    is_relevant,
    title_from_url,
)


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
    assert provider._is_accessory_only("vino", "Cava de Vinos 150 Botellas")
    assert not provider._is_accessory_only("cava de vinos", "Cava de Vinos 150 Botellas")


def test_is_relevant_rejects_unrelated_products() -> None:
    assert is_relevant(
        "laptop",
        "Laptop HP 15",
        "https://www.walmart.com.mx/ip/laptop-hp/123",
    )
    assert is_relevant(
        "laptop",
        'Apple MacBook Air 13" M5',
        "https://www.costco.com.mx/Electronicos/Apple/Mac/Apple-MacBook-Air/p/1",
    )
    assert not is_relevant(
        "laptop",
        'Samsung Pantalla 55" QLED',
        "https://www.costco.com.mx/Electronicos/Pantallas/p/2",
    )
    assert not is_relevant(
        "laptop",
        "Buck Shack Vino Tinto 750 ml",
        "https://www.costco.com.mx/Vinos/Vino-Tinto/p/3",
    )
    assert not is_relevant(
        "botellas de vino",
        "Audífonos Bluetooth",
        "https://www.costco.com.mx/Electronicos/Audifonos/p/4",
    )


def test_search_filters_unrelated_products() -> None:
    provider, _ = make_provider(
        [
            {
                "url": "https://www.walmart.com.mx/ip/laptop-hp/1",
                "title": "Laptop HP 15",
                "content": "Precio $12,999.00 MXN.",
                "score": 0.9,
            },
            {
                "url": "https://www.walmart.com.mx/ip/pantalla/2",
                "title": 'Samsung Pantalla 55" QLED',
                "content": "Precio $16,999.00 MXN.",
                "score": 0.8,
            },
            {
                "url": "https://www.walmart.com.mx/ip/vino/3",
                "title": "Vino Tinto 750 ml",
                "content": "Precio $599.00 MXN.",
                "score": 0.7,
            },
            {
                "url": "https://www.walmart.com.mx/ip/macbook/4",
                "title": 'Apple MacBook Air 13" M5',
                "content": "Precio $18,999.00 MXN.",
                "score": 0.6,
            },
        ]
    )

    options = provider.search("laptop", limit=10)

    assert [option.nombre for option in options] == [
        "Laptop HP 15",
        'Apple MacBook Air 13" M5',
    ]


def test_search_replaces_unhelpful_title_with_url_slug() -> None:
    provider, _ = make_provider(
        [
            {
                "url": "https://www.walmart.com.mx/ip/"
                "ASUS-ProArt-P16-Laptop-16-3K-OLED/0001",
                "title": "Creador de contenido, Diseño",
                "content": "Precio actual $62,999.00 MXN.",
                "score": 0.9,
            }
        ]
    )

    options = provider.search("laptop", limit=3)

    assert len(options) == 1
    assert options[0].nombre == "ASUS ProArt P16 Laptop 16 3K OLED"


def test_extract_price_prefers_product_price_labels() -> None:
    assert extract_price("Precio original $2,199.00") == Decimal("2199.00")
    assert extract_price(
        "Precio original $599.00. Ahorro - $119.80. Precio. $479.20."
    ) == Decimal("479.20")
    assert extract_price(
        "Aiden & Ivy, Sofá a solo $32,999. Precio original$2,199.00."
    ) == Decimal("2199.00")
    assert extract_price(
        "Precio actual MXN$12,998.99. Agotado. $275.00 precio actual $275.00."
    ) == Decimal("12998.99")


def test_title_from_url() -> None:
    assert title_from_url(
        "https://www.costco.com.mx/Computadoras-y-Tablets/"
        "ASUS-ProArt-P16-Laptop-16-3K-OLED/p/706501"
    ) == "ASUS ProArt P16 Laptop 16 3K OLED"
    assert title_from_url(
        "https://www.walmart.com.mx/ip/laptop-hp-15/00082184449628"
    ) == "laptop hp 15"
    assert title_from_url("https://www.costco.com.mx/vinos") is None
