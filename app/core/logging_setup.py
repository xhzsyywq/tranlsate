"""Application logging setup.

Logs go to both the console and a rotating file under
``%APPDATA%\\AutoTranslate\\logs\\app.log`` so issues can be diagnosed after
the fact even when running via ``pythonw`` (no console).
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .config import config_dir

_configured = False


def setup_logging(level: int = logging.DEBUG) -> None:
    global _configured
    if _configured:
        return

    log_dir = config_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)

    _configured = True
    logging.getLogger(__name__).info("Logging initialized -> %s", log_file)

    # Silence noisy third-party libraries (they can leak request headers).
    for noisy in ("httpcore", "httpx", "urllib3", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
