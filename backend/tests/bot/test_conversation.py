from decimal import Decimal

import pytest

from app.bot.conversation import (
    CANCELLED,
    COLLECTING,
    CONFIRMING,
    ConversationManager,
)
from app.models import Store


def test_new_session_defaults() -> None:
    manager = ConversationManager(default_mode="fast", default_voice="auto")
    session = manager.new_session(user_id=1, chat_id=2)

    assert session.producto is None
    assert session.estado == "idle"
    assert session.tiendas == list(Store)
    assert session.modo == "fast"
    assert session.voz == "auto"


def test_apply_text_builds_confirmation() -> None:
    manager = ConversationManager()
    session = manager.new_session(1, 2)

    session, parsed = manager.apply_text(
        session,
        "laptop para estudiante máximo 15000 en Walmart",
    )

    assert parsed.producto == "laptop"
    assert session.estado == CONFIRMING
    assert session.producto == "laptop"
    assert session.perfil == "estudiante"
    assert session.presupuesto == Decimal("15000.00")
    assert session.tiendas == [Store.walmart]
    assert manager.ready(session) is True


def test_apply_text_without_product_keeps_collecting() -> None:
    manager = ConversationManager()
    session = manager.new_session(1, 2)

    session, parsed = manager.apply_text(session, "máximo 15000")

    assert parsed.producto is None
    assert session.estado == COLLECTING
    assert session.presupuesto == Decimal("15000.00")
    assert manager.needs_product(session) is True
    assert manager.question(session) is not None


def test_follow_up_updates_do_not_clear_product() -> None:
    manager = ConversationManager()
    session = manager.new_session(1, 2)
    session, _ = manager.apply_text(session, "laptop")

    session, _ = manager.apply_text(session, "en Costco")
    assert session.producto == "laptop"
    assert session.tiendas == [Store.costco]

    session, _ = manager.apply_text(session, "para gamer")
    assert session.producto == "laptop"
    assert session.perfil == "gamer"

    session, _ = manager.apply_text(session, "sin limite")
    assert session.producto == "laptop"
    assert session.presupuesto is None


def test_mode_and_voice_validation() -> None:
    manager = ConversationManager()
    session = manager.new_session(1, 2)

    assert manager.set_mode(session, "detallado").modo == "detallado"
    assert manager.set_voice(session, "siempre").voz == "siempre"
    with pytest.raises(ValueError):
        manager.set_mode(session, "otro")
    with pytest.raises(ValueError):
        manager.set_voice(session, "otro")


def test_cancel_and_reset_clear_slots() -> None:
    manager = ConversationManager()
    session = manager.new_session(1, 2)
    session, _ = manager.apply_text(session, "laptop máximo 15000 para gamer")

    cancelled = manager.cancel(session)
    assert cancelled.estado == CANCELLED
    assert cancelled.producto is None
    assert cancelled.presupuesto is None

    reset = manager.reset(session)
    assert reset.estado == "idle"
    assert reset.producto is None
    assert reset.modo == session.modo


def test_summary_and_analysis_kwargs() -> None:
    manager = ConversationManager()
    session = manager.new_session(1, 2)
    session, _ = manager.apply_text(session, "laptop máximo 15000 para estudiante")
    session = manager.set_mode(session, "detallado")

    summary = manager.summary(session)
    assert "laptop" in summary
    assert "15,000.00" in summary
    assert "detallado" in summary

    kwargs = manager.analysis_kwargs(session)
    assert kwargs["consulta"] == "laptop"
    assert kwargs["presupuesto"] == Decimal("15000.00")
    assert kwargs["perfil"] == "estudiante"
    assert kwargs["use_llm"] is True
    assert kwargs["persist"] is True


def test_analysis_kwargs_requires_product() -> None:
    manager = ConversationManager()
    session = manager.new_session(1, 2)

    with pytest.raises(ValueError):
        manager.analysis_kwargs(session)
