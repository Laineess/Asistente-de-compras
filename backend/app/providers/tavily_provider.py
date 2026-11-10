from __future__ import annotations

import html
import re
from decimal import Decimal, InvalidOperation

from tavily import TavilyClient

from app.models import ProductOption, ReviewSnippet, Store
from app.providers.base import StoreProvider

STORE_DOMAINS = {
    Store.walmart: ["walmart.com.mx"],
    Store.costco: ["costco.com.mx"],
    Store.sams: ["sams.com.mx"],
}

PRODUCT_URL_HINTS = {
    Store.walmart: ("/ip/",),
    Store.costco: ("/p/",),
    Store.sams: ("/ip/",),
}

GENERIC_TITLE_MARKERS = (
    "todas las",
    "venta de",
    "miles de productos",
    "llevate",
    "llévate",
    "encuentra las mejores",
    "tienda en línea",
    "tienda en linea",
    "precio de socio",
    "departamentos",
)

ACCESSORY_MARKERS = (
    "mochila",
    "funda",
    "estuche",
    "cargador",
    "soporte",
    "base para",
    "cooler",
    "mouse",
    "teclado",
    "monitor",
    "impresora",
    "cartucho",
    "tinta",
    "cable",
    "adaptador",
    "protector",
    "skin",
)

NOISE_MARKERS = (
    "precio actual",
    "antes $",
    "de 5 estrellas",
    "meses sin intereses",
    "envío",
    "envio",
    "agregar a mi lista",
    "sin costo",
    "encuentra la",
    "encuentra el",
    "mejor se acomode",
    "a tus necesidades",
    "descubre",
    "compra ahora",
    "miles de productos",
    "precio de socio",
    "envío gratis",
    "envio gratis",
    "calificación de nuestros socios",
    "calificacion de nuestros socios",
    "también te puede interesar",
    "tambien te puede interesar",
    "te puede interesar",
    "otros socios",
    "otros productos",
    "también compraron",
    "tambien compraron",
    "ir directo al contenido",
    "iniciar sesión",
    "iniciar sesion",
    "carrito",
    "cookies",
    "imprimir",
    "última oportunidad",
    "ultima oportunidad",
    "armazones",
    "lentes de sol",
    "garantía extendida",
    "garantia extendida",
    "este sitio web",
    "política de cookies",
    "politica de cookies",
    "productos similares",
    "menú de navegación",
    "menu de navegacion",
)

STORE_SUFFIX_PATTERN = re.compile(
    r"\s*\|\s*(?:Walmart|Costco|Sam'?s)"
    r"(?:\s+(?:México|Mexico|en línea|en linea))?\s*$",
    re.IGNORECASE,
)

PRICE_PATTERNS = [
    re.compile(
        r"(?:MXN|MX\$|\$)\s*([0-9]{1,3}(?:[,\s][0-9]{3})*(?:\.[0-9]{1,2})?)",
        re.IGNORECASE,
    ),
    re.compile(r"\b([0-9]{1,3}(?:,[0-9]{3})+\.[0-9]{2})\b"),
]
RATING_PATTERN = re.compile(r"([0-5](?:\.[0-9])?)\s*(?:de\s*5|/\s*5|estrellas)", re.IGNORECASE)
SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+|\s+[·;|]\s+|\n+")


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return " ".join(value.split())


def clean_product_title(value: str) -> str:
    title = clean_text(value)
    while True:
        cleaned = STORE_SUFFIX_PATTERN.sub("", title).strip()
        if cleaned == title:
            break
        title = cleaned
    return title


def extract_price(text: str) -> Decimal | None:
    for pattern in PRICE_PATTERNS:
        match = pattern.search(text or "")
        if not match:
            continue
        raw = match.group(1).replace(",", "").replace(" ", "")
        try:
            price = Decimal(raw)
        except InvalidOperation:
            continue
        if price > 0:
            return price
    return None


def extract_rating(text: str) -> float | None:
    match = RATING_PATTERN.search(text or "")
    return float(match.group(1)) if match else None


def extract_reviews(text: str, limit: int = 3) -> list[ReviewSnippet]:
    raw = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    parts = [" ".join(part.split()) for part in SPLIT_PATTERN.split(raw) if part.strip()]
    filtered: list[str] = []
    for part in parts:
        lowered = part.lower()
        if len(part) <= 25 or len(part) > 300:
            continue
        if any(marker in lowered for marker in NOISE_MARKERS):
            continue
        if any(char in part for char in ("$", "★", "€")):
            continue
        if "http" in lowered or "www." in lowered:
            continue
        filtered.append(part)
        if len(filtered) >= limit:
            break
    return [ReviewSnippet(texto=part) for part in filtered]


class TavilyProvider(StoreProvider):
    def __init__(
        self,
        store: Store,
        api_key: str,
        client: TavilyClient | None = None,
    ) -> None:
        super().__init__(store)
        if not api_key and client is None:
            raise ValueError("Tavily API key requerida")
        self._client = client or TavilyClient(api_key=api_key)

    def search(self, query: str, limit: int = 3) -> list[ProductOption]:
        response = self._client.search(
            query=f"{query} precio MXN {self.store.display_name}",
            search_depth="advanced",
            max_results=max(limit * 4, 12),
            include_domains=STORE_DOMAINS[self.store],
        )

        results = response.get("results", [])
        results.sort(key=lambda result: result.get("score", 0), reverse=True)

        options: list[ProductOption] = []
        for result in results:
            url = result.get("url", "")
            title = clean_product_title(result.get("title", ""))
            content = clean_text(result.get("content", ""))

            if not url or not self._is_product_url(url):
                continue
            if self._is_generic_title(title):
                continue
            if self._is_accessory_only(query, title):
                continue

            combined = f"{title} {content}"
            price = extract_price(combined)
            if not title or price is None:
                continue

            reviews = extract_reviews(content)
            options.append(
                ProductOption(
                    nombre=title,
                    comercio=self.store,
                    precio=price,
                    moneda="MXN",
                    url=url,
                    descripcion=reviews[0].texto if reviews else None,
                    calificacion=extract_rating(combined),
                    resenas=reviews,
                    fuente="tavily",
                )
            )
            if len(options) >= limit:
                break

        return options

    def _is_product_url(self, url: str) -> bool:
        return any(hint in url for hint in PRODUCT_URL_HINTS[self.store])

    @staticmethod
    def _is_generic_title(title: str) -> bool:
        normalized = title.lower()
        return any(marker in normalized for marker in GENERIC_TITLE_MARKERS)

    @staticmethod
    def _is_accessory_only(query: str, title: str) -> bool:
        query_lower = query.lower()
        title_lower = title.lower()
        return any(
            marker in title_lower and marker not in query_lower
            for marker in ACCESSORY_MARKERS
        )
