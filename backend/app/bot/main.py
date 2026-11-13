from __future__ import annotations

import logging

from telegram import Update

from app.bot.handlers import create_application
from app.config import settings


class _TokenRedactionFilter(logging.Filter):
    def __init__(self, token: str) -> None:
        super().__init__()
        self._token = token

    def _redact(self, value: object) -> object:
        if isinstance(value, str) and self._token:
            return value.replace(self._token, "***")
        return value

    def filter(self, record: logging.LogRecord) -> bool:
        if not self._token:
            return True
        record.msg = self._redact(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(self._redact(arg) for arg in record.args)
        elif isinstance(record.args, dict):
            record.args = {
                key: self._redact(value) for key, value in record.args.items()
            }
        return True


def _configure_logging(token: str) -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    redaction = _TokenRedactionFilter(token)
    for handler in logging.getLogger().handlers:
        handler.addFilter(redaction)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def main() -> None:
    _configure_logging(settings.telegram_bot_token)
    if not settings.telegram_bot_token:
        raise SystemExit("Configura TELEGRAM_BOT_TOKEN en .env")
    if not settings.telegram_allowed_user_ids_set:
        raise SystemExit("Configura TELEGRAM_ALLOWED_USER_IDS en .env")
    application = create_application(settings)
    logging.getLogger(__name__).info("Bot iniciado con long polling")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
