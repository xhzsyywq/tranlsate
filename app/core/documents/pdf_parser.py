"""PDF parser.

Extracts text page by page with pypdf. PDF layout cannot be reliably rewritten
in place, so the rebuilt output is a UTF-8 ``.txt`` file with page markers,
which is the pragmatic choice for reading translated content.
"""

from __future__ import annotations

from pathlib import Path

from .base import DocumentParser, register


@register
class PdfParser(DocumentParser):
    extensions = (".pdf",)

    def __init__(self, path):
        super().__init__(path)
        self._pages: list[str] = []

    def extract(self) -> list[str]:
        from pypdf import PdfReader

        reader = PdfReader(str(self.path))
        self._pages = []
        for page in reader.pages:
            text = (page.extract_text() or "").strip()
            self._pages.append(text)
        # One segment per non-empty page.
        return [p for p in self._pages if p]

    def rebuild(self, translations: list[str], output_path) -> None:
        out = Path(output_path).with_suffix(".txt")
        blocks: list[str] = []
        it = iter(translations)
        page_no = 0
        for original in self._pages:
            page_no += 1
            if original:
                translated = next(it, "")
                blocks.append(f"--- Page {page_no} ---\n{translated}")
        out.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")

    def default_output_path(self, target_lang: str) -> Path:
        stem = self.path.stem
        return self.path.with_name(f"{stem}.{target_lang}.txt")
