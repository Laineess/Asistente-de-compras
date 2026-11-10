from app.models import Store
from app.providers import factory


def test_build_default_service_uses_mock_without_tavily_key(monkeypatch) -> None:
    monkeypatch.setattr(factory.settings, "tavily_api_key", "")

    service = factory.build_default_service()

    assert service._providers == {}
    assert set(service._fallback) == set(Store)
    assert all(
        provider.__class__.__name__ == "MockProvider"
        for provider in service._fallback.values()
    )


def test_build_default_service_builds_tavily_providers_with_key(monkeypatch) -> None:
    created: list[tuple[Store, str]] = []

    def fake_tavily(store: Store, api_key: str):
        created.append((store, api_key))
        return f"tavily:{store.value}"

    monkeypatch.setattr(factory.settings, "tavily_api_key", "clave")
    monkeypatch.setattr(factory, "TavilyProvider", fake_tavily)

    service = factory.build_default_service()

    assert created == [(store, "clave") for store in Store]
    assert service._providers == {
        Store.walmart: "tavily:walmart",
        Store.costco: "tavily:costco",
        Store.sams: "tavily:sams",
    }
    assert set(service._fallback) == set(Store)
