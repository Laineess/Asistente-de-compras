from __future__ import annotations

from app.agents.state import AgentState


def supervisor(state: AgentState) -> dict:
    pasos = state.get("pasos", [])
    ya_busco = any(paso.startswith("buscador:") for paso in pasos)

    if not state.get("opciones"):
        next_step = "fin" if (state.get("errores") or ya_busco) else "buscar"
    elif state.get("resumen_precios") is None:
        next_step = "precios"
    elif state.get("resumen_resenas") is None:
        next_step = "resenas"
    elif state.get("resumen_audiencia") is None:
        next_step = "audiencia"
    elif state.get("resultado") is None:
        next_step = "sintetizar"
    else:
        next_step = "fin"

    return {
        "siguiente": next_step,
        "pasos": [*pasos, f"supervisor:{next_step}"],
    }


def route_from_supervisor(state: AgentState) -> str:
    return state.get("siguiente", "fin")
