"""SubRip (.srt) subtitle parser.

Extracts each cue's text (timings and indices preserved) so subtitles can be
translated while keeping the exact timeline.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import DocumentParser, register

_INDEX_RE = re.compile(r"^\d+$")
_TIME_RE = re.compile(r"-->")


class _Cue:
    __slots__ = ("index", "timing", "lines")

    def __init__(self, index: str, timing: str, lines: list[str]):
        self.index = index
        self.timing = timing
        self.lines = lines


@register
class SrtParser(DocumentParser):
    extensions = (".srt",)

    def __init__(self, path):
        super().__init__(path)
        self._cues: list[_Cue] = []

    def _parse(self) -> None:
        text = Path(self.path).read_text(encoding="utf-8", errors="replace")
        blocks = re.split(r"\r?\n\r?\n", text.strip())
        self._cues = []
        for block in blocks:
            lines = [ln for ln in block.splitlines()]
            if not lines:
                continue
            index = ""
            timing = ""
            rest = lines
            if _INDEX_RE.match(lines[0].strip()):
                index = lines[0].strip()
                rest = lines[1:]
            if rest and _TIME_RE.search(rest[0]):
                timing = rest[0]
                rest = rest[1:]
            self._cues.append(_Cue(index, timing, rest))

    def extract(self) -> list[str]:
        self._parse()
        # One segment per cue (join multi-line cue text with newline).
        return ["\n".join(cue.lines) for cue in self._cues]

    def rebuild(self, translations: list[str], output_path) -> None:
        out_blocks: list[str] = []
        for i, cue in enumerate(self._cues):
            translated = translations[i] if i < len(translations) else "\n".join(cue.lines)
            parts: list[str] = []
            if cue.index:
                parts.append(cue.index)
            if cue.timing:
                parts.append(cue.timing)
            parts.append(translated)
            out_blocks.append("\n".join(parts))
        Path(output_path).write_text("\n\n".join(out_blocks) + "\n", encoding="utf-8")
