"""Settings dialog: configure provider, API key, model, and languages."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from ..core.config import AppConfig
from ..core.providers.base import LANG_NAMES
from ..core.providers.registry import available_providers
from .i18n import UI_LANGUAGES, lang_label, tr


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("settings_title"))
        self.setMinimumWidth(420)
        self._config = config

        self.provider_edit = QComboBox()
        self.provider_edit.addItems(available_providers())
        self.provider_edit.setCurrentText(config.provider)

        self.api_key_edit = QLineEdit(config.api_key)
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("sk-...")

        self.base_url_edit = QLineEdit(config.base_url)
        self.model_edit = QLineEdit(config.model)

        self.ui_lang_edit = QComboBox()
        for code, name in UI_LANGUAGES.items():
            self.ui_lang_edit.addItem(name, code)
        self._select_data(self.ui_lang_edit, config.ui_lang)

        self.source_edit = QComboBox()
        self.target_edit = QComboBox()
        for code in LANG_NAMES:
            self.source_edit.addItem(lang_label(code), code)
            if code != "auto":
                self.target_edit.addItem(lang_label(code), code)
        self._select_data(self.source_edit, config.source_lang)
        self._select_data(self.target_edit, config.target_lang)

        form = QFormLayout()
        form.addRow(tr("settings_provider"), self.provider_edit)
        form.addRow(tr("settings_api_key"), self.api_key_edit)
        form.addRow(tr("settings_base_url"), self.base_url_edit)
        form.addRow(tr("settings_model"), self.model_edit)
        form.addRow(
            f"{tr('settings_ui_lang')} {tr('settings_ui_lang_hint')}", self.ui_lang_edit
        )
        form.addRow(tr("settings_default_source"), self.source_edit)
        form.addRow(tr("settings_default_target"), self.target_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("ok"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    @staticmethod
    def _select_data(combo: QComboBox, code: str) -> None:
        idx = combo.findData(code)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def updated_config(self) -> AppConfig:
        """Return a new AppConfig reflecting the dialog's current values."""
        return self._config.model_copy(
            update={
                "provider": self.provider_edit.currentText(),
                "api_key": self.api_key_edit.text().strip(),
                "base_url": self.base_url_edit.text().strip(),
                "model": self.model_edit.text().strip(),
                "ui_lang": self.ui_lang_edit.currentData(),
                "source_lang": self.source_edit.currentData(),
                "target_lang": self.target_edit.currentData(),
            }
        )
