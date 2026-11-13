from __future__ import annotations

import html
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote

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
    "cava de vinos",
    "enfriador",
    "vinera",
    "copas",
    "copa",
    "vasos",
    "vaso",
    "sacacorchos",
    "decantador",
    "hielera",
)

QUERY_STOPWORDS = frozenset(
    {
        "a",
        "al",
        "algo",
        "algun",
        "alguna",
        "algunas",
        "algunos",
        "barata",
        "barato",
        "buena",
        "bueno",
        "busca",
        "buscando",
        "buscar",
        "busco",
        "calidad",
        "casa",
        "compara",
        "comparalas",
        "comparar",
        "compararlas",
        "comprar",
        "compra",
        "con",
        "costco",
        "de",
        "del",
        "dame",
        "el",
        "en",
        "escuela",
        "estudiante",
        "familia",
        "gamer",
        "gaming",
        "hasta",
        "hogar",
        "juegos",
        "la",
        "las",
        "los",
        "maximo",
        "me",
        "mejor",
        "menos",
        "mi",
        "mis",
        "muestrame",
        "mxn",
        "necesito",
        "nueva",
        "nuevo",
        "o",
        "oficina",
        "opcion",
        "opciones",
        "para",
        "pesos",
        "por",
        "precio",
        "precios",
        "presupuesto",
        "producto",
        "productos",
        "profesional",
        "que",
        "quiero",
        "recomienda",
        "recomiendame",
        "sam's",
        "sams",
        "sin",
        "tienda",
        "tiendas",
        "tope",
        "trabajo",
        "un",
        "una",
        "universidad",
        "unos",
        "unas",
        "wallmart",
        "walmart",
        "y",
    }
)

QUERY_SYNONYMS = {
    "laptop": (
        "laptop",
        "laptops",
        "macbook",
        "notebook",
        "portatil",
        "portatiles",
        "computadora",
        "computadoras",
    ),
    "computadora": (
        "computadora",
        "computadoras",
        "laptop",
        "laptops",
        "macbook",
        "notebook",
        "portatil",
        "portatiles",
        "pc",
    ),
    "celular": (
        "celular",
        "celulares",
        "smartphone",
        "smartphones",
        "telefono",
        "telefonos",
    ),
    "audifonos": ("audifonos", "auriculares", "headphones", "earbuds", "airpods"),
    "tv": ("tv", "televisor", "televisores", "television", "pantalla", "pantallas"),
    "televisor": (
        "televisor",
        "televisores",
        "television",
        "tv",
        "pantalla",
        "pantallas",
    ),
    "refrigerador": ("refrigerador", "refrigeradores", "refri", "nevera", "frigorifico"),
    "vino": ("vino", "vinos", "wine"),
    "tablet": ("tablet", "tablets", "ipad"),
    "consola": ("consola", "consolas", "playstation", "xbox", "nintendo"),
    "zapatos": ("zapatos", "tenis", "calzado"),
}

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

MONEY_AMOUNT = (
    r"(?:MXN\$?|MX\$|\$)\s*"
    r"([0-9]{1,3}(?:[,\s][0-9]{3})*(?:\.[0-9]{1,2})?)"
)
PRICE_PATTERNS = [
    re.compile(MONEY_AMOUNT, re.IGNORECASE),
    re.compile(r"\b([0-9]{1,3}(?:,[0-9]{3})+\.[0-9]{2})\b"),
]
CURRENT_PRICE_PATTERNS = [
    re.compile(
        r"Precio(?!\s+original)\s*"
        r"(?:actual|de socio|especial|final|en línea|en linea)?\s*"
        rf"[:.]?\s*{MONEY_AMOUNT}",
        re.IGNORECASE,
    ),
]
ORIGINAL_PRICE_PATTERNS = [
    re.compile(
        rf"Precio\s+original\s*[:.]?\s*{MONEY_AMOUNT}",
        re.IGNORECASE,
    ),
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


def title_from_url(url: str) -> str | None:
    value = unquote(url or "")
    slug = ""
    if "/p/" in value:
        slug = value.split("/p/", 1)[0].rsplit("/", 1)[-1]
    elif "/ip/" in value:
        slug = value.split("/ip/", 1)[1].split("/", 1)[0]
    if not slug:
        return None
    title = " ".join(re.sub(r"[-_]+", " ", slug).split())
    return title[:200] or None


def normalize_search_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(value.lower().split())


def query_terms(query: str) -> tuple[str, ...]:
    terms = re.findall(r"[a-z0-9]+", normalize_search_text(query))
    expanded: list[str] = []
    for term in terms:
        if (len(term) < 2 and not term.isdigit()) or term in QUERY_STOPWORDS:
            continue
        expanded.extend(QUERY_SYNONYMS.get(term, (term,)))
    return tuple(dict.fromkeys(expanded))


def is_relevant(query: str, title: str, url: str) -> bool:
    terms = query_terms(query)
    if not terms:
        return True
    haystack = normalize_search_text(f"{title} {url}")
    tokens = set(re.findall(r"[a-z0-9]+", haystack))
    return any(
        term in tokens or f"{term}s" in tokens or f"{term}es" in tokens
        for term in terms
    )


def _match_price(match: re.Match[str]) -> Decimal | None:
    raw = match.group(1).replace(",", "").replace(" ", "")
    try:
        price = Decimal(raw)
    except InvalidOperation:
        return None
    return price if price > 0 else None


def extract_price(text: str, title: str | None = None) -> Decimal | None:
    value = text or ""
    for pattern in [*CURRENT_PRICE_PATTERNS, *ORIGINAL_PRICE_PATTERNS]:
        match = pattern.search(value)
        if match is not None:
            price = _match_price(match)
            if price is not None:
                return price

    search_text = value
    if title:
        index = search_text.lower().find(title.lower())
        if index > 0:
            search_text = search_text[index:]
    for pattern in PRICE_PATTERNS:
        match = pattern.search(search_text)
        if match is None:
            continue
        price = _match_price(match)
        if price is not None:
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
            if not is_relevant(query, title, url):
                continue
            if not is_relevant(query, title, ""):
                url_title = title_from_url(url)
                if url_title and is_relevant(query, url_title, ""):
                    title = url_title
            if self._is_accessory_only(query, title):
                continue

            combined = f"{title} {content}"
            price = extract_price(combined, title=title)
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
