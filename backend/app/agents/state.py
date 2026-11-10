from __future__ import annotations

from decimal import Decimal
from typing import Literal, TypedDict

from app.models import (
    AnalysisResult,
    AudienceSummary,
    PriceSummary,
    ProductOption,
    ReviewSummary,
    Store,
)

Route = Literal["buscar", "precios", "resenas", "audiencia", "sintetizar", "fin"]


class AgentState(TypedDict, total=False):
    consulta: str
    limite_por_tienda: int
    perfil: str | None
    presupuesto: Decimal | None
    tiendas: list[Store]
    opciones: list[ProductOption]
    errores: list[str]
    tiendas_con_mock: list[Store]
    resumen_precios: PriceSummary | None
    resumen_resenas: ReviewSummary | None
    resumen_audiencia: AudienceSummary | None
    resultado: AnalysisResult | None
    filas_guardadas: int
    siguiente: Route
    pasos: list[str]
    advertencias: list[str]


def initial_state(
    consulta: str,
    limite_por_tienda: int = 3,
    perfil: str | None = None,
    tiendas: list[Store] | None = None,
    presupuesto: Decimal | None = None,
) -> AgentState:
    return {
        "consulta": consulta.strip(),
        "limite_por_tienda": limite_por_tienda,
        "perfil": perfil,
        "presupuesto": presupuesto if presupuesto and presupuesto > 0 else None,
        "tiendas": tiendas or list(Store),
        "opciones": [],
        "errores": [],
        "tiendas_con_mock": [],
        "resumen_precios": None,
        "resumen_resenas": None,
        "resumen_audiencia": None,
        "resultado": None,
        "filas_guardadas": 0,
        "siguiente": "buscar",
        "pasos": [],
        "advertencias": [],
    }
