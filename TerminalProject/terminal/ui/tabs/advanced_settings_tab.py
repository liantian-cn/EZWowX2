from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class AdvancedSettingsTab(QWidget):
    """“高级设置”页。

    这里继续保留 FPS 设置，并补上标题库相关的高级选项。
    标题管理逻辑仍然完全交给 TitleManager，本页只负责界面和调用入口。
    """

    fps_changed = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self.title_manager = None

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(12)

        self.fps_group = QGroupBox('截图频率')
        self.fps_layout = QVBoxLayout()
        self.fps_layout.setContentsMargins(12, 12, 12, 12)
        self.fps_layout.setSpacing(12)

        self.help_label = QLabel('这个值会直接影响截图 worker 的循环等待时间。')
        self.help_label.setWordWrap(True)

        self.fps_row = QHBoxLayout()
        self.fps_row.setContentsMargins(0, 0, 0, 0)
        self.fps_row.setSpacing(12)

        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setMinimum(1)
        self.fps_slider.setMaximum(40)
        self.fps_slider.setValue(20)
        self.fps_slider.valueChanged.connect(self._handle_fps_slider_changed)

        self.fps_value_label = QLabel('20 FPS')

        self.fps_row.addWidget(self.fps_slider, 1)
        self.fps_row.addWidget(self.fps_value_label)
        self.fps_layout.addWidget(self.help_label)
        self.fps_layout.addLayout(self.fps_row)
        self.fps_group.setLayout(self.fps_layout)

        self.threshold_group = QGroupBox('余弦阈值')
        self.threshold_layout = QVBoxLayout()
        self.threshold_layout.setContentsMargins(12, 12, 12, 12)
        self.threshold_layout.setSpacing(12)

        self.threshold_help_label = QLabel(
            '这个值决定相似匹配要多接近才算命中。\n'
            '数值越高越严格，误匹配更少。'
        )
        self.threshold_help_label.setWordWrap(True)

        self.threshold_row = QHBoxLayout()
        self.threshold_row.setContentsMargins(0, 0, 0, 0)
        self.threshold_row.setSpacing(12)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(980)
        self.threshold_slider.setMaximum(999)
        self.threshold_slider.setValue(999)
        self.threshold_slider.valueChanged.connect(self._handle_threshold_slider_changed)

        self.threshold_value_label = QLabel('0.999')

        self.threshold_row.addWidget(self.threshold_slider, 1)
        self.threshold_row.addWidget(self.threshold_value_label)
        self.threshold_layout.addWidget(self.threshold_help_label)
        self.threshold_layout.addLayout(self.threshold_row)
        self.threshold_group.setLayout(self.threshold_layout)

        self.import_export_group = QGroupBox('标题库导入导出')
        self.import_export_layout = QHBoxLayout()
        self.import_export_layout.setContentsMargins(12, 12, 12, 12)
        self.import_export_layout.setSpacing(12)

        self.export_button = QPushButton('导出标题库')
        self.export_button.clicked.connect(self._handle_export_clicked)
        self.import_button = QPushButton('导入标题库')
        self.import_button.clicked.connect(self._handle_import_clicked)

        self.import_export_layout.addWidget(self.export_button)
        self.import_export_layout.addWidget(self.import_button)
        self.import_export_group.setLayout(self.import_export_layout)

        self.main_layout.addWidget(self.fps_group)
        self.main_layout.addWidget(self.threshold_group)
        self.main_layout.addWidget(self.import_export_group)
        self.main_layout.addStretch()
        self.setLayout(self.main_layout)

    def set_title_manager(self, title_manager) -> None:
        self.title_manager = title_manager
        threshold = float(title_manager.similarity_threshold)
        self.threshold_slider.blockSignals(True)
        self.threshold_slider.setValue(int(round(threshold * 1000)))
        self.threshold_slider.blockSignals(False)
        self.threshold_value_label.setText(f'{threshold:.3f}')

    def _handle_fps_slider_changed(self, value: int) -> None:
        self.fps_value_label.setText(f'{value} FPS')
        self.fps_changed.emit(value)

    def _handle_threshold_slider_changed(self, value: int) -> None:
        threshold = value / 1000.0
        self.threshold_value_label.setText(f'{threshold:.3f}')
        if self.title_manager is None:
            return
        self.title_manager.similarity_threshold = threshold

    def _handle_export_clicked(self) -> None:
        if self.title_manager is None:
            return

        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            '导出标题库',
            str(Path('title-manager-export.json').resolve()),
            'JSON 文件 (*.json)',
        )
        if not path:
            return

        try:
            self.title_manager.export_json(path)
        except Exception as exc:
            QMessageBox.warning(self, '导出失败', str(exc))
            return

        QMessageBox.information(self, '导出成功', f'已导出到:\n{path}')

    def _handle_import_clicked(self) -> None:
        if self.title_manager is None:
            return

        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            '导入标题库',
            '',
            'JSON 文件 (*.json)',
        )
        if not path:
            return

        try:
            self.title_manager.import_json(path)
        except Exception as exc:
            QMessageBox.warning(self, '导入失败', str(exc))
            return

        QMessageBox.information(self, '导入成功', f'已从下列文件导入:\n{path}')
