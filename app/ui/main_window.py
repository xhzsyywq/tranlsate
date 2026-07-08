"""Main window: dual text panes, language selectors, and translate button."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..core.config import AppConfig
from ..core.engine import TranslationEngine
from ..core.providers.base import LANG_NAMES
from .settings_dialog import SettingsDialog
from .worker import TranslationTask


class MainWindow(QMainWindow):
    def __init__(self, engine: TranslationEngine):
        super().__init__()
        self.engine = engine
        self._task: TranslationTask | None = None

        self.setWindowTitle("AutoTranslate")
        self.resize(760, 480)

        self._build_menu()
        self._build_central()
        self._sync_lang_selectors()

    # ------------------------------------------------------------------ UI
    def _build_menu(self) -> None:
        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        menu = self.menuBar().addMenu("File")
        menu.addAction(settings_action)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        menu.addSeparator()
        menu.addAction(quit_action)

    def _build_central(self) -> None:
        self.source_lang = QComboBox()
        self.target_lang = QComboBox()
        for code, name in LANG_NAMES.items():
            self.source_lang.addItem(f"{name} ({code})", code)
            if code != "auto":
                self.target_lang.addItem(f"{name} ({code})", code)

        swap_btn = QPushButton("\u21c4")
        swap_btn.setFixedWidth(40)
        swap_btn.setToolTip("Swap languages")
        swap_btn.clicked.connect(self._swap_languages)

        lang_bar = QHBoxLayout()
        lang_bar.addWidget(QLabel("From"))
        lang_bar.addWidget(self.source_lang, 1)
        lang_bar.addWidget(swap_btn)
        lang_bar.addWidget(QLabel("To"))
        lang_bar.addWidget(self.target_lang, 1)

        self.source_text = QTextEdit()
        self.source_text.setPlaceholderText("Enter text to translate...")
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Translation appears here...")

        panes = QHBoxLayout()
        panes.addWidget(self.source_text)
        panes.addWidget(self.result_text)

        self.translate_btn = QPushButton("Translate")
        self.translate_btn.setShortcut("Ctrl+Return")
        self.translate_btn.clicked.connect(self.translate)

        layout = QVBoxLayout()
        layout.addLayout(lang_bar)
        layout.addLayout(panes, 1)
        layout.addWidget(self.translate_btn)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.statusBar().showMessage("Ready")

    def _sync_lang_selectors(self) -> None:
        self._select_lang(self.source_lang, self.engine.config.source_lang)
        self._select_lang(self.target_lang, self.engine.config.target_lang)

    @staticmethod
    def _select_lang(combo: QComboBox, code: str) -> None:
        idx = combo.findData(code)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    # -------------------------------------------------------------- actions
    def _swap_languages(self) -> None:
        src = self.source_lang.currentData()
        tgt = self.target_lang.currentData()
        if src == "auto":
            return
        self._select_lang(self.source_lang, tgt)
        self._select_lang(self.target_lang, src)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.engine.config, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            new_config = dialog.updated_config()
            new_config.save()
            self.engine.reload(new_config)
            self._sync_lang_selectors()
            self.statusBar().showMessage("Settings saved", 3000)

    def translate(self) -> None:
        text = self.source_text.toPlainText().strip()
        if not text:
            self.statusBar().showMessage("Nothing to translate", 3000)
            return
        if not self.engine.config.api_key:
            QMessageBox.warning(
                self,
                "API key required",
                "Please set your API key in Settings (Ctrl+,) first.",
            )
            return

        source = self.source_lang.currentData()
        target = self.target_lang.currentData()

        self.translate_btn.setEnabled(False)
        self.statusBar().showMessage("Translating...")

        self._task = TranslationTask(self.engine, text, source, target)
        self._task.worker.finished.connect(self._on_finished)
        self._task.worker.failed.connect(self._on_failed)
        self._task.thread.finished.connect(self._on_thread_done)
        self._task.start()

    def _on_finished(self, result: str) -> None:
        self.result_text.setPlainText(result)
        self.statusBar().showMessage("Done", 3000)

    def _on_failed(self, message: str) -> None:
        self.result_text.clear()
        self.statusBar().showMessage("Translation failed", 5000)
        QMessageBox.critical(self, "Translation failed", message)

    def _on_thread_done(self) -> None:
        self.translate_btn.setEnabled(True)
        self._task = None

    def _quit(self) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.quit()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        """Minimize to tray instead of quitting, if a tray icon is active."""
        tray = getattr(self, "tray", None)
        if tray is not None and tray.isVisible():
            event.ignore()
            self.hide()
            tray.showMessage(
                "AutoTranslate",
                "Still running in the system tray.",
                msecs=2000,
            )
        else:
            event.accept()
