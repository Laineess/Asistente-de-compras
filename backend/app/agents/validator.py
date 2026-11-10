from __future__ import annotations

from app.agents.state import AgentState


def validator(state: AgentState) -> dict:
    result = state.get("resultado")
    if result is None:
        return {"pasos": [*state.get("pasos", []), "validar:sin-resultado"]}

    warnings = list(state.get("advertencias", []))
    stores = {option.comercio for option in result.opciones}
    if len(stores) < 3:
        names = ", ".join(store.display_name for store in sorted(stores, key=lambda s: s.value))
        warnings.append(f"Solo se analizaron {len(stores)} de 3 tiendas: {names}.")
    if result.resumen_resenas is None or result.resumen_resenas.resenas_analizadas < 3:
        warnings.append("No se alcanzaron al menos 3 reseñas analizadas.")
    if any(option.fuente == "mock" for option in result.opciones):
        warnings.append(
            "Algunas opciones provienen del catálogo de respaldo (mock); "
            "verifica precios antes de comprar."
        )
    if result.errores:
        warnings.append("La búsqueda reportó errores parciales; revisa la lista de errores.")

    deduped: list[str] = []
    for warning in warnings:
        if warning not in deduped:
            deduped.append(warning)

    result.advertencias = deduped
    return {
        "resultado": result,
        "advertencias": deduped,
        "pasos": [*state.get("pasos", []), "validar:ok"],
    }
