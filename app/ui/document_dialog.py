"""Document batch translation dialog.

Lets the user pick a file, choose source/target languages, output folder and
output format, translate all segments concurrently with a progress bar, and
open the output folder when finished. Output preferences are saved to config.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from ..core.documents import get_parser, supported_extensions
from ..core.documents.writers import OUTPUT_FORMATS
from ..core.engine import TranslationEngine
from ..features.doc_worker import DocTranslateTask
from .i18n import lang_label, tr
from ..core.providers.base import LANG_NAMES


class DocumentDialog(QDialog):
    def __init__(self, engine: TranslationEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._task: DocTranslateTask | None = None
        self._input_path: str | None = None
        self._output_path: str | None = None

        self.setWindowTitle(tr("doc_title"))
        self.setMinimumWidth(560)

        # File row
        self.file_label = QLabel(tr("doc_no_file"))
        self.choose_btn = QPushButton(tr("doc_choose_file"))
        self.choose_btn.clicked.connect(self._choose_file)
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_label, 1)
        file_row.addWidget(self.choose_btn)

        # Language row
        self.from_label = QLabel(tr("from"))
        self.to_label = QLabel(tr("to"))
        self.source_lang = QComboBox()
        self.target_lang = QComboBox()
        for code in LANG_NAMES:
            self.source_lang.addItem(lang_label(code), code)
            if code != "auto":
                self.target_lang.addItem(lang_label(code), code)
        self._select_data(self.source_lang, engine.config.source_lang)
        self._select_data(self.target_lang, engine.config.target_lang)
        lang_row = QHBoxLayout()
        lang_row.addWidget(self.from_label)
        lang_row.addWidget(self.source_lang, 1)
        lang_row.addWidget(self.to_label)
        lang_row.addWidget(self.target_lang, 1)

        # Output directory row
        self.dir_label = QLabel(tr("doc_output_dir"))
        self.dir_edit = QLineEdit(engine.config.doc_output_dir)
        self.dir_edit.setPlaceholderText(tr("doc_output_dir_default"))
        self.dir_btn = QPushButton(tr("doc_choose_dir"))
        self.dir_btn.clicked.connect(self._choose_dir)
        dir_row = QHBoxLayout()
        dir_row.addWidget(self.dir_label)
        dir_row.addWidget(self.dir_edit, 1)
        dir_row.addWidget(self.dir_btn)

        # Output format row
        self.fmt_label = QLabel(tr("doc_output_format"))
        self.fmt_combo = QComboBox()
        for key in OUTPUT_FORMATS:
            self.fmt_combo.addItem(tr(f"fmt_{key}"), key)
        self._select_data(self.fmt_combo, engine.config.doc_output_format)
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(self.fmt_label)
        fmt_row.addWidget(self.fmt_combo, 1)

        # Progress
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.status_label = QLabel("")

        # Buttons
        self.start_btn = QPushButton(tr("doc_start"))
        self.start_btn.clicked.connect(self._start)
        self.cancel_btn = QPushButton(tr("doc_cancel"))
        self.cancel_btn.clicked.connect(self._cancel)
        self.cancel_btn.setEnabled(False)
        self.open_btn = QPushButton(tr("doc_open_output"))
        self.open_btn.clicked.connect(self._open_output)
        self.open_btn.setEnabled(False)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.open_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(file_row)
        layout.addLayout(lang_row)
        layout.addLayout(dir_row)
        layout.addLayout(fmt_row)
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)
        layout.addLayout(btn_row)

    @staticmethod
    def _select_data(combo: QComboBox, code: str) -> None:
        idx = combo.findData(code)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _choose_file(self) -> None:
        exts = " ".join(f"*{e}" for e in supported_extensions())
        filter_str = f"{tr('doc_filter')} ({exts})"
        path, _ = QFileDialog.getOpenFileName(self, tr("doc_choose_file"), "", filter_str)
        if path:
            self._input_path = path
            self.file_label.setText(os.path.basename(path))
            self.open_btn.setEnabled(False)
            self.progress.setValue(0)
            self.status_label.setText("")

    def _choose_dir(self) -> None:
        start = self.dir_edit.text() or (
            os.path.dirname(self._input_path) if self._input_path else ""
        )
        path = QFileDialog.getExistingDirectory(self, tr("doc_choose_dir"), start)
        if path:
            self.dir_edit.setText(path)

    def _persist_prefs(self) -> None:
        cfg = self.engine.config
        cfg.doc_output_dir = self.dir_edit.text().strip()
        cfg.doc_output_format = self.fmt_combo.currentData()
        cfg.save()

    def _start(self) -> None:
        if not self._input_path:
            QMessageBox.information(self, tr("doc_title"), tr("doc_select_prompt"))
            return
        if not self.engine.config.api_key:
            QMessageBox.warning(
                self, tr("api_key_required_title"), tr("api_key_required_body")
            )
            return

        self._persist_prefs()
        source = self.source_lang.currentData()
        target = self.target_lang.currentData()
        output_dir = self.dir_edit.text().strip()
        output_format = self.fmt_combo.currentData()

        self.start_btn.setEnabled(False)
        self.choose_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress.setValue(0)

        self._task = DocTranslateTask(
            self.engine,
            self._input_path,
            source,
            target,
            output_dir,
            output_format,
            self.engine.config.max_workers,
        )
        self._task.worker.progress.connect(self._on_progress)
        self._task.worker.finished.connect(self._on_finished)
        self._task.worker.failed.connect(self._on_failed)
        self._task.thread.finished.connect(self._on_thread_done)
        self._task.start()

    def _cancel(self) -> None:
        if self._task is not None:
            self._task.worker.cancel()
            self.cancel_btn.setEnabled(False)

    def _on_progress(self, done: int, total: int) -> None:
        self.progress.setMaximum(max(total, 1))
        self.progress.setValue(done)
        self.status_label.setText(tr("doc_progress").format(done=done, total=total))

    def _on_finished(self, output_path: str) -> None:
        self._output_path = output_path
        self.status_label.setText(tr("doc_done").format(path=output_path))
        self.open_btn.setEnabled(True)

    def _on_failed(self, message: str) -> None:
        if message == "cancelled":
            self.status_label.setText(tr("doc_cancelled"))
        else:
            self.status_label.setText(tr("doc_failed"))
            QMessageBox.critical(self, tr("doc_failed"), message)

    def _on_thread_done(self) -> None:
        self.start_btn.setEnabled(True)
        self.choose_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self._task = None

    def _open_output(self) -> None:
        if self._output_path and Path(self._output_path).exists():
            folder = str(Path(self._output_path).parent)
            os.startfile(folder)  # noqa: S606 - Windows explorer open
