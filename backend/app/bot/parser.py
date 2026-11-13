from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from app.models import Store

STORE_ALIASES: dict[str, Store] = {
    "walmart": Store.walmart,
    "wal mart": Store.walmart,
    "costco": Store.costco,
    "sams": Store.sams,
    "sam s": Store.sams,
    "sams club": Store.sams,
}

PROFILE_ALIASES: dict[str, str] = {
    "estudiante": "estudiante",
    "universidad": "estudiante",
    "escuela": "estudiante",
    "profesional": "profesional",
    "trabajo": "profesional",
    "oficina": "profesional",
    "gamer": "gamer",
    "gaming": "gamer",
    "juegos": "gamer",
    "hogar": "hogar",
    "casa": "hogar",
    "familia": "hogar",
}

LEADING_PATTERN = re.compile(
    r"^(?:hola|oye|por favor|busca(?:me)?|buscar|compara(?:me)?|comparar|"
    r"encuentra(?:me)?|necesito|quiero|quisiera|me gustaria|recomiendame|"
    r"recomienda(?:me)?|ayudame a|puedes buscar|dame|muestrame|"
    r"que me recomiendas|opciones de)\b[\s,.:;-]*",
    re.IGNORECASE,
)

BUDGET_PATTERN = re.compile(
    r"(?:presupuesto(?:\s+m[aá]ximo)?|m[aá]ximo|max\.?|hasta|no m[aá]s de|"
    r"menos de|tope|por debajo de)\s*(?:de\s*)?\$?\s*(\d[\d.,]*)\s*"
    r"(mil|k|pesos|mxn)?\b",
    re.IGNORECASE,
)

BUDGET_AMOUNT_PATTERN = re.compile(
    r"(?<![\d.,])\$?\s*(\d[\d.,]*\d|\d)\s*(mil|k|pesos|mxn)?\b",
    re.IGNORECASE,
)

LIMIT_PATTERN = re.compile(
    r"(?:l[ií]mite|opciones)\s*(?:de\s*)?(\d{1,2})|"
    r"(\d{1,2})\s*(?:por|de)\s*(?:tienda|tiendas)",
    re.IGNORECASE,
)

STORE_PATTERN = re.compile(
    r"\b(?:en|de|tienda|tiendas)?\s*(walmart|wal mart|costco|sams club|sams|sam'?s)\b",
    re.IGNORECASE,
)

PROFILE_PATTERN = re.compile(
    r"\b(?:para|de|uso)\s+(?:el|la|los|las|un|una)?\s*"
    r"(estudiante|universidad|escuela|profesional|trabajo|oficina|gamer|"
    r"gaming|juegos|hogar|casa|familia)\b",
    re.IGNORECASE,
)

LEADING_STOPWORDS = {
    "un",
    "una",
    "unos",
    "unas",
    "el",
    "la",
    "los",
    "las",
    "de",
    "del",
    "para",
    "por",
    "en",
    "con",
    "sin",
    "y",
    "o",
    "que",
    "me",
    "mi",
    "mis",
    "al",
    "a",
    "producto",
    "productos",
    "opcion",
    "opciones",
}

TRAILING_STOPWORDS = {"y", "o", "en", "de", "del", "para", "por", "con", "al", "a"}


@dataclass(slots=True)
class ParsedRequest:
    producto: str | None = None
    tiendas: list[Store] | None = None
    presupuesto: Decimal | None = None
    presupuesto_mencionado: bool = False
    perfil: str | None = None
    perfil_mencionado: bool = False
    limite: int | None = None
    notas: list[str] = field(default_factory=list)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.lower().split())


def _amount(raw: str, suffix: str | None) -> Decimal | None:
    raw = raw.strip().replace(" ", "")
    if not raw:
        return None
    suffix = (suffix or "").lower()
    if suffix in {"mil", "k"}:
        raw = raw.replace(",", ".")
        try:
            return Decimal(raw) * 1000
        except InvalidOperation:
            return None
    if "," in raw and "." not in raw:
        raw = raw.replace(",", "")
    elif "," in raw and "." in raw:
        raw = raw.replace(",", "")
    elif raw.count(".") == 1 and len(raw.split(".")[-1]) == 3:
        raw = raw.replace(".", "")
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None
    if value <= 0:
        return None
    return value.quantize(Decimal("0.01"))


