from decimal import Decimal

from app.agents.audience_agent import heuristic_audience, make_audience_agent
from app.agents.price_agent import price_agent
from app.agents.search_agent import make_search_agent
from app.agents.supervisor import route_from_supervisor, supervisor
from app.agents.synthesis_agent import fallback_recommendation, make_synthesis_agent
from app.agents.validator import validator
from app.models import (
    AnalysisResult,
    AudienceProfile,
    AudienceSummary,
    PriceSummary,
    ProductOption,
    ReviewSummary,
    Store,
)


def make_option(
    nombre: str,
    comercio: Store,
    precio: str,
    *,
    calificacion: float | None = None,
    descripcion: str | None = None,
    fuente: str = "mock",
) -> ProductOption:
    return ProductOption(
        nombre=nombre,
        comercio=comercio,
        precio=Decimal(precio),
        calificacion=calificacion,
        descripcion=descripcion,
        fuente=fuente,
    )


def sample_options() -> list[ProductOption]:
    return [
        make_option(
            "Laptop basica",
            Store.walmart,
            "100.00",
            calificacion=4.0,
            descripcion="8 GB RAM 256 GB SSD",
        ),
        make_option(
            "Laptop pro",
            Store.costco,
            "300.00",
            calificacion=4.8,
            descripcion="16 GB RAM 1 TB SSD RTX",
        ),
        make_option(
            "Laptop gamer",
            Store.sams,
            "250.00",
            calificacion=4.5,
            descripcion="32 GB RAM 2 TB SSD RTX 4070",
        ),
    ]


def sample_price_summary() -> PriceSummary:
    return PriceSummary(
        precio_final=Decimal("100.00"),
        opcion_recomendada="Laptop basica",
        precio_promedio=Decimal("216.67"),
        precio_minimo=Decimal("100.00"),
        precio_maximo=Decimal("300.00"),
        rango=Decimal("200.00"),
        opciones_consideradas=3,
        comercio_mas_barato="Walmart",
        comercio_mas_caro="Costco",
    )


def sample_review_summary() -> ReviewSummary:
    return ReviewSummary(
        score=8.0,
        resenas_analizadas=3,
        sintesis="Opiniones mayormente positivas.",
        pros=["Buen precio"],
        contras=["Peso"],
        fuentes=["Walmart", "Costco"],
    )


def test_price_agent_without_options() -> None:
    updated = price_agent({"opciones": [], "errores": [], "pasos": []})

    assert updated["resumen_precios"] is None
    assert updated["errores"] == ["No hay opciones para calcular precios."]
    assert updated["pasos"] == ["precios:sin-opciones"]


def test_price_agent_calculates_summary() -> None:
    updated = price_agent({"opciones": sample_options(), "errores": [], "pasos": []})
    summary = updated["resumen_precios"]

    assert summary is not None
    assert summary.precio_final == Decimal("100.00")
    assert summary.opcion_recomendada == "Laptop basica"
    assert summary.precio_promedio == Decimal("216.67")
    assert summary.precio_minimo == Decimal("100.00")
    assert summary.precio_maximo == Decimal("300.00")
    assert summary.rango == Decimal("200.00")
    assert summary.comercio_mas_barato == "Walmart"
    assert summary.comercio_mas_caro == "Costco"
    assert updated["pasos"] == ["precios:ok"]


def test_price_agent_filters_options_over_budget() -> None:
    updated = price_agent(
        {
            "opciones": sample_options(),
            "presupuesto": Decimal("260.00"),
            "errores": [],
            "advertencias": [],
            "pasos": [],
        }
    )
    summary = updated["resumen_precios"]

    assert summary is not None
    assert summary.precio_final == Decimal("100.00")
    assert summary.precio_maximo == Decimal("250.00")
    assert summary.precio_promedio == Decimal("175.00")
    assert summary.opciones_consideradas == 2
    assert summary.presupuesto == Decimal("260.00")
    assert summary.opciones_dentro_presupuesto == 2
    assert any("1 opción" in warning for warning in updated["advertencias"])


def test_price_agent_warns_when_budget_excludes_all_options() -> None:
    updated = price_agent(
        {
            "opciones": sample_options(),
            "presupuesto": Decimal("50.00"),
            "errores": [],
            "advertencias": [],
            "pasos": [],
        }
    )
    summary = updated["resumen_precios"]

    assert summary is not None
    assert summary.precio_final == Decimal("100.00")
    assert summary.opciones_consideradas == 3
    assert summary.presupuesto == Decimal("50.00")
    assert summary.opciones_dentro_presupuesto == 0
    assert any("Ninguna opción" in warning for warning in updated["advertencias"])


def test_supervisor_routes_in_order_and_handles_empty_results() -> None:
    assert supervisor({"opciones": [], "errores": [], "pasos": []})["siguiente"] == "buscar"
    assert (
        supervisor({"opciones": [], "errores": ["fallo"], "pasos": []})["siguiente"]
        == "fin"
    )
    assert (
        supervisor(
            {"opciones": [], "errores": [], "pasos": ["buscador:0 opciones"]}
        )["siguiente"]
        == "fin"
    )

    options = sample_options()
    assert supervisor({"opciones": options, "pasos": []})["siguiente"] == "precios"
    assert (
        supervisor(
            {
                "opciones": options,
                "resumen_precios": sample_price_summary(),
                "pasos": [],
            }
        )["siguiente"]
        == "resenas"
    )
    assert (
        supervisor(
            {
                "opciones": options,
                "resumen_precios": sample_price_summary(),
                "resumen_resenas": sample_review_summary(),
                "pasos": [],
            }
        )["siguiente"]
        == "audiencia"
    )
    assert (
        supervisor(
            {
                "opciones": options,
                "resumen_precios": sample_price_summary(),
                "resumen_resenas": sample_review_summary(),
                "resumen_audiencia": AudienceSummary(perfiles=[]),
                "pasos": [],
            }
        )["siguiente"]
        == "sintetizar"
    )
    assert (
        supervisor(
            {
                "opciones": options,
                "resumen_precios": sample_price_summary(),
                "resumen_resenas": sample_review_summary(),
                "resumen_audiencia": AudienceSummary(perfiles=[]),
                "resultado": AnalysisResult(producto="laptop", tiendas=[]),
                "pasos": [],
            }
        )["siguiente"]
        == "fin"
    )
    assert route_from_supervisor({"siguiente": "resenas"}) == "resenas"
    assert route_from_supervisor({}) == "fin"


