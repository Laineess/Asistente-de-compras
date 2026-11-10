from __future__ import annotations

import re
from typing import Any, Callable

from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.state import AgentState
from app.llm import invoke_json
from app.models import (
    AudienceProfile,
    AudienceSummary,
    PriceSummary,
    ProductOption,
    ReviewSummary,
)
from app.prompts import AUDIENCE_PROMPT
from app.providers.service import normalize_key

GAMER_KEYWORDS = (
    "gaming",
    "gamer",
    "rtx",
    "geforce",
    "victus",
    "loq",
    "tuf",
    "rog",
    "ryzen 7",
    "ryzen 9",
    "core i7",
    "core i9",
)


def _format_money(value: float | int) -> str:
    return f"${float(value):,.2f}"


def _gb_values(option: ProductOption) -> list[int]:
    text = f"{option.nombre} {option.descripcion or ''}".lower()
    return [int(value) for value in re.findall(r"(\d+)\s*gb", text)]


def _specs(option: ProductOption) -> tuple[int, int]:
    values = _gb_values(option)
    if not values:
        return 0, 0
    ram = values[0]
    storage = max(values[1:]) if len(values) > 1 else 0
    return ram, storage


def _keyword_count(option: ProductOption, keywords: tuple[str, ...]) -> int:
    text = normalize_key(f"{option.nombre} {option.descripcion or ''}")
    return sum(1 for keyword in keywords if keyword in text)


def heuristic_audience(
    options: list[ProductOption],
    price_summary: PriceSummary | None,
    review_summary: ReviewSummary | None,
) -> AudienceSummary:
    if not options:
        return AudienceSummary(perfiles=[], sintesis="No hay opciones para recomendar.")

    ordered = sorted(options, key=lambda option: option.precio)
    cheapest = ordered[0]
    average = (
        float(price_summary.precio_promedio)
        if price_summary
        else sum(float(option.precio) for option in options) / len(options)
    )

    professional = max(
        options,
        key=lambda option: (*_specs(option), option.calificacion or 0),
    )
    gamer = max(
        options,
        key=lambda option: (
            _keyword_count(option, GAMER_KEYWORDS),
            *_specs(option),
            option.calificacion or 0,
        ),
    )
    home = max(
        options,
        key=lambda option: (option.calificacion or 0, -abs(float(option.precio) - average)),
    )

    price_min = float(price_summary.precio_minimo) if price_summary else float(cheapest.precio)
    price_max = float(price_summary.precio_maximo) if price_summary else float(ordered[-1].precio)
    price_range = max(price_max - price_min, 1.0)

    student_pct = max(
        40.0,
        min(100.0, 100.0 - ((float(cheapest.precio) - price_min) / price_range) * 60.0),
    )
    professional_ram, professional_storage = _specs(professional)
    gamer_ram, _ = _specs(gamer)
    gamer_keywords = _keyword_count(gamer, GAMER_KEYWORDS)

    profiles = [
        AudienceProfile(
            perfil="Estudiante",
            descripcion=(
                f"Mejor relación precio-beneficio: {cheapest.nombre} en "
                f"{cheapest.comercio.display_name}."
            ),
            evidencia=(
                f"{_format_money(cheapest.precio)} MXN; "
                f"calificación {cheapest.calificacion or 'N/D'}."
            ),
            porcentaje=round(student_pct, 1),
        ),
        AudienceProfile(
            perfil="Profesional",
            descripcion=(
                f"Mayor capacidad para trabajo: {professional.nombre} en "
                f"{professional.comercio.display_name}."
            ),
            evidencia=(
                f"RAM {professional_ram} GB, almacenamiento {professional_storage} GB; "
                f"precio {_format_money(professional.precio)} MXN."
            ),
            porcentaje=min(100.0, 50.0 + professional_ram * 2 + professional_storage / 64),
        ),
        AudienceProfile(
            perfil="Gamer",
            descripcion=(
                f"Opción con mejores indicios de rendimiento: {gamer.nombre} en "
                f"{gamer.comercio.display_name}."
            ),
            evidencia=(
                f"Palabras clave gamer: {gamer_keywords}; "
                f"precio {_format_money(gamer.precio)} MXN."
            ),
            porcentaje=min(100.0, 40.0 + gamer_keywords * 15 + gamer_ram * 2),
        ),
        AudienceProfile(
            perfil="Hogar",
            descripcion=(
                f"Opción mejor calificada para uso general: {home.nombre} en "
                f"{home.comercio.display_name}."
            ),
            evidencia=(
                f"Calificación {home.calificacion or 'N/D'}; "
                f"precio {_format_money(home.precio)} MXN."
            ),
            porcentaje=min(100.0, (home.calificacion or 4.0) * 20),
        ),
    ]

    sintesis = (
        f"Estudiante: {cheapest.nombre} ({cheapest.comercio.display_name}). "
        f"Profesional: {professional.nombre} ({professional.comercio.display_name}). "
        f"Gamer: {gamer.nombre} ({gamer.comercio.display_name}). "
        f"Hogar: {home.nombre} ({home.comercio.display_name})."
    )
    if review_summary is not None:
        sintesis += f" Score de reseñas: {review_summary.score}/10."
    return AudienceSummary(perfiles=profiles, sintesis=sintesis)


