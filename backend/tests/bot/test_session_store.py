from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.bot.conversation import Session
from app.bot.session_store import SessionStore
from app.models import Store


async def test_session_store_roundtrip(tmp_path) -> None:
    store = SessionStore(tmp_path / "bot_sessions.db", ttl_hours=24)
    await store.init()
    session = Session(
        user_id=10,
        chat_id=20,
        estado="confirmando",
        producto="laptop",
        tiendas=[Store.walmart, Store.costco],
        presupuesto=Decimal("15000.00"),
        perfil="estudiante",
        limite=4,
        modo="detallado",
        voz="siempre",
        entrada_voz=True,
    )

    await store.save(session)
    loaded = await store.get(10)

    assert loaded is not None
    assert loaded.chat_id == 20
    assert loaded.producto == "laptop"
    assert loaded.tiendas == [Store.walmart, Store.costco]
    assert loaded.presupuesto == Decimal("15000.00")
    assert loaded.perfil == "estudiante"
    assert loaded.limite == 4
    assert loaded.modo == "detallado"
    assert loaded.voz == "siempre"
    assert loaded.entrada_voz is True


async def test_session_store_updates_existing_row(tmp_path) -> None:
    store = SessionStore(tmp_path / "bot_sessions.db", ttl_hours=24)
    await store.init()
    session = Session(user_id=10, chat_id=20, producto="laptop")
    await store.save(session)

    session.producto = "audifonos"
    session.estado = "confirmando"
    await store.save(session)
    loaded = await store.get(10)

    assert loaded is not None
    assert loaded.producto == "audifonos"
    assert loaded.estado == "confirmando"


async def test_session_store_isolates_users(tmp_path) -> None:
    store = SessionStore(tmp_path / "bot_sessions.db", ttl_hours=24)
    await store.init()
    await store.save(Session(user_id=1, chat_id=11, producto="laptop"))
    await store.save(Session(user_id=2, chat_id=22, producto="licuadora"))

    first = await store.get(1)
    second = await store.get(2)

    assert first is not None and first.producto == "laptop"
    assert second is not None and second.producto == "licuadora"


async def test_session_store_expires_and_deletes(tmp_path) -> None:
    store = SessionStore(tmp_path / "bot_sessions.db", ttl_hours=1)
    await store.init()
    old = Session(
        user_id=10,
        chat_id=20,
        producto="laptop",
        actualizado_en=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    await store.save(old)

    assert await store.get(10) is None
    assert await store.get(10) is None


async def test_session_store_purge_expired(tmp_path) -> None:
    store = SessionStore(tmp_path / "bot_sessions.db", ttl_hours=1)
    await store.init()
    old = Session(
        user_id=1,
        chat_id=11,
        actualizado_en=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    fresh = Session(user_id=2, chat_id=22)
    await store.save(old)
    await store.save(fresh)

    deleted = await store.purge_expired()

    assert deleted == 1
    assert await store.get(1) is None
    assert await store.get(2) is not None