def test_validator_adds_and_deduplicates_warnings() -> None:
    result = AnalysisResult(
        producto="laptop",
        tiendas=[Store.walmart],
        opciones=[make_option("Laptop", Store.walmart, "100.00")],
        resumen_resenas=None,
        errores=["fallo parcial"],
        advertencias=["Aviso existente", "Aviso existente"],
    )
    updated = validator(
        {
            "resultado": result,
            "advertencias": ["Aviso existente"],
            "pasos": [],
        }
    )
    warnings = updated["advertencias"]

    assert warnings[0] == "Aviso existente"
    assert len(warnings) == len(set(warnings))
    assert any("1 de 3 tiendas" in warning for warning in warnings)
    assert any("3 reseñas" in warning for warning in warnings)
    assert any("mock" in warning for warning in warnings)
    assert any("errores parciales" in warning for warning in warnings)
    assert updated["resultado"].advertencias == warnings
    assert updated["pasos"] == ["validar:ok"]


def test_validator_without_result() -> None:
    assert validator({"resultado": None, "pasos": []}) == {
        "pasos": ["validar:sin-resultado"]
    }


def test_heuristic_audience_without_options() -> None:
    summary = heuristic_audience([], None, None)

    assert summary.perfiles == []
    assert summary.sintesis == "No hay opciones para recomendar."


def test_heuristic_audience_builds_profiles() -> None:
    summary = heuristic_audience(
        sample_options(),
        sample_price_summary(),
        sample_review_summary(),
    )

    assert {profile.perfil for profile in summary.perfiles} == {
        "Estudiante",
        "Profesional",
        "Gamer",
        "Hogar",
    }
    assert all(profile.porcentaje is not None for profile in summary.perfiles)
    assert "Laptop basica" in summary.sintesis
    assert "Score de reseñas: 8.0/10" in summary.sintesis


def test_audience_agent_adds_requested_profile() -> None:
    agent = make_audience_agent(None)
    updated = agent(
        {
            "opciones": sample_options(),
            "resumen_precios": sample_price_summary(),
            "resumen_resenas": sample_review_summary(),
            "perfil": "Docente",
            "pasos": [],
        }
    )
    summary = updated["resumen_audiencia"]

    assert any(profile.perfil == "Docente" for profile in summary.perfiles)
    assert updated["pasos"] == ["audiencia:ok"]


def test_fallback_recommendation_mentions_cheapest_and_mock_data() -> None:
    text = fallback_recommendation(
        {
            "opciones": sample_options(),
            "resumen_precios": sample_price_summary(),
            "resumen_resenas": sample_review_summary(),
            "resumen_audiencia": AudienceSummary(
                perfiles=[
                    AudienceProfile(
                        perfil="Estudiante",
                        descripcion="Mejor precio.",
                    )
                ],
                sintesis="Perfil principal: estudiante.",
            ),
            "tiendas_con_mock": [Store.walmart],
        }
    )

    assert "Laptop basica en Walmart" in text
    assert "Por perfil: Perfil principal: estudiante." in text
    assert "catálogo de respaldo" in text


def test_synthesis_agent_builds_result() -> None:
    agent = make_synthesis_agent(None)
    updated = agent(
        {
            "consulta": "laptop",
            "tiendas": [Store.walmart, Store.costco, Store.sams],
            "opciones": sample_options(),
            "resumen_precios": sample_price_summary(),
            "resumen_resenas": sample_review_summary(),
            "resumen_audiencia": AudienceSummary(
                perfiles=[
                    AudienceProfile(
                        perfil="Estudiante",
                        descripcion="Mejor precio.",
                    )
                ],
                sintesis="Perfil principal: estudiante.",
            ),
            "advertencias": ["Aviso"],
            "errores": ["Error"],
            "pasos": [],
        }
    )
    result = updated["resultado"]

    assert result is not None
    assert result.producto == "laptop"
    assert result.recomendacion.startswith("Recomendación:")
    assert result.advertencias == ["Aviso"]
    assert result.errores == ["Error"]
    assert updated["pasos"] == ["sintetizar:ok"]


def test_search_agent_handles_service_error() -> None:
    class FailingService:
        def search(self, query):
            raise RuntimeError("servicio caido")

    agent = make_search_agent(FailingService())
    updated = agent(
        {
            "consulta": "laptop",
            "tiendas": [Store.walmart],
            "limite_por_tienda": 1,
            "errores": [],
            "pasos": [],
        }
    )

    assert updated["opciones"] == []
    assert updated["errores"] == ["búsqueda: servicio caido"]
    assert updated["pasos"] == ["buscador:error"]


def test_product_option_exposes_store_display_name() -> None:
    option = make_option("Laptop", Store.sams, "100.00")

    assert option.comercio_nombre == "Sam's"
