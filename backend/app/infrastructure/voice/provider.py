"""Voice, STT, TTS, and Telephony provider abstractions."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel


class OutboundCallRequest(BaseModel):
    to_phone: str
    task_id: UUID
    reason: str
    initial_prompt: str
    metadata: Dict[str, Any] = {}


class OutboundCallResponse(BaseModel):
    call_id: str
    status: str
    provider: str


class TelephonyProvider(ABC):
    """Abstract interface for telephony providers (Twilio, Vapi, etc.)."""

    @abstractmethod
    async def make_call(self, request: OutboundCallRequest) -> OutboundCallResponse:
        """Initiates an outbound voice call."""
        pass

    @abstractmethod
    async def hangup_call(self, call_id: str) -> bool:
        """Terminates an active voice call."""
        pass


class STTProvider(ABC):
    """Abstract interface for Speech-to-Text transcription."""

    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """Converts raw audio bytes to text transcript."""
        pass


class TTSProvider(ABC):
    """Abstract interface for Text-to-Speech synthesis."""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Converts text into audio bytes."""
        pass


class MockTelephonyProvider(TelephonyProvider):
    """Mock telephony provider for testing and offline development."""

    def __init__(self) -> None:
        self.calls: Dict[str, OutboundCallRequest] = {}

    async def make_call(self, request: OutboundCallRequest) -> OutboundCallResponse:
        import uuid
        call_id = f"mock-call-{uuid.uuid4().hex[:8]}"
        self.calls[call_id] = request
        return OutboundCallResponse(
            call_id=call_id,
            status="INITIATED",
            provider="mock",
        )

    async def hangup_call(self, call_id: str) -> bool:
        return True


class TelephonyProviderFactory:
    """Registry and factory for voice telephony providers."""

    _registry: Dict[str, type[TelephonyProvider]] = {
        "mock": MockTelephonyProvider,
    }

    @classmethod
    def register(cls, name: str, provider_cls: type[TelephonyProvider]) -> None:
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def get_provider(cls, name: str, **kwargs: Any) -> TelephonyProvider:
        provider_cls = cls._registry.get(name.lower(), MockTelephonyProvider)
        return provider_cls(**kwargs)
