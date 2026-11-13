from decimal import Decimal

from app.bot.parser import parse_request
from app.models import Store


def test_parse_full_request() -> None:
    parsed = parse_request(
        "Busca una laptop para la universidad, máximo 15000, en Walmart y Costco"
    )

    assert parsed.producto == "laptop"
    assert parsed.tiendas == [Store.walmart, Store.costco]
    assert parsed.presupuesto == Decimal("15000.00")
    assert parsed.presupuesto_mencionado is True
    assert parsed.perfil == "estudiante"
    assert parsed.perfil_mencionado is True


def test_parse_short_product() -> None:
    parsed = parse_request("busca audifonos bluetooth")

    assert parsed.producto == "audifonos bluetooth"
    assert parsed.tiendas is None
    assert parsed.presupuesto is None


def test_parse_budget_suffixes() -> None:
    assert parse_request("laptop 15k").presupuesto == Decimal("15000")
    assert parse_request("laptop 20,000 pesos").presupuesto == Decimal("20000.00")
    assert parse_request("laptop hasta 12.5 mil").presupuesto == Decimal("12500.0")


def test_parse_sin_limite_clears_budget() -> None:
    parsed = parse_request("sin limite")

    assert parsed.presupuesto is None
    assert parsed.presupuesto_mencionado is True
    assert parsed.producto is None


def test_parse_profile_answer() -> None:
    for text, expected in [
        ("para estudiante", "estudiante"),
        ("para gamer", "gamer"),
        ("hogar", "hogar"),
        ("profesional", "profesional"),
    ]:
        parsed = parse_request(text)
        assert parsed.perfil == expected
        assert parsed.perfil_mencionado is True


def test_parse_all_stores_and_limit() -> None:
    parsed = parse_request("laptop en las tres tiendas limite 5")

    assert parsed.producto == "laptop"
    assert parsed.tiendas == list(Store)
    assert parsed.limite == 5


def test_parse_does_not_treat_casa_as_profile() -> None:
    parsed = parse_request("busca una casa de campaña")

    assert parsed.producto == "casa de campana"
    assert parsed.perfil is None


def test_parse_empty_message() -> None:
    parsed = parse_request("   ")

    assert parsed.producto is None
    assert "mensaje vacio" in parsed.notas
