from __future__ import annotations

from typing import Any, Callable

from app.agents.state import AgentState
from app.models import ProductQuery, Store


def make_search_agent(service: Any) -> Callable[[AgentState], dict]:
    def search_agent(state: AgentState) -> dict:
        tiendas = state.get("tiendas") or list(Store)
        query = ProductQuery(
            producto=state["consulta"],
            tiendas=tiendas,
            limite_por_tienda=state.get("limite_por_tienda", 3),
        )
        try:
            result = service.search(query)
        except Exception as exc:
            return {
                "opciones": [],
                "errores": [*state.get("errores", []), f"búsqueda: {exc}"],
                "pasos": [*state.get("pasos", []), "buscador:error"],
            }

        return {
            "opciones": result.opciones,
            "errores": [*state.get("errores", []), *result.errores],
            "tiendas_con_mock": result.tiendas_con_mock,
            "pasos": [*state.get("pasos", []), f"buscador:{len(result.opciones)} opciones"],
        }

    return search_agent
