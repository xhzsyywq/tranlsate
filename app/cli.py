"""Command-line interface for verifying the translation pipeline.

Examples
--------
    python -m app.cli --text "Hello, world" --to zh
    python -m app.cli --to en --from zh    # then type/pipe text via stdin
    python -m app.cli --show-config
"""

from __future__ import annotations

import argparse
import sys

from .core.config import AppConfig
from .core.engine import TranslationEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.cli", description="AutoTranslate command-line interface"
    )
    parser.add_argument("--text", "-t", help="Text to translate. If omitted, reads stdin.")
    parser.add_argument("--from", dest="source", help="Source language code (e.g. auto, en).")
    parser.add_argument("--to", dest="target", help="Target language code (e.g. zh, en).")
    parser.add_argument(
        "--show-config", action="store_true", help="Print effective configuration and exit."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = AppConfig.load()

    if args.show_config:
        safe = config.model_dump()
        if safe.get("api_key"):
            safe["api_key"] = "***" + safe["api_key"][-4:]
        for key, value in safe.items():
            print(f"{key}: {value}")
        return 0

    text = args.text if args.text is not None else sys.stdin.read()
    if not text.strip():
        print("No input text provided.", file=sys.stderr)
        return 1

    engine = TranslationEngine(config)
    try:
        result = engine.translate(text, args.source, args.target)
    except Exception as exc:  # noqa: BLE001 - surface any backend error to user
        print(f"Translation failed: {exc}", file=sys.stderr)
        return 2

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
