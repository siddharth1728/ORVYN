"""LLM and Embedding provider interfaces and registry."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class LLMResponse(BaseModel):
    content: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    usage: Dict[str, Any] = Field(default_factory=dict)
    model: str = "mock"


class LLMProvider(ABC):
    """Abstract interface for LLM model providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generates completion or tool calls from the model."""
        pass


class EmbeddingProvider(ABC):
    """Abstract interface for vector embedding providers."""

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generates vector embeddings for a batch of strings."""
        pass


class MockLLMProvider(LLMProvider):
    """Deterministic mock provider for offline testing and development."""

    def __init__(self, predefined_response: str = "Plan created successfully.") -> None:
        self.predefined_response = predefined_response

    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        return LLMResponse(
            content=self.predefined_response,
            tool_calls=[],
            usage={"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
            model="mock-agent-model",
        )


class LLMProviderFactory:
    """Registry and factory for LLM providers."""

    _registry: Dict[str, type[LLMProvider]] = {
        "mock": MockLLMProvider,
    }

    @classmethod
    def register(cls, name: str, provider_cls: type[LLMProvider]) -> None:
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def get_provider(cls, name: str, **kwargs: Any) -> LLMProvider:
        provider_cls = cls._registry.get(name.lower())
        if not provider_cls:
            # Fall back to mock if requested provider is unregistered
            return MockLLMProvider()
        return provider_cls(**kwargs)
