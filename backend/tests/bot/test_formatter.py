from decimal import Decimal

from app.bot.conversation import Session
from app.bot.formatter import (
    format_results,
    group_options,
    split_message,
    top_groups,
)
from app.models import AnalysisResult, PriceSummary, ProductOption, Store


def _option(
    name: str,
    store: Store,
    price: str,
    url: str | None = "https://example.com/producto",
) -> ProductOption:
    return ProductOption(
        nombre=name,
        comercio=store,
        precio=Decimal(price),
        url=url,
        descripcion="Producto de prueba para el analisis de resenas.",
    )


def _result() -> AnalysisResult:
    return AnalysisResult(
        producto="laptop",
        tiendas=[Store.walmart, Store.costco, Store.sams],
        opciones=[
            _option("Laptop Lenovo IdeaPad 3", Store.walmart, "12000"),
            _option("Laptop Lenovo IdeaPad 3", Store.costco, "11800"),
            _option("Laptop HP Pavilion 15", Store.walmart, "14000"),
            _option("Laptop ASUS Vivobook 15", Store.sams, "9500"),
        ],
        resumen_precios=PriceSummary(
            precio_final=Decimal("11800"),
            opcion_recomendada="Laptop Lenovo IdeaPad 3",
            precio_promedio=Decimal("11825"),
            precio_minimo=Decimal("9500"),
            precio_maximo=Decimal("14000"),
            rango=Decimal("4500"),
            opciones_consideradas=4,
            comercio_mas_barato="Sam's",
            comercio_mas_caro="Walmart",
            presupuesto=Decimal("15000"),
            opciones_dentro_presupuesto=4,
        ),
        recomendacion="La Lenovo ofrece el mejor equilibrio.",
    )


def test_group_options_merges_same_product() -> None:
    groups = group_options(_result().opciones)

    lenovo = next(group for group in groups if "Lenovo" in group.nombre)
    assert len(lenovo.opciones) == 2
    assert len(groups) == 3


def test_top_groups_puts_recommended_first() -> None:
    groups = top_groups(_result(), limit=3)

    assert [group.nombre for group in groups] == [
        "Laptop Lenovo IdeaPad 3",
        "Laptop ASUS Vivobook 15",
        "Laptop HP Pavilion 15",
    ]


def test_format_results_includes_links_and_top3() -> None:
    session = Session(user_id=1, chat_id=2, producto="laptop")
    reply = format_results(_result(), session)
    text = "\n".join(reply.messages)

    assert "Top 3" in text
    assert "Lenovo" in text
    assert "ASUS" in text
    assert "HP" in text
    assert "https://example.com/producto" in text
    assert "Recomendado" in text
    assert "Enlaces encontrados" in text
    assert len(reply.audio_scripts) == 3


def test_format_results_without_options() -> None:
    result = AnalysisResult(
        producto="laptop",
        tiendas=[Store.walmart],
        errores=["sin opciones"],
    )
    reply = format_results(result, Session(user_id=1, chat_id=2))

    assert len(reply.messages) == 1
    assert "Sin resultados" in reply.messages[0]
    assert "sin opciones" in reply.messages[0]


def test_format_results_ignores_unsafe_url() -> None:
    result = _result()
    result.opciones[0].url = "javascript:alert(1)"
    reply = format_results(result, Session(user_id=1, chat_id=2))
    text = "\n".join(reply.messages)

    assert "javascript:" not in text


def test_split_message_respects_limit_and_keeps_lines() -> None:
    text = "\n".join(f"linea {index} " + "x" * 80 for index in range(20))

    chunks = split_message(text, limit=300)

    assert len(chunks) > 1
    assert all(len(chunk) <= 300 for chunk in chunks)
    assert all(chunk.strip() for chunk in chunks)
    assert "linea 0" in chunks[0]
    assert "linea 19" in chunks[-1]
