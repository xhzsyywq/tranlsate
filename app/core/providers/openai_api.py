"""OpenAI-compatible chat completions adapter.

This works with any backend that implements the OpenAI Chat Completions API,
including DeepSeek (the default), OpenAI itself, and many self-hosted gateways.
Switching backend is just a matter of changing ``base_url`` and ``model``.
"""

from __future__ import annotations

import httpx

from .base import ChatMessage, TranslationProvider, lang_name


class OpenAICompatibleProvider(TranslationProvider):
    name = "openai"

    def _endpoint(self) -> str:
        return self.base_url.rstrip("/") + "/v1/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, messages: list[dict], temperature: float = 0.3) -> str:
        if not self.api_key:
            raise ValueError("API key is not configured.")
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(self._endpoint(), headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text.strip():
            return ""
        src = lang_name(source_lang)
        tgt = lang_name(target_lang)
        system = (
            "You are a professional translation engine. Translate the user's "
            f"text from {src} to {tgt}. Output only the translation, with no "
            "explanations, notes, or quotation marks."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ]
        return self._request(messages)

    def chat(self, messages: list[ChatMessage]) -> str:
        payload = [{"role": m.role, "content": m.content} for m in messages]
        return self._request(payload, temperature=0.7)

    def solve(self, question: str, answer_lang: str = "zh") -> str:
        """Answer a question (e.g. from OCR) using the chat model.

        The reply starts with a concise final answer on the first line
        (prefixed with a marker) followed by a short explanation, so callers
        can extract just the answer for auto-fill.
        """
        if not question.strip():
            return ""
        lang = lang_name(answer_lang)
        system = (
            "You are an expert exam solver. Read the question (which may include "
            "multiple-choice options) and answer it correctly. Respond in "
            f"{lang}. Format your reply exactly as:\n"
            "ANSWER: <the concise final answer, e.g. the option letter or value>\n"
            "EXPLANATION: <a brief explanation>"
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ]
        return self._request(messages, temperature=0.2)
