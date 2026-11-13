from __future__ import annotations

import html
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.bot.conversation import CONFIRMING, RESULTS, ConversationManager, Session
from app.bot.formatter import (
    format_help,
    format_results,
    format_status,
    format_welcome,
)
from app.bot.runner import AnalysisRunner
from app.bot.session_store import SessionStore
from app.bot.voice import VoiceError, VoiceService
from app.config import Settings
from app.models import Store

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, limit: int, window_hours: int = 1) -> None:
        self.limit = max(1, limit)
        self.window = timedelta(hours=window_hours)
        self._events: dict[int, deque[datetime]] = defaultdict(deque)

    def allow(self, user_id: int, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        events = self._events[user_id]
        cutoff = now - self.window
        while events and events[0] < cutoff:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True


def _user_id(update: Update) -> int | None:
    user = update.effective_user
    return user.id if user is not None else None


def _chat_id(update: Update) -> int | None:
    chat = update.effective_chat
    return chat.id if chat is not None else None


def _authorized(update: Update, allowed: set[int]) -> bool:
    user_id = _user_id(update)
    return bool(allowed) and user_id in allowed


def _confirmation_keyboard(session: Session) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("Analizar", callback_data="analyze"),
            InlineKeyboardButton("Cancelar", callback_data="cancel"),
        ],
        [
            InlineKeyboardButton("Todas", callback_data="stores:all"),
            InlineKeyboardButton("Walmart", callback_data="stores:walmart"),
            InlineKeyboardButton("Costco", callback_data="stores:costco"),
            InlineKeyboardButton("Sam's", callback_data="stores:sams"),
        ],
        [
            InlineKeyboardButton("Modo fast", callback_data="mode:fast"),
            InlineKeyboardButton("Modo detallado", callback_data="mode:detallado"),
        ],
    ]
    if session.estado == RESULTS:
        rows.append([InlineKeyboardButton("Nueva consulta", callback_data="new")])
    return InlineKeyboardMarkup(rows)


def _mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("fast (sin Gemini)", callback_data="mode:fast"),
                InlineKeyboardButton("detallado (Gemini)", callback_data="mode:detallado"),
            ]
        ]
    )


def _voice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("auto", callback_data="voice:auto"),
                InlineKeyboardButton("siempre", callback_data="voice:siempre"),
                InlineKeyboardButton("nunca", callback_data="voice:nunca"),
            ]
        ]
    )


async def _send(
    update: Update,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    message = update.effective_message
    if message is None:
        return
    await message.reply_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=reply_markup,
    )


