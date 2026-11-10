from __future__ import annotations

from decimal import Decimal

from app.agents.state import AgentState
from app.models import PriceSummary


def _format_money(value: Decimal) -> str:
    return f"${float(value):,.2f}"


def price_agent(state: AgentState) -> dict:
    opciones = state.get("opciones", [])
    if not opciones:
        return {
            "resumen_precios": None,
            "errores": [*state.get("errores", []), "No hay opciones para calcular precios."],
            "pasos": [*state.get("pasos", []), "precios:sin-opciones"],
        }

    presupuesto = state.get("presupuesto")
    advertencias = list(state.get("advertencias", []))
    consideradas = opciones
    dentro_presupuesto: int | None = None

    if presupuesto is not None and presupuesto > 0:
        dentro = [option for option in opciones if option.precio <= presupuesto]
        dentro_presupuesto = len(dentro)
        if dentro:
            consideradas = dentro
            excluidas = len(opciones) - len(dentro)
            if excluidas:
                advertencias.append(
                    f"{excluidas} opción(es) superan el presupuesto de "
                    f"{_format_money(presupuesto)} MXN y no se consideraron "
                    "para la recomendación."
                )
        else:
            advertencias.append(
                f"Ninguna opción está dentro del presupuesto de "
                f"{_format_money(presupuesto)} MXN; se muestran todas."
            )

    ordenadas = sorted(
        consideradas,
        key=lambda option: (option.precio, option.comercio.value),
    )
    minimo = ordenadas[0]
    maximo = ordenadas[-1]
    total = sum((option.precio for option in consideradas), Decimal("0"))
    promedio = (total / Decimal(len(consideradas))).quantize(Decimal("0.01"))

    resumen = PriceSummary(
        precio_final=minimo.precio,
        opcion_recomendada=minimo.nombre,
        precio_promedio=promedio,
        precio_minimo=minimo.precio,
        precio_maximo=maximo.precio,
        rango=maximo.precio - minimo.precio,
        moneda=minimo.moneda,
        opciones_consideradas=len(consideradas),
        comercio_mas_barato=minimo.comercio.display_name,
        comercio_mas_caro=maximo.comercio.display_name,
        presupuesto=presupuesto if presupuesto is not None and presupuesto > 0 else None,
        opciones_dentro_presupuesto=dentro_presupuesto,
    )
    return {
        "resumen_precios": resumen,
        "advertencias": advertencias,
        "pasos": [*state.get("pasos", []), "precios:ok"],
    }
