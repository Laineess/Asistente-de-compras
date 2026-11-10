from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.state import AgentState
from app.llm import invoke_text
from app.models import (
    AnalysisResult,
    AudienceSummary,
    PriceSummary,
    ProductOption,
    ReviewSummary,
)
from app.prompts import SYNTHESIS_PROMPT


def _format_money(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _options_to_text(options: list[ProductOption]) -> str:
    lines: list[str] = []
    for index, option in enumerate(options, 1):
        lines.append(
            f"{index}. {option.nombre} | {option.comercio.display_name} | "
            f"{_format_money(option.precio)} {option.moneda} | "
            f"calificación {option.calificacion or 'N/D'} | "
            f"fuente: {option.fuente} | {option.url or 'sin URL'}"
        )
    return "\n".join(lines)


def _price_to_text(summary: PriceSummary | None) -> str:
    if summary is None:
        return "No disponible"
    return (
        f"Precio mínimo: {_format_money(summary.precio_minimo)} {summary.moneda}; "
        f"máximo: {_format_money(summary.precio_maximo)}; "
        f"promedio: {_format_money(summary.precio_promedio)}; "
        f"rango: {_format_money(summary.rango)}; "
        f"opción recomendada: {summary.opcion_recomendada} "
        f"({summary.comercio_mas_barato}); "
        f"comercio más caro: {summary.comercio_mas_caro}."
    )


def _review_to_text(summary: ReviewSummary | None) -> str:
    if summary is None:
        return "No disponible"
    return (
        f"Score: {summary.score}/10; reseñas analizadas: {summary.resenas_analizadas}; "
        f"síntesis: {summary.sintesis}; pros: {'; '.join(summary.pros)}; "
        f"contras: {'; '.join(summary.contras)}; "
        f"fuentes: {', '.join(summary.fuentes)}."
    )


def _audience_to_text(summary: AudienceSummary | None) -> str:
    if summary is None:
        return "No disponible"
    parts: list[str] = []
    for profile in summary.perfiles:
        parts.append(
            f"{profile.perfil}: {profile.descripcion} "
            f"(evidencia: {profile.evidencia or 'N/D'}; "
            f"idoneidad: {profile.porcentaje or 'N/D'}%)."
        )
    if summary.sintesis:
        parts.append(f"Síntesis: {summary.sintesis}")
    return " ".join(parts) or "No disponible"


def fallback_recommendation(state: AgentState) -> str:
    options = state.get("opciones", [])
    if not options:
        return "No se encontraron opciones suficientes para emitir una recomendación."

    cheapest = min(options, key=lambda option: option.precio)
    price = state.get("resumen_precios")
    review = state.get("resumen_resenas")
    audience = state.get("resumen_audiencia")

    lines = [
        f"Recomendación: {cheapest.nombre} en {cheapest.comercio.display_name} "
        f"por {_format_money(cheapest.precio)} {cheapest.moneda}."
    ]
    if price is not None:
        lines.append(
            f"Es la opción más económica entre {price.opciones_consideradas} analizadas, "
            f"con precios de {_format_money(price.precio_minimo)} a "
            f"{_format_money(price.precio_maximo)} "
            f"(promedio {_format_money(price.precio_promedio)})."
        )
    if review is not None:
        lines.append(f"Reseñas: {review.sintesis}")
    if audience is not None and audience.sintesis:
        lines.append(f"Por perfil: {audience.sintesis}")
    if state.get("tiendas_con_mock"):
        stores = ", ".join(store.display_name for store in state["tiendas_con_mock"])
        lines.append(
            f"Advertencia: algunos datos de {stores} provienen del catálogo "
            f"de respaldo (mock)."
        )
    return " ".join(lines)


def make_synthesis_agent(llm: BaseChatModel | None) -> Callable[[AgentState], dict]:
    def synthesis_agent(state: AgentState) -> dict:
        recommendation = fallback_recommendation(state)
        if llm is not None:
            text = invoke_text(
                llm,
                SYNTHESIS_PROMPT.format(
                    producto=state.get("consulta", ""),
                    opciones=_options_to_text(state.get("opciones", [])),
                    precios=_price_to_text(state.get("resumen_precios")),
                    resenas=_review_to_text(state.get("resumen_resenas")),
                    perfiles=_audience_to_text(state.get("resumen_audiencia")),
                    advertencias="; ".join(state.get("advertencias", [])) or "Ninguna.",
                ),
            )
            if text:
                recommendation = text

        result = AnalysisResult(
            producto=state.get("consulta", ""),
            tiendas=state.get("tiendas", []),
            opciones=state.get("opciones", []),
            resumen_precios=state.get("resumen_precios"),
            resumen_resenas=state.get("resumen_resenas"),
            usuarios_relevantes=state.get("resumen_audiencia"),
            recomendacion=recommendation,
            advertencias=list(state.get("advertencias", [])),
            errores=list(state.get("errores", [])),
            fecha_consulta=datetime.now(),
        )
        return {
            "resultado": result,
            "pasos": [*state.get("pasos", []), "sintetizar:ok"],
        }

    return synthesis_agent
