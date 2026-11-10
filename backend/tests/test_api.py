from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes import get_repository
from app.db.models import Base
from app.db.repository import ResultadoRepository
from app.main import app
from app.models import (
    AnalysisResult,
    AudienceProfile,
    AudienceSummary,
    PriceSummary,
    ProductOption,
    ReviewSummary,
    Store,
)

client = TestClient(app)


def temp_repository(tmp_path) -> ResultadoRepository:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'api.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )
    return ResultadoRepository(session_factory)


def sample_result() -> AnalysisResult:
    options = [
        ProductOption(
            nombre="Laptop A",
            comercio=Store.walmart,
            precio=Decimal("12000.00"),
        ),
        ProductOption(
            nombre="Laptop B",
            comercio=Store.costco,
            precio=Decimal("13500.50"),
        ),
    ]
    return AnalysisResult(
        producto="laptop",
        tiendas=list(Store),
        opciones=options,
        resumen_precios=PriceSummary(
            precio_final=Decimal("12000.00"),
            opcion_recomendada="Laptop A",
            precio_promedio=Decimal("12750.25"),
            precio_minimo=Decimal("12000.00"),
            precio_maximo=Decimal("13500.50"),
            rango=Decimal("1500.50"),
            moneda="MXN",
            opciones_consideradas=2,
            comercio_mas_barato="Walmart",
            comercio_mas_caro="Costco",
        ),
        resumen_resenas=ReviewSummary(
            score=7.5,
            resenas_analizadas=3,
            sintesis="Opiniones positivas.",
            pros=["Buen precio"],
            contras=["Peso"],
            fuentes=["Walmart", "Costco"],
        ),
        usuarios_relevantes=AudienceSummary(
            perfiles=[
                AudienceProfile(
                    perfil="Estudiante",
                    descripcion="Buena opción.",
                    porcentaje=80,
                )
            ],
            sintesis="Perfil principal: estudiante.",
        ),
        recomendacion="Recomendación de prueba.",
        filas_guardadas=2,
        fecha_consulta=datetime(2026, 11, 8, 12, 0, 0),
    )


def sample_state() -> dict:
    return {
        "resultado": sample_result(),
        "pasos": [
            "supervisor:buscar",
            "sintetizar:ok",
            "validar:ok",
            "persistir:2 filas",
        ],
        "errores": [],
        "advertencias": [],
        "filas_guardadas": 2,
    }


def test_analyze_returns_result(monkeypatch) -> None:
    monkeypatch.setattr("app.api.routes.run_analysis", lambda **kwargs: sample_state())

    response = client.post(
        "/api/analyze",
        json={
            "producto": "laptop",
            "limite_por_tienda": 2,
            "usar_llm": False,
            "guardar": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["resultado"]["producto"] == "laptop"
    assert body["filas_guardadas"] == 2
    assert "persistir:2 filas" in body["pasos"]


def test_analyze_returns_502_without_result(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.run_analysis",
        lambda **kwargs: {
            "resultado": None,
            "errores": ["sin resultados"],
            "pasos": [],
        },
    )

    response = client.post("/api/analyze", json={"producto": "producto raro"})

    assert response.status_code == 502
    assert response.json()["detail"]["errores"] == ["sin resultados"]


def test_history_and_stats(tmp_path) -> None:
    repo = temp_repository(tmp_path)
    repo.save_result(sample_result())
    app.dependency_overrides[get_repository] = lambda: repo
    try:
        history = client.get(
            "/api/history",
            params={"limit": 10, "producto": "laptop"},
        )
        assert history.status_code == 200
        rows = history.json()
        assert len(rows) == 2
        assert {row["comercio"] for row in rows} == {"Walmart", "Costco"}

        stats = client.get("/api/stats", params={"producto": "laptop"})
        assert stats.status_code == 200
        data = stats.json()
        assert data["total"] == 2
        assert Decimal(data["precio_minimo"]) == Decimal("12000.00")
        assert Decimal(data["precio_maximo"]) == Decimal("13500.50")
        assert len(data["por_comercio"]) == 2
    finally:
        app.dependency_overrides.pop(get_repository, None)


def test_history_validates_limit() -> None:
    app.dependency_overrides[get_repository] = lambda: None
    try:
        response = client.get("/api/history", params={"limit": 0})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_repository, None)


class FakeGraph:
    def stream(self, state, stream_mode="updates"):
        yield {
            "supervisor": {
                "siguiente": "buscar",
                "pasos": ["supervisor:buscar"],
            }
        }
        yield {
            "buscar": {
                "opciones": sample_result().opciones,
                "pasos": ["buscador:2 opciones"],
            }
        }
        yield {
            "sintetizar": {
                "resultado": sample_result(),
                "pasos": ["sintetizar:ok"],
            }
        }
        yield {"validar": {"advertencias": [], "pasos": ["validar:ok"]}}
        yield {"persistir": {"filas_guardadas": 2, "pasos": ["persistir:2 filas"]}}


def test_analyze_stream_emits_done(monkeypatch) -> None:
    monkeypatch.setattr("app.api.routes.build_graph", lambda **kwargs: FakeGraph())

    response = client.post(
        "/api/analyze/stream",
        json={
            "producto": "laptop",
            "limite_por_tienda": 2,
            "usar_llm": False,
            "guardar": False,
        },
    )

    assert response.status_code == 200
    assert '"event": "done"' in response.text
    assert "Recomendación de prueba." in response.text


def test_analyze_validates_empty_product_and_limit() -> None:
    empty_product = client.post("/api/analyze", json={"producto": ""})
    assert empty_product.status_code == 422

    invalid_limit = client.post(
        "/api/analyze",
        json={"producto": "laptop", "limite_por_tienda": 11},
    )
    assert invalid_limit.status_code == 422


def test_history_rejects_empty_product_filter() -> None:
    app.dependency_overrides[get_repository] = lambda: None
    try:
        response = client.get("/api/history", params={"producto": ""})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_repository, None)


class FailingGraph:
    def stream(self, state, stream_mode="updates"):
        raise RuntimeError("fallo de stream")


def test_analyze_stream_emits_error(monkeypatch) -> None:
    monkeypatch.setattr("app.api.routes.build_graph", lambda **kwargs: FailingGraph())

    response = client.post(
        "/api/analyze/stream",
        json={
            "producto": "laptop",
            "limite_por_tienda": 2,
            "usar_llm": False,
            "guardar": False,
        },
    )

    assert response.status_code == 200
    assert '"event": "error"' in response.text
    assert "fallo de stream" in response.text


def test_analyze_stream_returns_500_when_graph_cannot_be_built(monkeypatch) -> None:
    def failing_build_graph(**kwargs):
        raise RuntimeError("graph caido")

    monkeypatch.setattr("app.api.routes.build_graph", failing_build_graph)

    response = client.post(
        "/api/analyze/stream",
        json={"producto": "laptop", "usar_llm": False, "guardar": False},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "graph caido"


def test_get_repository_uses_cached_factory(monkeypatch) -> None:
    get_repository.cache_clear()
    monkeypatch.setattr(
        "app.api.routes.build_default_repository",
        lambda: "repositorio",
    )

    assert get_repository() == "repositorio"
    assert get_repository() == "repositorio"

    get_repository.cache_clear()
