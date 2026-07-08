"""Abstract base class for translation providers.

Every backend (OpenAI-compatible, DeepL, Google, local models, ...) implements
this interface. ``chat`` is exposed in addition to ``translate`` so later
features such as the question-solver can reuse the same adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """A single chat message."""

    role: str
    content: str


# Human-readable language names used when building prompts.
LANG_NAMES = {
    "auto": "the source language (auto-detect)",
    "zh": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "ru": "Russian",
    "pt": "Portuguese",
    "it": "Italian",
}


def lang_name(code: str) -> str:
    return LANG_NAMES.get(code, code)


class TranslationProvider(ABC):
    """Common interface for all translation backends."""

    name: str = "base"

    def __init__(self, api_key: str, base_url: str, model: str, timeout: float = 30.0):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate ``text`` from ``source_lang`` to ``target_lang``."""

    @abstractmethod
    def chat(self, messages: list[ChatMessage]) -> str:
        """Send a raw chat conversation and return the assistant reply."""
