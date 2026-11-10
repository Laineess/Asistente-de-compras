from __future__ import annotations

import re
from typing import Any, Callable

from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.state import AgentState
from app.llm import invoke_json
from app.models import ProductOption, ReviewSummary
from app.prompts import REVIEW_PROMPT
from app.providers.service import normalize_key

POSITIVE_WORDS = {
    "bueno",
    "buena",
    "buen",
    "excelente",
    "rapido",
    "rapida",
    "comodo",
    "comoda",
    "calidad",
    "recomiendo",
    "perfecto",
    "perfecta",
    "bonito",
    "bonita",
    "potente",
    "fluido",
    "fluida",
    "mejor",
    "satisfecho",
    "satisfecha",
    "funciona",
    "util",
    "duradero",
    "duradera",
    "ligero",
    "ligera",
    "practico",
    "practica",
}
NEGATIVE_WORDS = {
    "malo",
    "mala",
    "lento",
    "lenta",
    "caro",
    "cara",
    "falla",
    "fallas",
    "problema",
    "problemas",
    "deficiente",
    "pesimo",
    "pesima",
    "ruido",
    "calienta",
    "calor",
    "devolvi",
    "devolvio",
    "defectuoso",
    "defectuosa",
    "fragil",
    "incomodo",
    "incomoda",
    "tarde",
    "retraso",
    "pesado",
    "pesada",
}
POSITIVE_PHRASES = (
    "buena bateria",
    "bateria dura",
    "buen precio",
    "buena calidad",
    "muy bueno",
    "muy buena",
    "lo recomiendo",
)
NEGATIVE_PHRASES = (
    "no recomiendo",
    "no funciona",
    "no sirve",
    "mala calidad",
    "no me gusto",
    "salio mal",
    "bateria dura poco",
    "poca bateria",
    "bateria mala",
    "bateria mejorable",
    "se calienta",
    "hace ruido",
    "se llena",
    "llena rapido",
    "poco almacenamiento",
    "almacenamiento insuficiente",
    "poco espacio",
    "peso alto",
    "pocos puertos",
)
MARKETING_MARKERS = (
    "encuentra la",
    "encuentra el",
    "mejor se acomode",
    "a tus necesidades",
    "descubre",
    "compra ahora",
    "miles de productos",
    "precio de socio",
    "envio gratis",
)


def _texts(options: list[ProductOption]) -> tuple[list[str], list[str], bool]:
    texts: list[str] = []
    sources: list[str] = []
    used_descriptions = False
    for option in options:
        for review in option.resenas:
            texts.append(review.texto)
            if option.comercio.display_name not in sources:
                sources.append(option.comercio.display_name)
    if len(texts) < 3:
        for option in options:
            texts.append(option.descripcion or option.nombre)
            used_descriptions = True
            if option.comercio.display_name not in sources:
                sources.append(option.comercio.display_name)
            if len(texts) >= 3:
                break
    while len(texts) < 3:
        texts.append("No hay suficientes opiniones verificadas para este producto.")
        used_descriptions = True
    return texts, sources, used_descriptions


def _sentiment(text: str) -> float:
    normalized = normalize_key(text)
    words = set(re.findall(r"[a-z0-9]+", normalized))
    positive = len(words & POSITIVE_WORDS)
    negative = len(words & NEGATIVE_WORDS)
    positive += sum(1 for phrase in POSITIVE_PHRASES if phrase in normalized)
    negative += sum(1 for phrase in NEGATIVE_PHRASES if phrase in normalized)
    return max(0.0, min(10.0, 5.0 + 2.0 * (positive - negative)))


def _clauses(text: str) -> list[str]:
    normalized = re.sub(
        r"\b(pero|aunque|sin embargo)\b",
        ",",
        text,
        flags=re.IGNORECASE,
    )
    parts = re.split(r"[;,.]", normalized)
    return [part.strip() for part in parts if part.strip()]


def _clean_snippet(text: str) -> str:
    return " ".join(text.split()).strip(" .,;:¡!¿?")


def _snippets(texts: list[str], positive: bool) -> list[str]:
    selected: list[str] = []
    for text in texts:
        for clause in _clauses(text):
            normalized = normalize_key(clause)
            if any(marker in normalized for marker in MARKETING_MARKERS):
                continue
            score = _sentiment(clause)
            if (positive and score > 5.5) or (not positive and score < 4.5):
                snippet = _clean_snippet(clause)
                if len(snippet) > 8 and snippet not in selected:
                    selected.append(snippet[:180])
            if len(selected) >= 3:
                return selected
    return selected


def heuristic_review(options: list[ProductOption]) -> ReviewSummary:
    texts, sources, used_descriptions = _texts(options)
    scores = [_sentiment(text) for text in texts]
    score = round(sum(scores) / len(scores), 1)
    pros = _snippets(texts, positive=True)
    contras = _snippets(texts, positive=False)
    if not pros:
        pros = ["Sin comentarios positivos destacados."]
    if not contras:
        contras = ["Sin comentarios negativos destacados."]
    sintesis = (
        f"Se analizaron {len(texts)} opiniones. Score promedio: {score}/10. "
        f"Fortalezas: {'; '.join(pros[:2])}. "
        f"Quejas: {'; '.join(contras[:2])}."
    )
    if used_descriptions:
        sintesis += " Se usaron descripciones como respaldo por falta de reseñas."
    return ReviewSummary(
        score=score,
        resenas_analizadas=len(texts),
        sintesis=sintesis,
        pros=pros,
        contras=contras,
        fuentes=sources,
    )


def _reviews_to_text(options: list[ProductOption]) -> str:
    lines: list[str] = []
    for option in options:
        for review in option.resenas:
            lines.append(f"- [{option.comercio.display_name}] {review.texto}")
    if not lines:
        for option in options:
            lines.append(
                f"- [{option.comercio.display_name}] {option.descripcion or option.nombre}"
            )
    return "\n".join(lines)


def _sanitize_summary(
    data: dict[str, Any],
    options: list[ProductOption],
    fallback: ReviewSummary,
) -> ReviewSummary:
    texts, sources, _ = _texts(options)
    data["resenas_analizadas"] = len(texts)
    data.setdefault("fuentes", sources)
    if not isinstance(data.get("pros"), list):
        data["pros"] = fallback.pros
    if not isinstance(data.get("contras"), list):
        data["contras"] = fallback.contras
    try:
        return ReviewSummary.model_validate(data)
    except Exception:
        return fallback


def make_review_agent(llm: BaseChatModel | None) -> Callable[[AgentState], dict]:
    def review_agent(state: AgentState) -> dict:
        options = state.get("opciones", [])
        fallback = heuristic_review(options)
        summary = fallback
        if llm is not None:
            data = invoke_json(llm, REVIEW_PROMPT.format(reviews=_reviews_to_text(options)))
            if data is not None:
                summary = _sanitize_summary(data, options, fallback)
        return {
            "resumen_resenas": summary,
            "pasos": [*state.get("pasos", []), "resenas:ok"],
        }

    return review_agent
