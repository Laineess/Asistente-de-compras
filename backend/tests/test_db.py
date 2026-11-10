from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.persistence_agent import make_persistence_agent
from app.db.models import Base
from app.db.repository import ResultadoRepository
from app.graph import run_analysis
from app.models import AnalysisResult, ProductOption, Store
from app.providers.mock_provider import MockProvider
from app.providers.service import ProductSearchService


def temp_repository(tmp_path) -> ResultadoRepository:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
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


def mock_service() -> ProductSearchService:
    providers = {store: MockProvider(store) for store in Store}
    return ProductSearchService(providers=providers, fallback_providers=providers)


def sample_result() -> AnalysisResult:
    return AnalysisResult(
        producto="laptop",
        tiendas=list(Store),
        opciones=[
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
        ],
        fecha_consulta=datetime(2026, 11, 8, 12, 0, 0),
    )


def test_repository_saves_one_row_per_option(tmp_path) -> None:
    repo = temp_repository(tmp_path)
    saved = repo.save_result(sample_result())

    assert saved == 2
    assert repo.count() == 2
    rows = repo.list_resultados()
    assert len(rows) == 2
    assert {row.comercio for row in rows} == {"Walmart", "Costco"}
    assert {float(row.precio) for row in rows} == {12000.0, 13500.5}
    assert all(row.fecha_consulta == datetime(2026, 11, 8, 12, 0, 0) for row in rows)


def test_repository_clear(tmp_path) -> None:
    repo = temp_repository(tmp_path)
    repo.save_result(sample_result())

    assert repo.clear() == 2
    assert repo.count() == 0


def test_persistence_agent_skips_without_result() -> None:
    agent = make_persistence_agent(None)

    state = agent({})

    assert state["filas_guardadas"] == 0
    assert state["pasos"] == ["persistir:sin-resultado"]


def test_persistence_agent_handles_repository_error() -> None:
    class FailingRepository:
        def save_result(self, result: AnalysisResult) -> int:
            raise RuntimeError("db caida")

    agent = make_persistence_agent(FailingRepository())
    state = agent(
        {
            "resultado": sample_result(),
            "advertencias": [],
            "errores": [],
            "pasos": [],
        }
    )

    assert state["filas_guardadas"] == 0
    assert "persistir:error" in state["pasos"]
    assert any("base de datos" in warning for warning in state["advertencias"])
    assert any("persistencia" in error for error in state["errores"])


def test_graph_persists_result(tmp_path) -> None:
    repo = temp_repository(tmp_path)
    state = run_analysis(
        "laptop",
        limite_por_tienda=2,
        service=mock_service(),
        use_llm=False,
        repository=repo,
        persist=True,
    )
    result = state["resultado"]

    assert result is not None
    assert result.filas_guardadas == len(result.opciones)
    assert state["filas_guardadas"] == len(result.opciones)
    assert any(step.startswith("persistir:") for step in state["pasos"])
    assert repo.count() == len(result.opciones)
