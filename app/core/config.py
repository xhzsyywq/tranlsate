"""Configuration management.

Settings are persisted to ``%APPDATA%\\AutoTranslate\\config.json`` on Windows.
Environment variables (optionally loaded from a local ``.env``) override the
stored values, which is convenient for development and CI.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

APP_NAME = "AutoTranslate"


def config_dir() -> Path:
    """Return the per-user config directory, creating it if needed."""
    base = os.environ.get("APPDATA") or str(Path.home())
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return config_dir() / "config.json"


class AppConfig(BaseModel):
    """Persisted application settings."""

    provider: str = Field(default="openai")
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.deepseek.com")
    model: str = Field(default="deepseek-chat")
    source_lang: str = Field(default="auto")
    target_lang: str = Field(default="zh")
    ui_lang: str = Field(default="zh")
    timeout: float = Field(default=30.0)

    @classmethod
    def load(cls) -> "AppConfig":
        """Load config from disk, then apply environment overrides."""
        data: dict = {}
        path = config_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}

        env_map = {
            "provider": "AUTOTRANSLATE_PROVIDER",
            "api_key": "AUTOTRANSLATE_API_KEY",
            "base_url": "AUTOTRANSLATE_BASE_URL",
            "model": "AUTOTRANSLATE_MODEL",
            "source_lang": "AUTOTRANSLATE_SOURCE_LANG",
            "target_lang": "AUTOTRANSLATE_TARGET_LANG",
            "ui_lang": "AUTOTRANSLATE_UI_LANG",
        }
        for field, env_name in env_map.items():
            value = os.environ.get(env_name)
            if value:
                data[field] = value

        return cls(**data)

    def save(self) -> None:
        """Persist current settings to disk."""
        path = config_path()
        path.write_text(
            json.dumps(self.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
