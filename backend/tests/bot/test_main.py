import pytest

from app.bot import main as bot_main
from app.config import Settings


class FakeApplication:
    def __init__(self) -> None:
        self.polling_calls = []

    def run_polling(self, **kwargs) -> None:
        self.polling_calls.append(kwargs)


def test_main_requires_token(monkeypatch) -> None:
    monkeypatch.setattr(
        bot_main,
        "settings",
        Settings(telegram_bot_token="", telegram_allowed_user_ids="42"),
    )

    with pytest.raises(SystemExit):
        bot_main.main()


def test_main_requires_allowlist(monkeypatch) -> None:
    monkeypatch.setattr(
        bot_main,
        "settings",
        Settings(telegram_bot_token="123456:ABC", telegram_allowed_user_ids=""),
    )

    with pytest.raises(SystemExit):
        bot_main.main()


def test_main_runs_polling(monkeypatch) -> None:
    settings = Settings(
        telegram_bot_token="123456:ABC",
        telegram_allowed_user_ids="42",
    )
    application = FakeApplication()
    monkeypatch.setattr(bot_main, "settings", settings)
    monkeypatch.setattr(bot_main, "create_application", lambda _settings: application)

    bot_main.main()

    assert application.polling_calls
    assert "allowed_updates" in application.polling_calls[0]
