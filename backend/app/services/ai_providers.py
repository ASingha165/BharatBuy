"""Provider abstractions for optional, explanation-only AI generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional


class AIProvider(ABC):
    """Small provider contract used only after deterministic procurement evaluation."""

    name: str

    @property
    @abstractmethod
    def configured(self) -> bool:
        """Whether this provider has the configuration required to make a call."""

    @abstractmethod
    def generate(self, prompt: str) -> Optional[str]:
        """Generate grounded prose, or return None when the provider is unavailable."""


class _GoogleGenAIProvider(AIProvider):
    def __init__(
        self,
        *,
        name: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        call_fn: Callable[[str, str, str, float], str],
        sdk_available: bool,
    ) -> None:
        self.name = name
        self.api_key = (api_key or "").strip()
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._call_fn = call_fn
        self._sdk_available = sdk_available

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self._sdk_available and self.model)

    def generate(self, prompt: str) -> Optional[str]:
        if not self.configured:
            return None
        text = self._call_fn(self.api_key, self.model, prompt, self.timeout_seconds)
        return text.strip() if text and text.strip() else None


class GemmaProvider(_GoogleGenAIProvider):
    """Fast remote Gemma provider; it never supplies procurement facts."""

    def __init__(self, **kwargs) -> None:
        super().__init__(name="gemma", **kwargs)


class GeminiProvider(_GoogleGenAIProvider):
    """Reasoning-oriented Gemini provider for complex grounded briefings."""

    def __init__(self, **kwargs) -> None:
        super().__init__(name="gemini", **kwargs)
