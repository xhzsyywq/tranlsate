"""Output writers for translated documents.

Supports writing the translated segments either in the source file's original
format (``same``) or converting to a chosen format (``txt``/``docx``/``srt``).
The ``same`` mode delegates back to the source parser's ``rebuild``.
"""

from __future__ import annotations

from pathlib import Path

# Output format identifiers and the file extension each produces.
OUTPUT_FORMATS: dict[str, str] = {
    "same": "",  # keep the source extension
    "txt": ".txt",
    "docx": ".docx",
    "srt": ".srt",
}


def resolve_output_path(
    source: Path,
    segments_count: int,
    target_lang: str,
    output_dir: str,
    output_format: str,
    parser,
) -> Path:
    """Compute the final output path from user settings."""
    directory = Path(output_dir) if output_dir else source.parent
    directory.mkdir(parents=True, exist_ok=True)

    if output_format == "same" or output_format not in OUTPUT_FORMATS:
        default = parser.default_output_path(target_lang)
        return directory / default.name

    ext = OUTPUT_FORMATS[output_format]
    return directory / f"{source.stem}.{target_lang}{ext}"


def write_output(
    parser,
    segments: list[str],
    translations: list[str],
    output_path: Path,
    output_format: str,
) -> Path:
    """Write ``translations`` to ``output_path`` in the requested format.

    Returns the actual path written (may differ, e.g. PDF -> txt).
    """
    if output_format == "same" or output_format not in OUTPUT_FORMATS:
        parser.rebuild(translations, output_path)
        if not output_path.exists():
            alt = output_path.with_suffix(".txt")
            if alt.exists():
                return alt
        return output_path

    if output_format == "txt":
        _write_txt(translations, output_path)
    elif output_format == "srt":
        _write_srt(parser, segments, translations, output_path)
    elif output_format == "docx":
        _write_docx(translations, output_path)
    return output_path


def _write_txt(translations: list[str], output_path: Path) -> None:
    body = "\n".join(t for t in translations if t is not None)
    output_path.write_text(body + "\n", encoding="utf-8")


def _write_docx(translations: list[str], output_path: Path) -> None:
    from docx import Document

    doc = Document()
    for translated in translations:
        doc.add_paragraph(translated)
    doc.save(str(output_path))


def _write_srt(parser, segments, translations: list[str], output_path: Path) -> None:
    # If the source was SRT, reuse its rebuild to keep timings; otherwise emit
    # a simple sequential SRT with one-second cues.
    if hasattr(parser, "_cues") and getattr(parser, "_cues"):
        parser.rebuild(translations, output_path)
        return
    lines: list[str] = []
    for i, translated in enumerate(translations, start=1):
        start = _fmt_time(i - 1)
        end = _fmt_time(i)
        lines.append(f"{i}\n{start} --> {end}\n{translated}\n")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _fmt_time(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d},000"
