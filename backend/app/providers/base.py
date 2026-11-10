from abc import ABC, abstractmethod

from app.models import ProductOption, Store


class StoreProvider(ABC):
    def __init__(self, store: Store) -> None:
        self.store = store

    @abstractmethod
    def search(self, query: str, limit: int = 3) -> list[ProductOption]:
        raise NotImplementedError
