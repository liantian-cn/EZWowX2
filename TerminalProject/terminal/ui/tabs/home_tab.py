from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...embedded_assets import get_logo_pixmap
from ...keyboard import WindowRecord
from ...rotation import ALL_ROTATIONS
from ...rotation.base import BaseRotation


class HomeTab(QWidget):
    """首页页。"""

    start_clicked = Signal()
    stop_clicked = Signal()
    monitor_changed = Signal(object)
    open_title_editor_clicked = Signal()
    refresh_windows_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.left_panel = QWidget()

        self.logo_container = QWidget()
        self.logo_container.setFixedSize(300, 300)
        self.logo_layout = QVBoxLayout()
        self.logo_layout.setContentsMargins(20, 20, 20, 20)
        self.logo_layout.setSpacing(0)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_pixmap = get_logo_pixmap()
        self.logo_label.setPixmap(
            logo_pixmap.scaled(
                260,
                260,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.logo_layout.addWidget(self.logo_label)
        self.logo_container.setLayout(self.logo_layout)

        self.info_container = QWidget()
        self.info_layout = QVBoxLayout()
        self.info_layout.setContentsMargins(20, 0, 20, 0)
        self.info_layout.setSpacing(6)

        self.info_title_label = QLabel('T.E.R.M.I.N.A.L')
        info_title_font = QFont('Microsoft YaHei')
        info_title_font.setPixelSize(18)
        self.info_title_label.setFont(info_title_font)

        self.info_body_label = QLabel(
            '\n'
            'DejaVu的MATRIX裂开了一条缝。那边，有人类不该看到的颜色..\n\n'
            'MATRIX翻译完毕：那些敌人说他们不怕死。那你怕不怕……'
        )
        self.info_body_label.setWordWrap(True)

        self.info_layout.addWidget(self.info_title_label)
        self.info_layout.addWidget(self.info_body_label)
        self.info_container.setLayout(self.info_layout)

        self.cfg_container = QWidget()
        self.cfg_layout = QVBoxLayout()
        self.cfg_layout.setContentsMargins(40, 0, 40, 0)
        self.cfg_layout.setSpacing(12)

        self.rotation_combo = QComboBox()
        self.rotation_desc_label = QLabel()
        self.rotation_desc_label.setWordWrap(True)
        self.rotation_combo.currentIndexChanged.connect(self._update_rotation_desc)
        self._load_rotations()

        self.monitor_combo = QComboBox()
        self.monitor_combo.addItem('未选择显示器', None)
        self.monitor_combo.currentIndexChanged.connect(self._emit_current_monitor_region)

        self.window_row_container = QWidget()
        self.window_row_layout = QHBoxLayout()
        self.window_row_layout.setContentsMargins(0, 0, 0, 0)
        self.window_row_layout.setSpacing(8)

        self.window_combo = QComboBox()
        self.window_combo.addItem('Select DejaVu', None)

        self.refresh_window_button = QPushButton('Refresh')
        self.refresh_window_button.setFixedHeight(28)
        self.refresh_window_button.setFixedWidth(92)
        self.refresh_window_button.clicked.connect(self.refresh_windows_clicked.emit)

        self.window_row_layout.addWidget(self.window_combo, 1)
        self.window_row_layout.addWidget(self.refresh_window_button, 0)
        self.window_row_container.setLayout(self.window_row_layout)

        self.open_title_editor_button = QPushButton('打开标题编辑器')
        self.open_title_editor_button.setFixedHeight(28)
        self.open_title_editor_button.clicked.connect(self.open_title_editor_clicked.emit)

        self.cfg_layout.addWidget(self.rotation_combo)
        self.cfg_layout.addWidget(self.rotation_desc_label)
        self.cfg_layout.addWidget(self.monitor_combo)
        self.cfg_layout.addWidget(self.window_row_container)
        self.cfg_layout.addWidget(self.open_title_editor_button)
        self.cfg_container.setLayout(self.cfg_layout)

        self.btn_container = QWidget()
        self.btn_layout = QVBoxLayout()
        self.btn_layout.setContentsMargins(40, 12, 40, 12)
        self.btn_layout.setSpacing(8)

        self.status_label = QLabel('🔴 未启动')
        status_font = QFont('Microsoft YaHei')
        status_font.setPixelSize(14)
        self.status_label.setFont(status_font)

        self.start_button = QPushButton('启动')
        start_button_font = QFont('Microsoft YaHei')
        start_button_font.setPixelSize(24)
        self.start_button.setFont(start_button_font)
        self.start_button.setFixedHeight(50)
        self.start_button.clicked.connect(self._handle_start_button_clicked)

        self.btn_layout.addWidget(self.status_label)
        self.btn_layout.addWidget(self.start_button)
        self.btn_container.setLayout(self.btn_layout)

        self.footer_container = QWidget()
        self.footer_layout = QVBoxLayout()
        self.footer_layout.setContentsMargins(40, 0, 40, 40)
        self.footer_layout.setSpacing(0)

        self.version_label = QLabel('12.0.5.67165')
        version_label_font = QFont('Microsoft YaHei')
        version_label_font.setPixelSize(12)
        self.version_label.setFont(version_label_font)
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.footer_layout.addWidget(self.version_label)
        self.footer_container.setLayout(self.footer_layout)

        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(0)
        self.left_layout.addWidget(
            self.logo_container,
            0,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
        )
        self.left_layout.addWidget(self.info_container)
        self.left_layout.addStretch()
        self.left_layout.addWidget(self.cfg_container)
        self.left_layout.addWidget(self.btn_container)
        self.left_layout.addWidget(self.footer_container)
        self.left_panel.setLayout(self.left_layout)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.document().setMaximumBlockCount(3000)

        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.left_panel, 1)
        self.main_layout.addWidget(self.log_output, 3)
        self.setLayout(self.main_layout)

    def _load_rotations(self) -> None:
        self.rotation_combo.blockSignals(True)
        self.rotation_combo.clear()

        for rotation_class in ALL_ROTATIONS:
            self.rotation_combo.addItem(rotation_class.name, rotation_class)

        self.rotation_combo.blockSignals(False)
        self._update_rotation_desc()

    def _update_rotation_desc(self) -> None:
        rotation_class = self.current_rotation_class()
        self.rotation_desc_label.setText(rotation_class.desc if rotation_class is not None else '')

    def _handle_start_button_clicked(self) -> None:
        if self.start_button.text() == '启动':
            self.start_clicked.emit()
            return

        self.stop_clicked.emit()

    def _emit_current_monitor_region(self) -> None:
        self.monitor_changed.emit(self.current_monitor_region())

    def set_monitors(self, monitors: list[dict[str, int]]) -> None:
        self.monitor_combo.blockSignals(True)
        self.monitor_combo.clear()

        if not monitors:
            self.monitor_combo.addItem('未选择显示器', None)
            self.monitor_combo.blockSignals(False)
            return

        for index, monitor in enumerate(monitors, start=1):
            label = f"显示器{index} ({monitor['height']}x{monitor['width']})"
            self.monitor_combo.addItem(label, monitor)

        self.monitor_combo.setCurrentIndex(0)
        self.monitor_combo.blockSignals(False)

    def set_windows(self, windows: list[WindowRecord]) -> None:
        self.window_combo.clear()

        if not windows:
            self.window_combo.addItem('未选择游戏窗口', None)
            return

        for window in windows:
            label = f"ID: {window['hwnd']} | {window['title']}"
            self.window_combo.addItem(label, window['hwnd'])

        self.window_combo.setCurrentIndex(0)

    def current_rotation_class(self) -> type[BaseRotation] | None:
        data = self.rotation_combo.currentData()
        return data if isinstance(data, type) and issubclass(data, BaseRotation) else None

    def current_monitor_region(self) -> dict[str, int] | None:
        return self.monitor_combo.currentData()

    def current_window_handle(self) -> int | None:
        data = self.window_combo.currentData()
        return data if isinstance(data, int) else None

    def set_running_state(self, is_running: bool) -> None:
        if is_running:
            self.status_label.setText('🟢 运行中')
            self.start_button.setText('停止')
            self.monitor_combo.setEnabled(False)
            self.rotation_combo.setEnabled(False)
            self.window_combo.setEnabled(False)
            self.refresh_window_button.setEnabled(False)
            return

        self.status_label.setText('🔴 未启动')
        self.start_button.setText('启动')
        self.monitor_combo.setEnabled(True)
        self.rotation_combo.setEnabled(True)
        self.window_combo.setEnabled(True)
        self.refresh_window_button.setEnabled(True)

    def append_log(self, text: str) -> None:
        self.log_output.appendPlainText(text)
