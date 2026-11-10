from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.persistence_agent import make_persistence_agent
from app.db import session as db_session
from app.db.models import Base
from app.db.repository import ResultadoRepository, build_default_repository
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


def other_result() -> AnalysisResult:
    return AnalysisResult(
        producto="tablet",
        tiendas=[Store.sams],
        opciones=[
            ProductOption(
                nombre="Tablet C",
                comercio=Store.sams,
                precio=Decimal("5000.00"),
            )
        ],
        fecha_consulta=datetime(2026, 11, 9, 12, 0, 0),
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


def test_repository_filters_and_stats(tmp_path) -> None:
    repo = temp_repository(tmp_path)
    repo.save_result(sample_result())
    repo.save_result(other_result())

    filtered = repo.list_resultados(producto="LAPTOP")
    assert len(filtered) == 2
    assert all("Laptop" in row.nombre_producto for row in filtered)

    assert len(repo.list_resultados(limit=1)) == 1

    stats = repo.stats()
    assert stats["total"] == 3
    assert stats["precio_minimo"] == Decimal("5000.00")
    assert stats["precio_maximo"] == Decimal("13500.50")
    assert Decimal(str(stats["precio_promedio"])).quantize(
        Decimal("0.01")
    ) == Decimal("10166.83")
    assert len(stats["por_comercio"]) == 3

    laptop_stats = repo.stats(producto="laptop")
    assert laptop_stats["total"] == 2
    assert laptop_stats["precio_minimo"] == Decimal("12000.00")
    assert len(laptop_stats["por_comercio"]) == 2


def test_repository_stats_without_data(tmp_path) -> None:
    repo = temp_repository(tmp_path)

    assert repo.stats() == {
        "total": 0,
        "precio_minimo": None,
        "precio_maximo": None,
        "precio_promedio": None,
        "por_comercio": [],
    }


def test_repository_save_result_without_options(tmp_path) -> None:
    repo = temp_repository(tmp_path)
    result = AnalysisResult(producto="vacio", tiendas=[], opciones=[])

    assert repo.save_result(result) == 0
    assert repo.count() == 0


def test_build_default_repository_initializes_database(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr("app.db.repository.init_db", lambda: calls.append("init"))

    repo = build_default_repository()

    assert calls == ["init"]
    assert isinstance(repo, ResultadoRepository)


def test_init_db_creates_tables(monkeypatch) -> None:
    calls: list[object] = []

    class FakeMetadata:
        def create_all(self, bind) -> None:
            calls.append(bind)

    monkeypatch.setattr(db_session.Base, "metadata", FakeMetadata())

    db_session.init_db()

    assert calls == [db_session.engine]


def test_get_session_yields_and_closes_session(monkeypatch) -> None:
    class FakeSession:
        closed = False

        def close(self) -> None:
            self.closed = True

    fake = FakeSession()
    monkeypatch.setattr(db_session, "SessionLocal", lambda: fake)
    generator = db_session.get_session()

    assert next(generator) is fake
    with pytest.raises(StopIteration):
        next(generator)
    assert fake.closed
