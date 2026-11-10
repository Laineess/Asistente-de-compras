from app.config import settings
from app.models import Store
from app.providers.mock_provider import MockProvider
from app.providers.service import ProductSearchService
from app.providers.tavily_provider import TavilyProvider


def build_default_service() -> ProductSearchService:
    providers = {}
    if settings.tavily_api_key:
        providers = {
            store: TavilyProvider(store, settings.tavily_api_key)
            for store in Store
        }

    fallback = {store: MockProvider(store) for store in Store}
    return ProductSearchService(providers=providers, fallback_providers=fallback)
