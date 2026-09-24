from __future__ import annotations

from pprint import pformat
from typing import Any

from PySide6.QtWidgets import QApplication, QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


def format_debug_output(data: Any) -> str:
    """把解析结果整理成适合放进 debug 页的多行文本。"""

    return pformat(data, width=100, sort_dicts=False)


class DebugTab(QWidget):
    """专门显示解析结果调试文本的页签。"""

    def __init__(self) -> None:
        super().__init__()

        self._is_paused = False

        self.pause_button = QPushButton('暂停')
        self.pause_button.clicked.connect(self._toggle_pause)

        self.copy_button = QPushButton('复制')
        self.copy_button.clicked.connect(self._copy_to_clipboard)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)

        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.addWidget(self.pause_button)
        self.toolbar_layout.addWidget(self.copy_button)
        self.toolbar_layout.addStretch()

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.toolbar_layout)
        self.main_layout.addWidget(self.output)
        self.setLayout(self.main_layout)

    def _toggle_pause(self) -> None:
        self._is_paused = not self._is_paused
        self.pause_button.setText('继续' if self._is_paused else '暂停')

    def _copy_to_clipboard(self) -> None:
        QApplication.clipboard().setText(self.output.toPlainText())

    def set_debug_text(self, text: str) -> None:
        if self._is_paused:
            return

        self.output.setPlainText(text)

    def refresh_from_decode_snapshot(self, snapshot: dict[str, Any]) -> None:
        decoded_data = snapshot.get('decoded_data')
        if decoded_data is None:
            self.set_debug_text('')
            return

        self.set_debug_text(format_debug_output(decoded_data))
