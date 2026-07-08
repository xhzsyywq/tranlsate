"""Main window: dual text panes, language selectors, and translate button."""

from __future__ import annotations

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
from ..core.logging_setup import get_logger
from ..core.providers.base import LANG_NAMES
from ..features.screen_translate import ScreenTranslator
from . import i18n
from .i18n import lang_label, tr
from .settings_dialog import SettingsDialog
from .worker import TranslationTask

log = get_logger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, engine: TranslationEngine):
        super().__init__()
        self.engine = engine
        self._task: TranslationTask | None = None
        self._screen_translator = ScreenTranslator(engine)
        self._screen_translator.recognizing.connect(self._on_screen_recognizing)
        self._screen_translator.recognized.connect(self._on_screen_recognized)
        self._screen_translator.failed.connect(self._on_screen_failed)

        i18n.set_language(engine.config.ui_lang)

        self.resize(760, 480)

        self._build_menu()
        self._build_central()
        self._populate_lang_selectors()
        self._sync_lang_selectors()
        self.retranslate()

    # ------------------------------------------------------------------ UI
    def _build_menu(self) -> None:
        self.settings_action = QAction(self)
        self.settings_action.setShortcut("Ctrl+,")
        self.settings_action.triggered.connect(self.open_settings)
        self.file_menu = self.menuBar().addMenu("")
        self.screen_action = QAction(self)
        self.screen_action.setShortcut("Ctrl+Alt+Z")
        self.screen_action.triggered.connect(self.start_screen_translate)
        self.file_menu.addAction(self.screen_action)
        self.file_menu.addAction(self.settings_action)
        self.quit_action = QAction(self)
        self.quit_action.triggered.connect(self._quit)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.quit_action)

    def _build_central(self) -> None:
        self.source_lang = QComboBox()
        self.target_lang = QComboBox()

        self.swap_btn = QPushButton("\u21c4")
        self.swap_btn.setFixedWidth(40)
        self.swap_btn.clicked.connect(self._swap_languages)

        self.from_label = QLabel()
        self.to_label = QLabel()
        lang_bar = QHBoxLayout()
        lang_bar.addWidget(self.from_label)
        lang_bar.addWidget(self.source_lang, 1)
        lang_bar.addWidget(self.swap_btn)
        lang_bar.addWidget(self.to_label)
        lang_bar.addWidget(self.target_lang, 1)

        self.source_text = QTextEdit()
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)

        panes = QHBoxLayout()
        panes.addWidget(self.source_text)
        panes.addWidget(self.result_text)

        self.translate_btn = QPushButton()
        self.translate_btn.setShortcut("Ctrl+Return")
        self.translate_btn.clicked.connect(self.translate)

        self.screen_btn = QPushButton()
        self.screen_btn.clicked.connect(self.start_screen_translate)

        button_bar = QHBoxLayout()
        button_bar.addWidget(self.screen_btn)
        button_bar.addWidget(self.translate_btn, 1)

        layout = QVBoxLayout()
        layout.addLayout(lang_bar)
        layout.addLayout(panes, 1)
        layout.addLayout(button_bar)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

    def _populate_lang_selectors(self) -> None:
        for code in LANG_NAMES:
            self.source_lang.addItem(lang_label(code), code)
            if code != "auto":
                self.target_lang.addItem(lang_label(code), code)

    def retranslate(self) -> None:
        """Apply current-language strings to all widgets."""
        self.setWindowTitle(tr("app_title"))
        self.file_menu.setTitle(tr("menu_file"))
        self.screen_action.setText(tr("screen_translate"))
        self.settings_action.setText(tr("menu_settings"))
        self.quit_action.setText(tr("menu_quit"))
        self.from_label.setText(tr("from"))
        self.to_label.setText(tr("to"))
        self.swap_btn.setToolTip(tr("swap_tooltip"))
        self.source_text.setPlaceholderText(tr("source_placeholder"))
        self.result_text.setPlaceholderText(tr("result_placeholder"))
        self.translate_btn.setText(tr("translate"))
        self.screen_btn.setText(tr("screen_translate"))
        self.statusBar().showMessage(tr("status_ready"))
        for combo in (self.source_lang, self.target_lang):
            for i in range(combo.count()):
                combo.setItemText(i, lang_label(combo.itemData(i)))

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

    def start_screen_translate(self) -> None:
        """Trigger the screen region-selection + OCR translation flow."""
        self._screen_translator.start()

    def _on_screen_recognizing(self) -> None:
        log.info("Main window: OCR recognizing, bringing window to front")
        self.showNormal()
        self.activateWindow()
        self.raise_()
        self.statusBar().showMessage(tr("screen_recognizing"))

    def _on_screen_recognized(self, text: str) -> None:
        log.info("Main window: recognized text received (%d chars)", len(text))
        text = text.strip()
        if not text:
            log.warning("Main window: recognized text empty after strip")
            self.statusBar().showMessage(tr("screen_no_text"), 3000)
            return
        self.source_text.setPlainText(text)
        log.info("Main window: source box set, auto-translating")
        self.statusBar().showMessage(tr("status_done"), 2000)
        self.translate()

    def _on_screen_failed(self, message: str) -> None:
        log.error("Main window: screen translate failed: %s", message)
        self.statusBar().showMessage(tr("status_failed"), 5000)
        QMessageBox.critical(self, tr("status_failed"), message)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.engine.config, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            new_config = dialog.updated_config()
            new_config.save()
            self.engine.reload(new_config)
            i18n.set_language(new_config.ui_lang)
            self._sync_lang_selectors()
            self.retranslate()
            tray = getattr(self, "tray", None)
            if tray is not None:
                tray.retranslate()
            self.statusBar().showMessage(tr("status_settings_saved"), 3000)

    def translate(self) -> None:
        text = self.source_text.toPlainText().strip()
        if not text:
            self.statusBar().showMessage(tr("status_nothing"), 3000)
            return
        if not self.engine.config.api_key:
            QMessageBox.warning(
                self,
                tr("api_key_required_title"),
                tr("api_key_required_body"),
            )
            return

        source = self.source_lang.currentData()
        target = self.target_lang.currentData()

        self.translate_btn.setEnabled(False)
        self.statusBar().showMessage(tr("status_translating"))

        self._task = TranslationTask(self.engine, text, source, target)
        self._task.worker.finished.connect(self._on_finished)
        self._task.worker.failed.connect(self._on_failed)
        self._task.thread.finished.connect(self._on_thread_done)
        self._task.start()

    def _on_finished(self, result: str) -> None:
        self.result_text.setPlainText(result)
        self.statusBar().showMessage(tr("status_done"), 3000)

    def _on_failed(self, message: str) -> None:
        self.result_text.clear()
        self.statusBar().showMessage(tr("status_failed"), 5000)
        QMessageBox.critical(self, tr("translation_failed_title"), message)

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
                tr("tray_minimized_title"),
                tr("tray_minimized_body"),
                msecs=2000,
            )
        else:
            event.accept()
