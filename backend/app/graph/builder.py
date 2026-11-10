from __future__ import annotations

from decimal import Decimal
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from app.agents import (
    AgentState,
    initial_state,
    make_audience_agent,
    make_persistence_agent,
    make_review_agent,
    make_search_agent,
    make_synthesis_agent,
    price_agent,
    route_from_supervisor,
    supervisor,
    validator,
)
from app.db.repository import ResultadoRepository, build_default_repository
from app.llm import build_llm
from app.models import Store
from app.providers.factory import build_default_service


def build_graph(
    service: Any | None = None,
    llm: BaseChatModel | None = None,
    use_llm: bool = True,
    repository: ResultadoRepository | None = None,
    persist: bool = True,
):
    search_service = service or build_default_service()
    model = llm if use_llm else None
    if use_llm and model is None:
        model = build_llm()

    persistence_repository = repository
    if persist and persistence_repository is None:
        persistence_repository = build_default_repository()

    graph = StateGraph(AgentState)
    graph.add_node("supervisor", supervisor)
    graph.add_node("buscar", make_search_agent(search_service))
    graph.add_node("precios", price_agent)
    graph.add_node("resenas", make_review_agent(model))
    graph.add_node("audiencia", make_audience_agent(model))
    graph.add_node("sintetizar", make_synthesis_agent(model))
    graph.add_node("validar", validator)
    graph.add_node(
        "persistir",
        make_persistence_agent(persistence_repository, enabled=persist),
    )

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "buscar": "buscar",
            "precios": "precios",
            "resenas": "resenas",
            "audiencia": "audiencia",
            "sintetizar": "sintetizar",
            "fin": END,
        },
    )
    graph.add_edge("buscar", "supervisor")
    graph.add_edge("precios", "supervisor")
    graph.add_edge("resenas", "supervisor")
    graph.add_edge("audiencia", "supervisor")
    graph.add_edge("sintetizar", "validar")
    graph.add_edge("validar", "persistir")
    graph.add_edge("persistir", END)
    return graph.compile()


def run_analysis(
    consulta: str,
    limite_por_tienda: int = 3,
    perfil: str | None = None,
    tiendas: list[Store] | None = None,
    presupuesto: Decimal | None = None,
    service: Any | None = None,
    llm: BaseChatModel | None = None,
    use_llm: bool = True,
    repository: ResultadoRepository | None = None,
    persist: bool = True,
) -> AgentState:
    graph = build_graph(
        service=service,
        llm=llm,
        use_llm=use_llm,
        repository=repository,
        persist=persist,
    )
    state = initial_state(
        consulta=consulta,
        limite_por_tienda=limite_por_tienda,
        perfil=perfil,
        tiendas=tiendas,
        presupuesto=presupuesto,
    )
    return graph.invoke(state)