def create_application(
    settings: Settings,
    *,
    store: SessionStore | None = None,
    runner: AnalysisRunner | None = None,
    manager: ConversationManager | None = None,
    limiter: RateLimiter | None = None,
    voice_service: VoiceService | None = None,
) -> Application:
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN no esta configurado")
    allowed = settings.telegram_allowed_user_ids_set
    session_store = store or SessionStore(
        settings.bot_session_db_path,
        ttl_hours=settings.bot_session_ttl_hours,
    )
    analysis_runner = runner or AnalysisRunner()
    conversation = manager or ConversationManager(
        default_mode=settings.bot_default_mode,
        default_voice=settings.bot_voice_reply_mode,
    )
    rate_limiter = limiter or RateLimiter(settings.bot_rate_limit_per_hour)
    audio_service = voice_service or VoiceService(
        max_audio_seconds=settings.bot_max_audio_seconds,
        stt_model=settings.telegram_stt_model,
        stt_device=settings.telegram_stt_device,
        stt_compute_type=settings.telegram_stt_compute_type,
        tts_voice=settings.telegram_tts_voice,
    )

    async def post_init(application: Application) -> None:
        await session_store.init()
        await session_store.purge_expired()
        if not allowed:
            logger.warning("TELEGRAM_ALLOWED_USER_IDS esta vacio; el bot rechazara a todos")

    async def guard(update: Update) -> bool:
        if _authorized(update, allowed):
            return True
        logger.warning("Intento no autorizado de user_id=%s", _user_id(update))
        await _send(update, "No autorizado.")
        return False

    async def get_session(update: Update) -> Session | None:
        user_id = _user_id(update)
        chat_id = _chat_id(update)
        if user_id is None or chat_id is None:
            return None
        session = await session_store.get(user_id)
        if session is None:
            session = conversation.new_session(user_id, chat_id)
            await session_store.save(session)
        elif session.chat_id != chat_id:
            session.chat_id = chat_id
            await session_store.save(session)
        return session

    async def send_summary(update: Update, session: Session) -> None:
        await _send(
            update,
            conversation.summary(session),
            reply_markup=_confirmation_keyboard(session),
        )

    async def send_audio(update: Update, session: Session, reply) -> None:
        if session.voz == "nunca":
            return
        if session.voz == "auto" and not session.entrada_voz:
            return
        message = update.effective_message
        if message is None or not reply.audio_scripts:
            return
        for script, group in zip(reply.audio_scripts, reply.groups):
            path = None
            try:
                path = await audio_service.synthesize_text(script)
                if path is None:
                    continue
                with path.open("rb") as audio:
                    if path.suffix.lower() == ".ogg":
                        await message.reply_voice(voice=audio, caption=group.nombre[:900])
                    else:
                        await message.reply_audio(audio=audio, title=group.nombre[:900])
            except Exception:
                logger.exception("No pude generar o enviar el audio")
            finally:
                audio_service.cleanup(path)

    async def execute(update: Update, session: Session) -> None:
        if not conversation.ready(session):
            await _send(update, conversation.question(session) or "Falta el producto.")
            return
        if not rate_limiter.allow(session.user_id):
            await _send(
                update,
                "Límite de análisis alcanzado. Intenta más tarde.",
            )
            return
        running = conversation.set_running(session)
        await session_store.save(running)
        message = update.effective_message
        if message is None:
            return
        status = await message.reply_text("Analizando… esto puede tardar unos segundos.")
        try:
            state = await analysis_runner.run(**conversation.analysis_kwargs(running))
        except Exception:
            logger.exception("Fallo el analisis del bot")
            restored = conversation.set_results(running)
            await session_store.save(restored)
            await status.edit_text(
                "No pude completar el análisis. Intenta de nuevo con /nuevo "
                "o cambia a modo fast con /modo."
            )
            return
        result = state.get("resultado")
        finished = conversation.set_results(running)
        await session_store.save(finished)
        if result is None:
            errors = state.get("errores") or ["sin resultado"]
            await status.edit_text(
                "No pude generar una recomendación.\nErrores: " + "; ".join(errors)
            )
            return
        reply = format_results(result, finished)
        try:
            await status.edit_text(
                reply.messages[0],
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=_confirmation_keyboard(finished),
            )
        except Exception:
            await status.edit_text("Resultado listo. Enviando detalles…")
            await _send(update, reply.messages[0])
        for chunk in reply.messages[1:]:
            await message.reply_text(
                chunk,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        await send_audio(update, finished, reply)

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await guard(update):
            return
        session = await get_session(update)
        if session is None:
            return
        session = conversation.reset(session)
        await session_store.save(session)
        await _send(update, format_welcome())

    async def new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await guard(update):
            return
        session = await get_session(update)
        if session is None:
            return
        session = conversation.reset(session)
        await session_store.save(session)
        await _send(update, "Nueva consulta. " + (conversation.question(session) or ""))

    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await guard(update):
            return
        session = await get_session(update)
        if session is None:
            return
        session = conversation.cancel(session)
        await session_store.save(session)
        await _send(update, "Consulta cancelada. Usa /nuevo para empezar otra.")

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await guard(update):
            return
        await _send(update, format_help())

    async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await guard(update):
            return
        session = await get_session(update)
        if session is None:
            return
        await _send(
            update,
            f"Modo actual: <b>{session.modo}</b>. Elige uno:",
            reply_markup=_mode_keyboard(),
        )

    async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await guard(update):
            return
        session = await get_session(update)
        if session is None:
            return
        await _send(
            update,
            f"Respuesta de audio actual: <b>{session.voz}</b>. Elige una opción:",
            reply_markup=_voice_keyboard(),
        )

    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await guard(update):
            return
        session = await get_session(update)
        if session is None:
            return
        await _send(update, format_status(session))

    async def process_text(
        update: Update,
        session: Session,
        text: str,
        *,
        from_voice: bool = False,
    ) -> None:
        lowered = text.casefold()
        if lowered in {"analizar", "si", "sí", "confirmar", "dale", "ok"}:
            session = conversation.set_input_voice(session, from_voice)
            await session_store.save(session)
            await execute(update, session)
            return
        if lowered in {"cancelar", "cancel"}:
            session = conversation.cancel(session)
            await session_store.save(session)
            await _send(update, "Consulta cancelada. Usa /nuevo para empezar otra.")
            return
        updated, _ = conversation.apply_text(session, text, from_voice=from_voice)
        await session_store.save(updated)
        if conversation.needs_product(updated):
            await _send(update, conversation.question(updated) or "")
            return
        await send_summary(update, updated)

    async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await guard(update):
            return
        message = update.effective_message
        if message is None or not message.text:
            return
        session = await get_session(update)
        if session is None:
            return
        await process_text(update, session, message.text.strip())

    async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await guard(update):
            return
        message = update.effective_message
        if message is None or not (message.voice or message.audio):
            return
        session = await get_session(update)
        if session is None:
            return
        status = await message.reply_text("Transcribiendo audio…")
        try:
            text = await audio_service.transcribe_message(message)
        except VoiceError as exc:
            await status.edit_text(str(exc))
            return
        except Exception:
            logger.exception("Fallo la transcripcion del bot")
            await status.edit_text(
                "No pude transcribir el audio. Intenta de nuevo o escribe la consulta."
            )
            return
        await status.edit_text(
            f"Entendí: <i>{html.escape(text)}</i>",
            parse_mode="HTML",
        )
        await process_text(update, session, text, from_voice=True)

    async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if query is None:
            return
        await query.answer()
        if not _authorized(update, allowed):
            logger.warning("Callback no autorizado de user_id=%s", _user_id(update))
            await query.message.reply_text("No autorizado.")
            return
        session = await get_session(update)
        if session is None:
            return
        data = query.data or ""
        action, _, value = data.partition(":")

        if action == "analyze":
            await execute(update, session)
            return
        if action == "cancel":
            session = conversation.cancel(session)
            await session_store.save(session)
            await query.message.reply_text(
                "Consulta cancelada. Usa /nuevo para empezar otra.",
                parse_mode="HTML",
            )
            return
        if action == "new":
            session = conversation.reset(session)
            await session_store.save(session)
            await query.message.reply_text(
                conversation.question(session) or "Nueva consulta.",
                parse_mode="HTML",
            )
            return
        if action == "mode":
            try:
                session = conversation.set_mode(session, value)
            except ValueError:
                return
            await session_store.save(session)
            await query.message.reply_text(
                f"Modo cambiado a <b>{session.modo}</b>.",
                parse_mode="HTML",
            )
            if session.estado == CONFIRMING and session.producto:
                await send_summary(update, session)
            return
        if action == "voice":
            try:
                session = conversation.set_voice(session, value)
            except ValueError:
                return
            await session_store.save(session)
            await query.message.reply_text(
                f"Respuesta de audio: <b>{session.voz}</b>.",
                parse_mode="HTML",
            )
            return
        if action == "stores":
            if value == "all":
                stores = list(Store)
            else:
                try:
                    stores = [Store(value)]
                except ValueError:
                    return
            session = conversation.set_stores(session, stores)
            await session_store.save(session)
            if session.producto:
                await send_summary(update, session)
            else:
                await query.message.reply_text(
                    "Tiendas actualizadas. ¿Qué producto quieres comparar?",
                    parse_mode="HTML",
                )

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("nuevo", new))
    application.add_handler(CommandHandler("cancelar", cancel))
    application.add_handler(CommandHandler("ayuda", help_command))
    application.add_handler(CommandHandler("modo", mode))
    application.add_handler(CommandHandler("voz", voice))
    application.add_handler(CommandHandler("estado", status))
    application.add_handler(CallbackQueryHandler(callback))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    return application
