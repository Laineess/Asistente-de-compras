import json

from app.agents.review_agent import heuristic_review
from app.graph import build_graph, run_analysis
from app.models import ProductOption, ProductQuery, ReviewSnippet, SearchResult, Store
from app.providers.mock_provider import MockProvider
from app.providers.service import ProductSearchService


def mock_service() -> ProductSearchService:
    providers = {store: MockProvider(store) for store in Store}
    return ProductSearchService(providers=providers, fallback_providers=providers)


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeLLM:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> FakeMessage:
        self.prompts.append(prompt)
        if not self.responses:
            raise RuntimeError("sin respuestas configuradas")
        return FakeMessage(self.responses.pop(0))


class EmptyService:
    def search(self, query: ProductQuery) -> SearchResult:
        return SearchResult(
            opciones=[],
            errores=["sin resultados"],
            tiendas_con_mock=[],
        )


def test_graph_runs_without_llm() -> None:
    state = run_analysis(
        "laptop",
        limite_por_tienda=2,
        service=mock_service(),
        use_llm=False,
        persist=False,
    )
    result = state["resultado"]

    assert result is not None
    assert result.recomendacion
    assert result.resumen_precios is not None
    assert result.resumen_resenas is not None
    assert result.resumen_resenas.resenas_analizadas >= 3
    assert result.usuarios_relevantes is not None
    assert len(result.usuarios_relevantes.perfiles) >= 4
    assert any(step.startswith("buscador:") for step in state["pasos"])
    assert any(step.startswith("sintetizar:") for step in state["pasos"])
    assert any(step.startswith("validar:") for step in state["pasos"])
    assert "persistir:omitido" in state["pasos"]


def test_graph_uses_llm_outputs() -> None:
    fake = FakeLLM(
        [
            json.dumps(
                {
                    "score": 8.2,
                    "resenas_analizadas": 6,
                    "sintesis": "Opiniones mayormente positivas.",
                    "pros": [
                        "Buen rendimiento",
                        "Precio competitivo",
                        "Diseño cuidado",
                    ],
                    "contras": [
                        "Batería mejorable",
                        "Peso alto",
                        "Pocos puertos",
                    ],
                }
            ),
            json.dumps(
                {
                    "perfiles": [
                        {
                            "perfil": "Estudiante",
                            "descripcion": "Buena relación precio-beneficio.",
                            "evidencia": "Opción económica.",
                            "porcentaje": 90,
                        },
                        {
                            "perfil": "Profesional",
                            "descripcion": "Suficiente para oficina.",
                            "evidencia": "16 GB RAM.",
                            "porcentaje": 80,
                        },
                        {
                            "perfil": "Gamer",
                            "descripcion": "No es la mejor opción.",
                            "evidencia": "Sin GPU dedicada.",
                            "porcentaje": 40,
                        },
                        {
                            "perfil": "Hogar",
                            "descripcion": "Uso general.",
                            "evidencia": "Buen precio.",
                            "porcentaje": 75,
                        },
                    ],
                    "sintesis": "Recomendaciones por perfil.",
                }
            ),
            "Recomendación final generada por el LLM.",
        ]
    )

    state = run_analysis(
        "laptop",
        limite_por_tienda=2,
        service=mock_service(),
        llm=fake,
        use_llm=True,
        persist=False,
    )
    result = state["resultado"]

    assert result is not None
    assert result.recomendacion == "Recomendación final generada por el LLM."
    assert result.resumen_resenas is not None
    assert result.resumen_resenas.score == 8.2
    assert result.usuarios_relevantes is not None
    assert len(result.usuarios_relevantes.perfiles) >= 4
    assert len(fake.prompts) == 3


def test_graph_stops_when_no_options() -> None:
    state = run_analysis(
        "producto raro",
        service=EmptyService(),
        use_llm=False,
        persist=False,
    )

    assert state["resultado"] is None
    assert state["errores"]
    assert "supervisor:fin" in state["pasos"]


def test_build_graph_builds_default_llm_and_repository(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "app.graph.builder.build_llm",
        lambda: calls.append("llm") or None,
    )
    monkeypatch.setattr(
        "app.graph.builder.build_default_repository",
        lambda: calls.append("repository") or None,
    )

    graph = build_graph(service=mock_service(), use_llm=True, persist=True)

    assert calls == ["llm", "repository"]
    assert graph is not None


def test_heuristic_review_extracts_pros_and_cons() -> None:
    option = ProductOption(
        nombre="Laptop de prueba",
        comercio=Store.walmart,
        precio=10000,
        resenas=[
            ReviewSnippet(
                texto="Buena por el precio, aunque el almacenamiento se llena rápido."
            ),
            ReviewSnippet(texto="Ligera y con buen teclado para escribir."),
            ReviewSnippet(texto="La batería dura todo el día."),
        ],
    )

    summary = heuristic_review([option])

    assert summary.resenas_analizadas >= 3
    assert any("precio" in pro.lower() for pro in summary.pros)
    assert any("almacenamiento" in contra.lower() for contra in summary.contras)
