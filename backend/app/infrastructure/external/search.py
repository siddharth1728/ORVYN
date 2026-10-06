"""Search provider abstraction and research boundary."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str
    source: str


class SearchProvider(ABC):
    """Abstract interface for external search providers."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        """Performs a web search returning factual sources."""
        pass


class UnconfiguredSearchProvider(SearchProvider):
    """Boundary provider when no live web research API is configured."""

    async def search(self, query: str, max_results: int = 5) -> List[SearchResultItem]:
        raise NotImplementedError(
            "Search provider is not configured. Set TAVILY_API_KEY or configure a supported search provider."
        )


class SearchProviderFactory:
    """Registry and factory for external search providers."""

    _registry: Dict[str, type[SearchProvider]] = {
        "mock": UnconfiguredSearchProvider,
    }

    @classmethod
    def register(cls, name: str, provider_cls: type[SearchProvider]) -> None:
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def get_provider(cls, name: str, **kwargs: Any) -> SearchProvider:
        provider_cls = cls._registry.get(name.lower(), UnconfiguredSearchProvider)
        return provider_cls(**kwargs)
