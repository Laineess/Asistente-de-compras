from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.bot.handlers import RateLimiter, _authorized, create_application
from app.config import Settings
from app.models import Store


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = RateLimiter(limit=2)
    now = datetime.now(timezone.utc)

    assert limiter.allow(1, now=now) is True
    assert limiter.allow(1, now=now + timedelta(seconds=1)) is True
    assert limiter.allow(1, now=now + timedelta(seconds=2)) is False
    assert limiter.allow(2, now=now) is True


def test_rate_limiter_window_expires() -> None:
    limiter = RateLimiter(limit=1, window_hours=1)
    now = datetime.now(timezone.utc)

    assert limiter.allow(1, now=now) is True
    assert limiter.allow(1, now=now + timedelta(minutes=30)) is False
    assert limiter.allow(1, now=now + timedelta(hours=2)) is True


def test_authorized_requires_allowlist_match() -> None:
    update = SimpleNamespace(effective_user=SimpleNamespace(id=42))

    assert _authorized(update, {42}) is True
    assert _authorized(update, {99}) is False
    assert _authorized(update, set()) is False


def test_settings_parses_allowed_ids() -> None:
    settings = Settings(telegram_allowed_user_ids="42, 99, invalido, -1")

    assert settings.telegram_allowed_user_ids_set == {42, 99}


def test_create_application_requires_token() -> None:
    with pytest.raises(ValueError):
        create_application(Settings(telegram_bot_token=""))


def test_create_application_builds_with_token() -> None:
    settings = Settings(
        telegram_bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        telegram_allowed_user_ids="42",
    )

    application = create_application(settings)

    assert application is not None
    assert application.handlers


class FakeMessage:
    def __init__(self, text: str = "") -> None:
        self.text = text
        self.replies: list[tuple[str, dict]] = []
        self.edits: list[tuple[str, dict]] = []

    async def reply_text(self, text: str, **kwargs):
        self.replies.append((text, kwargs))
        return self

    async def edit_text(self, text: str, **kwargs):
        self.edits.append((text, kwargs))
        return self


class FakeMedia:
    def __init__(self, duration: int = 3, file_name: str | None = None) -> None:
        self.duration = duration
        self.file_name = file_name

    async def get_file(self):
        raise NotImplementedError


class FakeVoiceMessage(FakeMessage):
    def __init__(self, voice: FakeMedia | None = None, audio: FakeMedia | None = None) -> None:
        super().__init__("")
        self.voice = voice
        self.audio = audio
        self.voices: list[dict] = []
        self.audios: list[dict] = []

    async def reply_voice(self, voice, **kwargs):
        self.voices.append(kwargs)
        return self

    async def reply_audio(self, audio, **kwargs):
        self.audios.append(kwargs)
        return self


class FakeVoiceService:
    def __init__(self, text: str = "laptop", audio=None, error: Exception | None = None) -> None:
        self.text = text
        self.audio = audio
        self.error = error
        self.transcribed = 0
        self.cleaned = []

    async def transcribe_message(self, message):
        self.transcribed += 1
        if self.error is not None:
            raise self.error
        return self.text

    async def synthesize_text(self, text):
        return self.audio

    def cleanup(self, path):
        self.cleaned.append(path)


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeChat:
    def __init__(self, chat_id: int) -> None:
        self.id = chat_id


class FakeQuery:
    def __init__(self, data: str, message: FakeMessage | None = None) -> None:
        self.data = data
        self.message = message or FakeMessage()
        self.answered = False

    async def answer(self) -> None:
        self.answered = True


class FakeUpdate:
    def __init__(
        self,
        user_id: int,
        chat_id: int,
        message: FakeMessage,
        query: FakeQuery | None = None,
    ) -> None:
        self.effective_user = FakeUser(user_id)
        self.effective_chat = FakeChat(chat_id)
        self.effective_message = message
        self.callback_query = query


