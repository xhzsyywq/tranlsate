"""Base classes and registry for document parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class DocumentParser(ABC):
    """Extracts translatable segments from a file and rebuilds it.

    Usage::

        parser = get_parser(path)
        segments = parser.extract()          # list[str]
        # translate each segment...
        parser.rebuild(translations, out)    # write output file
    """

    #: File extensions (lowercase, with dot) this parser handles.
    extensions: tuple[str, ...] = ()

    def __init__(self, path: str | Path):
        self.path = Path(path)

    @abstractmethod
    def extract(self) -> list[str]:
        """Return the list of translatable text segments in document order."""

    @abstractmethod
    def rebuild(self, translations: list[str], output_path: str | Path) -> None:
        """Write a new file at ``output_path`` using ``translations``.

        ``translations`` must have the same length and order as :meth:`extract`.
        """

    def default_output_path(self, target_lang: str) -> Path:
        """Suggested output path: ``name.<lang>.ext`` next to the source."""
        stem = self.path.stem
        suffix = self.path.suffix
        return self.path.with_name(f"{stem}.{target_lang}{suffix}")


_PARSERS: list[type[DocumentParser]] = []


def register(cls: type[DocumentParser]) -> type[DocumentParser]:
    _PARSERS.append(cls)
    return cls


def supported_extensions() -> list[str]:
    exts: list[str] = []
    for cls in _PARSERS:
        exts.extend(cls.extensions)
    return sorted(set(exts))


def get_parser(path: str | Path) -> DocumentParser:
    ext = Path(path).suffix.lower()
    for cls in _PARSERS:
        if ext in cls.extensions:
            return cls(path)
    raise ValueError(f"Unsupported document type: {ext}")


def _register_builtin() -> None:
    # Imported here to avoid circular imports and to populate the registry.
    from . import docx_parser, pdf_parser, srt_parser, txt_parser  # noqa: F401


_register_builtin()