def _remove_spans(text: str, spans: list[tuple[int, int]]) -> str:
    if not spans:
        return text
    spans = sorted(spans)
    parts: list[str] = []
    cursor = 0
    for start, end in spans:
        if start < cursor:
            continue
        parts.append(text[cursor:start])
        parts.append(" ")
        cursor = end
    parts.append(text[cursor:])
    return " ".join("".join(parts).split())


def _clean_product(text: str) -> str:
    text = _normalize(text)
    text = re.sub(r"[^\w\s+.-]", " ", text)
    text = " ".join(text.split())
    for _ in range(4):
        before = text
        text = LEADING_PATTERN.sub("", text, count=1).strip(" ,.;:-")
        words = text.split()
        while words and words[0] in LEADING_STOPWORDS:
            words.pop(0)
        while words and words[-1] in TRAILING_STOPWORDS:
            words.pop()
        text = " ".join(words)
        if text == before:
            break
    text = re.sub(r"\b(?:por favor|gracias)\b", " ", text)
    text = " ".join(text.split()).strip(" ,.;:-")
    return text[:200]


def _parse_stores(text: str) -> tuple[list[Store] | None, list[tuple[int, int]]]:
    normalized = _normalize(text)
    all_stores = re.search(r"\b(todas las tiendas|todas|las tres)\b", normalized)
    if all_stores is not None:
        full = re.search(
            r"\b(?:en\s+)?(?:todas\s+las\s+tiendas|las\s+tres\s+tiendas|"
            r"todas|las\s+tres)\b",
            text,
            re.IGNORECASE,
        )
        span = full.span() if full is not None else (all_stores.start(), all_stores.end())
        return list(Store), [span]
    found: list[Store] = []
    spans: list[tuple[int, int]] = []
    for match in STORE_PATTERN.finditer(text):
        raw = _normalize(match.group(1))
        store = STORE_ALIASES.get(raw)
        if store is not None and store not in found:
            found.append(store)
        spans.append(match.span())
    return (found or None), spans


def _parse_budget(text: str) -> tuple[Decimal | None, bool, list[tuple[int, int]]]:
    match = BUDGET_PATTERN.search(text)
    if match is not None:
        value = _amount(match.group(1), match.group(2))
        return value, True, [match.span()]

    match = BUDGET_AMOUNT_PATTERN.search(text)
    if match is not None:
        value = _amount(match.group(1), match.group(2))
        if value is not None and value >= 1000:
            return value, True, [match.span()]

    match = re.search(
        r"\b(sin l[ií]mite|sin presupuesto|presupuesto libre)\b",
        text,
        re.IGNORECASE,
    )
    if match is not None:
        return None, True, [match.span()]
    return None, False, []


def _parse_profile(text: str) -> tuple[str | None, bool, list[tuple[int, int]]]:
    match = PROFILE_PATTERN.search(text)
    if match is not None:
        profile = PROFILE_ALIASES.get(_normalize(match.group(1)))
        return profile, True, [match.span()]

    normalized = _normalize(text).strip(" .,;:!¡?¿")
    profile = PROFILE_ALIASES.get(normalized)
    if profile is not None:
        return profile, True, [(0, len(text))]
    return None, False, []


def _parse_limit(text: str) -> tuple[int | None, list[tuple[int, int]]]:
    match = LIMIT_PATTERN.search(text)
    if match is None:
        return None, []
    raw = match.group(1) or match.group(2)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None, []
    if 1 <= value <= 10:
        return value, [match.span()]
    return None, [match.span()]


def parse_request(text: str) -> ParsedRequest:
    if not text or not text.strip():
        return ParsedRequest(notas=["mensaje vacio"])

    tiendas, store_spans = _parse_stores(text)
    presupuesto, budget_given, budget_spans = _parse_budget(text)
    perfil, profile_given, profile_spans = _parse_profile(text)
    limite, limit_spans = _parse_limit(text)

    cleaned = _remove_spans(
        text,
        [*store_spans, *budget_spans, *profile_spans, *limit_spans],
    )
    producto = _clean_product(cleaned)

    notas: list[str] = []
    if not producto:
        notas.append("producto no identificado")
    return ParsedRequest(
        producto=producto or None,
        tiendas=tiendas,
        presupuesto=presupuesto,
        presupuesto_mencionado=budget_given,
        perfil=perfil,
        perfil_mencionado=profile_given,
        limite=limite,
        notas=notas,
    )