class FakeRunner:
    def __init__(self, state=None, error: Exception | None = None) -> None:
        self.state = state
        self.error = error
        self.calls: list[dict] = []

    async def run(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.state


def _bot_callbacks(application):
    callbacks = {}
    for handler in application.handlers[0]:
        commands = getattr(handler, "commands", None)
        if commands:
            for command in commands:
                callbacks[command] = handler.callback
        elif type(handler).__name__ == "CallbackQueryHandler":
            callbacks["callback"] = handler.callback
        elif getattr(handler.callback, "__name__", "") == "voice_message":
            callbacks["voice"] = handler.callback
        else:
            callbacks["text"] = handler.callback
    return callbacks


def _analysis_result():
    from decimal import Decimal

    from app.models import AnalysisResult, PriceSummary, ProductOption, Store

    option = ProductOption(
        nombre="Laptop Lenovo IdeaPad 3",
        comercio=Store.walmart,
        precio=Decimal("12000"),
        url="https://example.com/laptop",
        descripcion="Laptop para estudio.",
    )
    return AnalysisResult(
        producto="laptop",
        tiendas=[Store.walmart],
        opciones=[option],
        resumen_precios=PriceSummary(
            precio_final=Decimal("12000"),
            opcion_recomendada="Laptop Lenovo IdeaPad 3",
            precio_promedio=Decimal("12000"),
            precio_minimo=Decimal("12000"),
            precio_maximo=Decimal("12000"),
            rango=Decimal("0"),
            opciones_consideradas=1,
            comercio_mas_barato="Walmart",
            comercio_mas_caro="Walmart",
        ),
        recomendacion="Buena opción.",
    )


async def _app(tmp_path, runner=None, limiter=None, voice_service=None):
    from app.bot.handlers import create_application
    from app.bot.session_store import SessionStore
    from app.config import Settings

    settings = Settings(
        telegram_bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        telegram_allowed_user_ids="42",
    )
    store = SessionStore(tmp_path / "sessions.db", ttl_hours=24)
    await store.init()
    application = create_application(
        settings,
        store=store,
        runner=runner or FakeRunner({"resultado": _analysis_result()}),
        limiter=limiter,
        voice_service=voice_service,
    )
    return application, store


async def test_start_and_commands(tmp_path) -> None:
    application, store = await _app(tmp_path)
    callbacks = _bot_callbacks(application)
    message = FakeMessage("/start")
    update = FakeUpdate(42, 100, message)

    await callbacks["start"](update, None)
    assert "Asistente de compras" in message.replies[0][0]
    assert await store.get(42) is not None

    await callbacks["ayuda"](update, None)
    assert "Comandos" in message.replies[-1][0]

    await callbacks["modo"](update, None)
    assert "Modo actual" in message.replies[-1][0]

    await callbacks["voz"](update, None)
    assert "Respuesta de audio" in message.replies[-1][0]

    await callbacks["estado"](update, None)
    assert "Estado" in message.replies[-1][0]

    await callbacks["nuevo"](update, None)
    assert "Nueva consulta" in message.replies[-1][0]

    await callbacks["cancelar"](update, None)
    assert "cancelada" in message.replies[-1][0]


async def test_unauthorized_start_is_rejected(tmp_path) -> None:
    application, _ = await _app(tmp_path)
    callbacks = _bot_callbacks(application)
    message = FakeMessage("/start")
    update = FakeUpdate(99, 100, message)

    await callbacks["start"](update, None)

    assert message.replies[-1][0] == "No autorizado."


async def test_text_collects_product_and_confirms(tmp_path) -> None:
    application, store = await _app(tmp_path)
    callbacks = _bot_callbacks(application)
    message = FakeMessage("laptop máximo 15000")
    update = FakeUpdate(42, 100, message)

    await callbacks["text"](update, None)
    session = await store.get(42)

    assert session is not None
    assert session.producto == "laptop"
    assert session.estado == "confirmando"
    assert "Revisa la consulta" in message.replies[-1][0]
    assert message.replies[-1][1]["reply_markup"] is not None


async def test_text_without_product_asks_for_it(tmp_path) -> None:
    application, _ = await _app(tmp_path)
    callbacks = _bot_callbacks(application)
    message = FakeMessage("máximo 15000")
    update = FakeUpdate(42, 100, message)

    await callbacks["text"](update, None)

    assert "¿Qué producto" in message.replies[-1][0]


async def test_text_confirm_and_cancel_words(tmp_path) -> None:
    runner = FakeRunner({"resultado": _analysis_result()})
    application, store = await _app(tmp_path, runner=runner)
    callbacks = _bot_callbacks(application)
    message = FakeMessage("laptop")
    update = FakeUpdate(42, 100, message)

    await callbacks["text"](update, None)
    await callbacks["text"](update, None)
    assert message.text == "laptop"
    message.text = "analizar"
    await callbacks["text"](update, None)
    assert runner.calls

    message.text = "cancelar"
    await callbacks["text"](update, None)
    session = await store.get(42)
    assert session is not None and session.estado == "cancelado"


async def test_callback_analyze_success(tmp_path) -> None:
    runner = FakeRunner({"resultado": _analysis_result()})
    application, store = await _app(tmp_path, runner=runner)
    callbacks = _bot_callbacks(application)
    message = FakeMessage("laptop")
    update = FakeUpdate(42, 100, message)
    await callbacks["text"](update, None)

    status = FakeMessage()
    query = FakeQuery("analyze", status)
    callback_update = FakeUpdate(42, 100, status, query=query)
    await callbacks["callback"](callback_update, None)

    assert query.answered is True
    assert runner.calls[0]["consulta"] == "laptop"
    assert runner.calls[0]["use_llm"] is False
    assert status.edits
    assert "Resultado para laptop" in status.edits[0][0]
    session = await store.get(42)
    assert session is not None and session.estado == "resultados"


async def test_callback_analyze_reports_runner_error(tmp_path) -> None:
    runner = FakeRunner(error=RuntimeError("fallo"))
    application, _ = await _app(tmp_path, runner=runner)
    callbacks = _bot_callbacks(application)
    message = FakeMessage("laptop")
    update = FakeUpdate(42, 100, message)
    await callbacks["text"](update, None)

    status = FakeMessage()
    query = FakeQuery("analyze", status)
    callback_update = FakeUpdate(42, 100, status, query=query)
    await callbacks["callback"](callback_update, None)

    assert status.edits
    assert "No pude completar" in status.edits[0][0]


async def test_callback_analyze_reports_empty_result(tmp_path) -> None:
    runner = FakeRunner({"resultado": None, "errores": ["sin datos"]})
    application, _ = await _app(tmp_path, runner=runner)
    callbacks = _bot_callbacks(application)
    message = FakeMessage("laptop")
    update = FakeUpdate(42, 100, message)
    await callbacks["text"](update, None)

    status = FakeMessage()
    query = FakeQuery("analyze", status)
    callback_update = FakeUpdate(42, 100, status, query=query)
    await callbacks["callback"](callback_update, None)

    assert "No pude generar" in status.edits[0][0]
    assert "sin datos" in status.edits[0][0]


async def test_callback_analyze_respects_rate_limit(tmp_path) -> None:
    limiter = RateLimiter(limit=1)
    limiter.allow(42)
    runner = FakeRunner({"resultado": _analysis_result()})
    application, _ = await _app(tmp_path, runner=runner, limiter=limiter)
    callbacks = _bot_callbacks(application)
    message = FakeMessage("laptop")
    update = FakeUpdate(42, 100, message)
    await callbacks["text"](update, None)

    status = FakeMessage()
    query = FakeQuery("analyze", status)
    callback_update = FakeUpdate(42, 100, status, query=query)
    await callbacks["callback"](callback_update, None)

    assert status.replies[-1][0].startswith("Límite")
    assert runner.calls == []


async def test_callback_mode_voice_stores_and_cancel(tmp_path) -> None:
    application, store = await _app(tmp_path)
    callbacks = _bot_callbacks(application)
    message = FakeMessage("laptop")
    update = FakeUpdate(42, 100, message)
    await callbacks["text"](update, None)

    query = FakeQuery("mode:detallado", FakeMessage())
    callback_update = FakeUpdate(42, 100, query.message, query=query)
    await callbacks["callback"](callback_update, None)
    session = await store.get(42)
    assert session is not None and session.modo == "detallado"

    query = FakeQuery("voice:siempre", FakeMessage())
    callback_update = FakeUpdate(42, 100, query.message, query=query)
    await callbacks["callback"](callback_update, None)
    session = await store.get(42)
    assert session is not None and session.voz == "siempre"

    query = FakeQuery("stores:walmart", FakeMessage())
    callback_update = FakeUpdate(42, 100, query.message, query=query)
    await callbacks["callback"](callback_update, None)
    session = await store.get(42)
    assert session is not None and session.tiendas == [Store.walmart]

    query = FakeQuery("stores:all", FakeMessage())
    callback_update = FakeUpdate(42, 100, query.message, query=query)
    await callbacks["callback"](callback_update, None)
    session = await store.get(42)
    assert session is not None and session.tiendas == list(Store)

    query = FakeQuery("cancel", FakeMessage())
    callback_update = FakeUpdate(42, 100, query.message, query=query)
    await callbacks["callback"](callback_update, None)
    session = await store.get(42)
    assert session is not None and session.estado == "cancelado"

    query = FakeQuery("new", FakeMessage())
    callback_update = FakeUpdate(42, 100, query.message, query=query)
    await callbacks["callback"](callback_update, None)
    assert "¿Qué producto" in query.message.replies[-1][0]


async def test_callback_unauthorized_and_invalid_values(tmp_path) -> None:
    application, _ = await _app(tmp_path)
    callbacks = _bot_callbacks(application)
    message = FakeMessage("laptop")
    update = FakeUpdate(42, 100, message)
    await callbacks["text"](update, None)

    query = FakeQuery("mode:otro", FakeMessage())
    unauth = FakeUpdate(99, 100, query.message, query=query)
    await callbacks["callback"](unauth, None)
    assert query.message.replies[-1][0] == "No autorizado."

    query = FakeQuery("mode:otro", FakeMessage())
    authorized = FakeUpdate(42, 100, query.message, query=query)
    await callbacks["callback"](authorized, None)
    assert not query.message.replies

    query = FakeQuery("stores:otro", FakeMessage())
    authorized = FakeUpdate(42, 100, query.message, query=query)
    await callbacks["callback"](authorized, None)
    assert not query.message.replies

    query = FakeQuery("voice:otro", FakeMessage())
    authorized = FakeUpdate(42, 100, query.message, query=query)
    await callbacks["callback"](authorized, None)
    assert not query.message.replies



async def test_voice_transcribes_and_confirms(tmp_path) -> None:
    voice_service = FakeVoiceService("laptop máximo 15000")
    application, store = await _app(tmp_path, voice_service=voice_service)
    callbacks = _bot_callbacks(application)
    message = FakeVoiceMessage(voice=FakeMedia(duration=4))
    update = FakeUpdate(42, 100, message)

    await callbacks["voice"](update, None)

    session = await store.get(42)
    assert voice_service.transcribed == 1
    assert session is not None
    assert session.producto == "laptop"
    assert session.entrada_voz is True
    assert any("Entendí" in text for text, _ in message.edits)
    assert "Revisa la consulta" in message.replies[-1][0]


async def test_voice_reports_transcription_error(tmp_path) -> None:
    from app.bot.voice import VoiceError

    voice_service = FakeVoiceService(error=VoiceError("Audio inválido."))
    application, _ = await _app(tmp_path, voice_service=voice_service)
    callbacks = _bot_callbacks(application)
    message = FakeVoiceMessage(voice=FakeMedia(duration=4))
    update = FakeUpdate(42, 100, message)

    await callbacks["voice"](update, None)

    assert message.edits[-1][0] == "Audio inválido."


async def test_voice_result_sends_audio_in_auto_mode(tmp_path) -> None:
    audio = tmp_path / "respuesta.ogg"
    audio.write_bytes(b"audio")
    voice_service = FakeVoiceService("laptop", audio=audio)
    application, _ = await _app(tmp_path, voice_service=voice_service)
    callbacks = _bot_callbacks(application)
    message = FakeVoiceMessage(voice=FakeMedia(duration=4))
    update = FakeUpdate(42, 100, message)
    await callbacks["voice"](update, None)

    query = FakeQuery("analyze", message)
    callback_update = FakeUpdate(42, 100, message, query=query)
    await callbacks["callback"](callback_update, None)

    assert len(message.voices) == 1
    assert voice_service.cleaned == [audio]


async def test_text_result_sends_audio_when_always(tmp_path) -> None:
    audio = tmp_path / "respuesta.mp3"
    audio.write_bytes(b"audio")
    voice_service = FakeVoiceService(audio=audio)
    application, _ = await _app(tmp_path, voice_service=voice_service)
    callbacks = _bot_callbacks(application)
    message = FakeVoiceMessage()
    message.text = "laptop"
    update = FakeUpdate(42, 100, message)
    await callbacks["text"](update, None)

    query = FakeQuery("voice:siempre", message)
    await callbacks["callback"](FakeUpdate(42, 100, message, query=query), None)
    query = FakeQuery("analyze", message)
    await callbacks["callback"](FakeUpdate(42, 100, message, query=query), None)

    assert len(message.audios) == 1
    assert voice_service.cleaned == [audio]
