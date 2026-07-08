"""Provider registry.

Maps provider identifiers to their implementation classes so that new
backends can be added without touching the engine.
"""

from __future__ import annotations

from .base import TranslationProvider
from .openai_api import OpenAICompatibleProvider

_PROVIDERS: dict[str, type[TranslationProvider]] = {
    "openai": OpenAICompatibleProvider,
}


def register(name: str, cls: type[TranslationProvider]) -> None:
    _PROVIDERS[name] = cls


def available_providers() -> list[str]:
    return sorted(_PROVIDERS)


def get_provider_class(name: str) -> type[TranslationProvider]:
    try:
        return _PROVIDERS[name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {available_providers()}"
        ) from exc
