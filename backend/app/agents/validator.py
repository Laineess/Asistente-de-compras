from __future__ import annotations

from app.agents.state import AgentState


def validator(state: AgentState) -> dict:
    result = state.get("resultado")
    if result is None:
        return {"pasos": [*state.get("pasos", []), "validar:sin-resultado"]}

    warnings = list(state.get("advertencias", []))
    requested = set(state.get("tiendas") or result.tiendas)
    stores = {option.comercio for option in result.opciones}
    analyzed = stores & requested
    missing = requested - stores
    if missing:
        names = ", ".join(
            store.display_name for store in sorted(analyzed, key=lambda s: s.value)
        )
        warnings.append(
            f"Solo se analizaron {len(analyzed)} de {len(requested)} tiendas: "
            f"{names or 'ninguna'}."
        )
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
