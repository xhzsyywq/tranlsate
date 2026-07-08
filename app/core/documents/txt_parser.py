"""Plain-text parser: one segment per non-empty line, blank lines preserved."""

from __future__ import annotations

from pathlib import Path

from .base import DocumentParser, register


@register
class TxtParser(DocumentParser):
    extensions = (".txt", ".md")

    def __init__(self, path):
        super().__init__(path)
        self._lines: list[str] = []
        self._indices: list[int] = []  # indices of lines that are translatable

    def extract(self) -> list[str]:
        text = Path(self.path).read_text(encoding="utf-8", errors="replace")
        self._lines = text.splitlines()
        self._indices = [
            i for i, line in enumerate(self._lines) if line.strip()
        ]
        return [self._lines[i] for i in self._indices]

    def rebuild(self, translations: list[str], output_path) -> None:
        lines = list(self._lines)
        for idx, translated in zip(self._indices, translations):
            lines[idx] = translated
        Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
