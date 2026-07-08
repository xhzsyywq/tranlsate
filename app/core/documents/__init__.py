"""Document parsers for batch translation.

Each parser extracts a list of translatable text segments from a file, then
rebuilds the file with translated segments while preserving the original
structure (paragraphs, subtitle timings, page order, etc.).
"""

from .base import DocumentParser, get_parser, supported_extensions

__all__ = ["DocumentParser", "get_parser", "supported_extensions"]