def _sanitize_profile(profile: dict[str, Any]) -> dict[str, Any] | None:
    perfil = profile.get("perfil")
    descripcion = profile.get("descripcion")
    if (
        not isinstance(perfil, str)
        or not perfil.strip()
        or not isinstance(descripcion, str)
        or not descripcion.strip()
    ):
        return None

    percentage = profile.get("porcentaje")
    if isinstance(percentage, str):
        percentage = percentage.replace("%", "").strip()
        try:
            percentage = float(percentage)
        except ValueError:
            percentage = None
    if isinstance(percentage, (int, float)) and 0 <= percentage <= 1:
        percentage = percentage * 100
    if isinstance(percentage, (int, float)):
        percentage = max(0.0, min(100.0, float(percentage)))
    else:
        percentage = None

    evidence = profile.get("evidencia")
    return {
        "perfil": perfil.strip(),
        "descripcion": descripcion.strip(),
        "evidencia": evidence.strip() if isinstance(evidence, str) else None,
        "porcentaje": percentage,
    }


def _sanitize_audience(data: dict[str, Any], fallback: AudienceSummary) -> AudienceSummary:
    profiles = data.get("perfiles")
    if not isinstance(profiles, list):
        return fallback

    cleaned = [
        item
        for item in (
            _sanitize_profile(profile)
            for profile in profiles
            if isinstance(profile, dict)
        )
        if item
    ]

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in cleaned:
        key = item["perfil"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    cleaned = unique

    if len(cleaned) < 3:
        existing = {item["perfil"].lower() for item in cleaned}
        for profile in fallback.perfiles:
            if profile.perfil.lower() not in existing:
                cleaned.append(profile.model_dump())
            if len(cleaned) >= 3:
                break
    if len(cleaned) < 3:
        return fallback

    sintesis = data.get("sintesis")
    return AudienceSummary(
        perfiles=[AudienceProfile.model_validate(profile) for profile in cleaned],
        sintesis=(
            sintesis.strip()
            if isinstance(sintesis, str) and sintesis.strip()
            else fallback.sintesis
        ),
    )


def _options_to_text(options: list[ProductOption]) -> str:
    lines: list[str] = []
    for index, option in enumerate(options, 1):
        lines.append(
            f"{index}. {option.nombre} | {option.comercio.display_name} | "
            f"{_format_money(option.precio)} {option.moneda} | "
            f"calificación {option.calificacion or 'N/D'} | fuente: {option.fuente}"
        )
    return "\n".join(lines)


def _price_to_text(summary: PriceSummary | None) -> str:
    if summary is None:
        return "No disponible"
    return (
        f"mínimo {_format_money(summary.precio_minimo)}, "
        f"máximo {_format_money(summary.precio_maximo)}, "
        f"promedio {_format_money(summary.precio_promedio)}, "
        f"recomendada {summary.opcion_recomendada}"
    )


def _review_to_text(summary: ReviewSummary | None) -> str:
    if summary is None:
        return "No disponible"
    return f"score {summary.score}/10; {summary.sintesis}"


def make_audience_agent(llm: BaseChatModel | None) -> Callable[[AgentState], dict]:
    def audience_agent(state: AgentState) -> dict:
        options = state.get("opciones", [])
        fallback = heuristic_audience(
            options,
            state.get("resumen_precios"),
            state.get("resumen_resenas"),
        )
        summary = fallback
        if llm is not None:
            data = invoke_json(
                llm,
                AUDIENCE_PROMPT.format(
                    producto=state.get("consulta", ""),
                    opciones=_options_to_text(options),
                    precios=_price_to_text(state.get("resumen_precios")),
                    resenas=_review_to_text(state.get("resumen_resenas")),
                ),
            )
            if data is not None:
                summary = _sanitize_audience(data, fallback)

        if state.get("perfil"):
            perfil = state["perfil"].strip()
            if perfil and all(
                profile.perfil.lower() != perfil.lower() for profile in summary.perfiles
            ):
                summary.perfiles.append(
                    AudienceProfile(
                        perfil=perfil.capitalize(),
                        descripcion=f"Perfil solicitado: {perfil}.",
                        evidencia="Preferencia indicada por el usuario.",
                    )
                )

        return {
            "resumen_audiencia": summary,
            "pasos": [*state.get("pasos", []), "audiencia:ok"],
        }

    return audience_agent
