from __future__ import annotations

from decimal import Decimal

from app.agents.state import AgentState
from app.models import PriceSummary


def price_agent(state: AgentState) -> dict:
    opciones = state.get("opciones", [])
    if not opciones:
        return {
            "resumen_precios": None,
            "errores": [*state.get("errores", []), "No hay opciones para calcular precios."],
            "pasos": [*state.get("pasos", []), "precios:sin-opciones"],
        }

    ordenadas = sorted(opciones, key=lambda option: (option.precio, option.comercio.value))
    minimo = ordenadas[0]
    maximo = ordenadas[-1]
    total = sum((option.precio for option in opciones), Decimal("0"))
    promedio = (total / Decimal(len(opciones))).quantize(Decimal("0.01"))

    resumen = PriceSummary(
        precio_final=minimo.precio,
        opcion_recomendada=minimo.nombre,
        precio_promedio=promedio,
        precio_minimo=minimo.precio,
        precio_maximo=maximo.precio,
        rango=maximo.precio - minimo.precio,
        moneda=minimo.moneda,
        opciones_consideradas=len(opciones),
        comercio_mas_barato=minimo.comercio.display_name,
        comercio_mas_caro=maximo.comercio.display_name,
    )
    return {
        "resumen_precios": resumen,
        "pasos": [*state.get("pasos", []), "precios:ok"],
    }
