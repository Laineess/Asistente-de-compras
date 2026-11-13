from __future__ import annotations

import logging

from telegram import Update

from app.bot.handlers import create_application
from app.config import settings


def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if not settings.telegram_bot_token:
        raise SystemExit("Configura TELEGRAM_BOT_TOKEN en .env")
    if not settings.telegram_allowed_user_ids_set:
        raise SystemExit("Configura TELEGRAM_ALLOWED_USER_IDS en .env")
    application = create_application(settings)
    logging.getLogger(__name__).info("Bot iniciado con long polling")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
