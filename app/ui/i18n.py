"""Lightweight internationalization for the GUI.

Provides a global current-language state and a ``tr()`` lookup helper. Default
language is Simplified Chinese (``zh``). New strings just need an entry in each
language dict; missing keys fall back to the key itself.
"""

from __future__ import annotations

# Supported UI languages: code -> native display name.
UI_LANGUAGES: dict[str, str] = {
    "zh": "\u7b80\u4f53\u4e2d\u6587",
    "en": "English",
}

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "zh": {
        # Window / menu
        "app_title": "\u81ea\u52a8\u7ffb\u8bd1",
        "menu_file": "\u6587\u4ef6",
        "menu_settings": "\u8bbe\u7f6e",
        "menu_quit": "\u9000\u51fa",
        # Main window
        "from": "\u6e90\u8bed\u8a00",
        "to": "\u76ee\u6807\u8bed\u8a00",
        "swap_tooltip": "\u4ea4\u6362\u8bed\u8a00",
        "source_placeholder": "\u8f93\u5165\u8981\u7ffb\u8bd1\u7684\u6587\u672c...",
        "result_placeholder": "\u8bd1\u6587\u663e\u793a\u5728\u8fd9\u91cc...",
        "translate": "\u7ffb\u8bd1",
        # Status bar
        "status_ready": "\u5c31\u7eea",
        "status_translating": "\u7ffb\u8bd1\u4e2d...",
        "status_done": "\u5b8c\u6210",
        "status_nothing": "\u6ca1\u6709\u53ef\u7ffb\u8bd1\u7684\u5185\u5bb9",
        "status_failed": "\u7ffb\u8bd1\u5931\u8d25",
        "status_settings_saved": "\u8bbe\u7f6e\u5df2\u4fdd\u5b58",
        # Dialogs
        "api_key_required_title": "\u9700\u8981 API \u5bc6\u94a5",
        "api_key_required_body": "\u8bf7\u5148\u5728\u201c\u8bbe\u7f6e\u201d\uff08Ctrl+,\uff09\u4e2d\u586b\u5165 API \u5bc6\u94a5\u3002",
        "translation_failed_title": "\u7ffb\u8bd1\u5931\u8d25",
        # Settings dialog
        "settings_title": "\u8bbe\u7f6e",
        "settings_provider": "\u63d0\u4f9b\u5546",
        "settings_api_key": "API \u5bc6\u94a5",
        "settings_base_url": "API \u5730\u5740",
        "settings_model": "\u6a21\u578b",
        "settings_default_source": "\u9ed8\u8ba4\u6e90\u8bed\u8a00",
        "settings_default_target": "\u9ed8\u8ba4\u76ee\u6807\u8bed\u8a00",
        "settings_ui_lang": "\u754c\u9762\u8bed\u8a00",
        "settings_ui_lang_hint": "\uff08\u91cd\u542f\u540e\u5b8c\u5168\u751f\u6548\uff09",
        "ok": "\u786e\u5b9a",
        "cancel": "\u53d6\u6d88",
        # Tray
        "tray_show": "\u663e\u793a",
        "tray_tooltip": "\u81ea\u52a8\u7ffb\u8bd1",
        "tray_minimized_title": "\u81ea\u52a8\u7ffb\u8bd1",
        "tray_minimized_body": "\u7a0b\u5e8f\u4ecd\u5728\u7cfb\u7edf\u6258\u76d8\u4e2d\u8fd0\u884c\u3002",
        # Screen translation
        "screen_translate": "\u5c4f\u5e55\u7ffb\u8bd1",
        "screen_translate_hint": "\uff08\u5feb\u6377\u952e Ctrl+Alt+Z\uff09",
        "screen_result_title": "\u5c4f\u5e55\u7ffb\u8bd1\u7ed3\u679c",
        "screen_recognized": "\u8bc6\u522b\u6587\u672c",
        "screen_translation": "\u8bd1\u6587",
        "screen_recognizing": "\u6b63\u5728\u8bc6\u522b...",
        "screen_no_text": "\u672a\u8bc6\u522b\u5230\u6587\u672c",
        "screen_copy": "\u590d\u5236\u8bd1\u6587",
        # Language names (for selectors)
        "lang_auto": "\u81ea\u52a8\u68c0\u6d4b",
        "lang_zh": "\u4e2d\u6587\uff08\u7b80\u4f53\uff09",
        "lang_zh-tw": "\u4e2d\u6587\uff08\u7e41\u4f53\uff09",
        "lang_en": "\u82f1\u8bed",
        "lang_ja": "\u65e5\u8bed",
        "lang_ko": "\u97e9\u8bed",
        "lang_fr": "\u6cd5\u8bed",
        "lang_de": "\u5fb7\u8bed",
        "lang_es": "\u897f\u73ed\u7259\u8bed",
        "lang_ru": "\u4fc4\u8bed",
        "lang_pt": "\u8461\u8404\u7259\u8bed",
        "lang_it": "\u610f\u5927\u5229\u8bed",
    },
    "en": {
        "app_title": "AutoTranslate",
        "menu_file": "File",
        "menu_settings": "Settings",
        "menu_quit": "Quit",
        "from": "From",
        "to": "To",
        "swap_tooltip": "Swap languages",
        "source_placeholder": "Enter text to translate...",
        "result_placeholder": "Translation appears here...",
        "translate": "Translate",
        "status_ready": "Ready",
        "status_translating": "Translating...",
        "status_done": "Done",
        "status_nothing": "Nothing to translate",
        "status_failed": "Translation failed",
        "status_settings_saved": "Settings saved",
        "api_key_required_title": "API key required",
        "api_key_required_body": "Please set your API key in Settings (Ctrl+,) first.",
        "translation_failed_title": "Translation failed",
        "settings_title": "Settings",
        "settings_provider": "Provider",
        "settings_api_key": "API Key",
        "settings_base_url": "Base URL",
        "settings_model": "Model",
        "settings_default_source": "Default source",
        "settings_default_target": "Default target",
        "settings_ui_lang": "UI language",
        "settings_ui_lang_hint": "(applies fully after restart)",
        "ok": "OK",
        "cancel": "Cancel",
        "tray_show": "Show",
        "tray_tooltip": "AutoTranslate",
        "tray_minimized_title": "AutoTranslate",
        "tray_minimized_body": "Still running in the system tray.",
        "screen_translate": "Screen translate",
        "screen_translate_hint": "(Ctrl+Alt+Z)",
        "screen_result_title": "Screen translation",
        "screen_recognized": "Recognized text",
        "screen_translation": "Translation",
        "screen_recognizing": "Recognizing...",
        "screen_no_text": "No text detected",
        "screen_copy": "Copy translation",
        "lang_auto": "Auto-detect",
        "lang_zh": "Chinese (Simplified)",
        "lang_zh-tw": "Chinese (Traditional)",
        "lang_en": "English",
        "lang_ja": "Japanese",
        "lang_ko": "Korean",
        "lang_fr": "French",
        "lang_de": "German",
        "lang_es": "Spanish",
        "lang_ru": "Russian",
        "lang_pt": "Portuguese",
        "lang_it": "Italian",
    },
}

_current_lang = "zh"


def set_language(code: str) -> None:
    """Set the active UI language. Falls back to zh if unknown."""
    global _current_lang
    _current_lang = code if code in _TRANSLATIONS else "zh"


def current_language() -> str:
    return _current_lang


def tr(key: str) -> str:
    """Look up ``key`` in the current language, falling back to en then key."""
    table = _TRANSLATIONS.get(_current_lang, {})
    if key in table:
        return table[key]
    return _TRANSLATIONS["en"].get(key, key)


def lang_label(code: str) -> str:
    """Localized display name for a translation language code."""
    return tr(f"lang_{code}")
