"""Translation engine.

Builds the configured provider and exposes a simple ``translate`` API used by
both the CLI and the GUI.
"""

from __future__ import annotations

from .config import AppConfig
from .providers.base import ChatMessage, TranslationProvider
from .providers.registry import get_provider_class


class TranslationEngine:
    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig.load()
        self._provider: TranslationProvider | None = None

    def _build_provider(self) -> TranslationProvider:
        cls = get_provider_class(self.config.provider)
        return cls(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            model=self.config.model,
            timeout=self.config.timeout,
        )

    @property
    def provider(self) -> TranslationProvider:
        if self._provider is None:
            self._provider = self._build_provider()
        return self._provider

    def reload(self, config: AppConfig) -> None:
        """Apply a new configuration and rebuild the provider on next use."""
        self.config = config
        self._provider = None

    def translate(
        self,
        text: str,
        source_lang: str | None = None,
        target_lang: str | None = None,
    ) -> str:
        src = source_lang or self.config.source_lang
        tgt = target_lang or self.config.target_lang
        return self.provider.translate(text, src, tgt)

    def chat(self, messages: list[ChatMessage]) -> str:
        return self.provider.chat(messages)
