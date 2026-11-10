from app.config import PROJECT_ROOT, Settings


def test_settings_resolves_relative_sqlite_path() -> None:
    settings = Settings(database_url="sqlite:///./backend/data/test.db")

    expected = (PROJECT_ROOT / "backend/data/test.db").resolve().as_posix()
    assert settings.database_url == f"sqlite:///{expected}"


def test_settings_keeps_non_relative_database_urls() -> None:
    settings = Settings(database_url="sqlite:///relative.db")

    assert settings.database_url == "sqlite:///relative.db"


def test_cors_origins_list_trims_and_ignores_empty_values() -> None:
    settings = Settings(cors_origins="http://a, http://b , ")

    assert settings.cors_origins_list == ["http://a", "http://b"]
