from __future__ import annotations

import numpy as np
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...pixelcalc.title_manager import (
    BUFF_ON_FRIENDLY,
    CACHE_KIND_MISS,
    CACHE_KIND_PERSISTENT,
    CACHE_KIND_SIMILAR_MATCH,
    DEBUFF_ON_ENEMY,
    DEBUFF_ON_FRIENDLY,
    ENEMY_SPELL,
    NO_CATEGORY_TITLE_TYPES,
    PLAYER_SPELL,
)


CATEGORY_TABS = [
    ('友方减益', tuple(DEBUFF_ON_FRIENDLY)),
    ('友方增益', tuple(BUFF_ON_FRIENDLY)),
    ('敌方减益', tuple(DEBUFF_ON_ENEMY)),
    ('玩家技能', tuple(PLAYER_SPELL)),
    ('敌方读条', tuple(ENEMY_SPELL)),
]
NA_TITLE_TYPES = tuple(NO_CATEGORY_TITLE_TYPES)


class TitleEditorDialog(QDialog):
    def __init__(self, title_manager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title_manager = title_manager
        self.setWindowTitle('标题编辑器')
        self.resize(1100, 760)

        self.category_tables: dict[str, QTableWidget] = {}
        self._miss_input_cache: dict[str, str] = {}

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(12)

        self.tab_widget = QTabWidget()
        for tab_name, _title_types in CATEGORY_TABS:
            table = self._create_table(['图像', '标题', 'Hash', '分类', '操作'])
            self.category_tables[tab_name] = table
            self.tab_widget.addTab(self._wrap_table(table), tab_name)

        self.na_table = self._create_table(['图像', '当前标题', 'Hash', '分类', '来源', '输入标题', '操作'])
        self.tab_widget.addTab(self._wrap_table(self.na_table), 'N/A')

        self.similar_table = self._create_table(['图像', '当前标题', 'Hash', '分类', '操作'])
        self.tab_widget.addTab(self._wrap_table(self.similar_table), '相似匹配')

        self.miss_table = self._create_table(['图像', '当前标题', 'Hash', '分类', '输入标题', '操作'])
        self.tab_widget.addTab(self._wrap_table(self.miss_table), '未分类')

        self.main_layout.addWidget(self.tab_widget)
        self.setLayout(self.main_layout)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_live_tabs)
        self._start_refresh_cycle()

    def _start_refresh_cycle(self) -> None:
        self.refresh_database_tabs()
        self.refresh_live_tabs(force=True)
        if not self.refresh_timer.isActive():
            self.refresh_timer.start(1000)

    def _create_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 64)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.ResizeMode.ResizeToContents)
        return table

    def _wrap_table(self, table: QTableWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(table)
        container.setLayout(layout)
        return container

    def _build_image_label(self, png_bytes: bytes) -> QLabel:
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap()
        pixmap.loadFromData(png_bytes)

        label.setPixmap(pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        return label

    def _make_readonly_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        return item

    def refresh_database_tabs(self) -> None:
        records = self.title_manager.list_database_records()
        for tab_name, title_types in CATEGORY_TABS:
            filtered_records = [record for record in records if record['title_type'] in title_types]
            self._populate_database_table(self.category_tables[tab_name], filtered_records)

    def refresh_live_tabs(self, *, force: bool = False) -> None:
        self._remember_miss_inputs()
        if not force and self._is_editing_live_title_input():
            return
        records = self.title_manager.list_memory_records()
        na_records = [record for record in records if record['title_type'] in NA_TITLE_TYPES]
        similar_records = [
            record
            for record in records
            if record['cache_kind'] == CACHE_KIND_SIMILAR_MATCH and record['title_type'] not in NA_TITLE_TYPES
        ]
        miss_records = [
            record for record in records if record['cache_kind'] == CACHE_KIND_MISS and record['title_type'] not in NA_TITLE_TYPES
        ]
        self._populate_na_table(na_records)
        self._populate_similar_table(similar_records)
        self._populate_miss_table(miss_records)

    def _remember_miss_inputs(self) -> None:
        cached_inputs: dict[str, str] = {}
        cached_inputs.update(self._read_miss_inputs_from_table(self.miss_table, hash_column=2, input_column=4))
        cached_inputs.update(self._read_miss_inputs_from_table(self.na_table, hash_column=2, input_column=5))
        if cached_inputs:
            self._miss_input_cache.update(cached_inputs)

    def _read_miss_inputs_from_table(self, table: QTableWidget, *, hash_column: int, input_column: int) -> dict[str, str]:
        cached_inputs: dict[str, str] = {}
        for row in range(table.rowCount()):
            hash_item = table.item(row, hash_column)
            input_widget = table.cellWidget(row, input_column)
            if hash_item is None or not isinstance(input_widget, QLineEdit):
                continue
            cached_inputs[hash_item.text()] = input_widget.text()
        return cached_inputs

    def _is_editing_live_title_input(self) -> bool:
        focus_widget = self.focusWidget()
        if not isinstance(focus_widget, QLineEdit):
            return False
        return focus_widget in self.miss_table.findChildren(QLineEdit) or focus_widget in self.na_table.findChildren(QLineEdit)

    def _populate_database_table(self, table: QTableWidget, records: list[dict]) -> None:
        table.setRowCount(len(records))
        for row, record in enumerate(records):
            table.setRowHeight(row, 44)
            table.setCellWidget(row, 0, self._build_image_label(record['png_bytes']))
            table.setItem(row, 1, self._make_readonly_item(str(record['title'])))
            table.setItem(row, 2, self._make_readonly_item(str(record['hash'])))
            table.setItem(row, 3, self._make_readonly_item(str(record['title_type'])))
            table.setCellWidget(row, 4, self._build_database_actions(record))

    def _populate_na_table(self, records: list[dict]) -> None:
        self.na_table.setRowCount(len(records))
        for row, record in enumerate(records):
            record_hash = str(record['hash'])
            self.na_table.setRowHeight(row, 44)
            self.na_table.setCellWidget(row, 0, self._build_image_label(record['png_bytes']))
            self.na_table.setItem(row, 1, self._make_readonly_item(str(record['title'])))
            self.na_table.setItem(row, 2, self._make_readonly_item(record_hash))
            self.na_table.setItem(row, 3, self._make_readonly_item(str(record['title_type'])))
            self.na_table.setItem(row, 4, self._make_readonly_item(self._resolve_source_label(record)))

            if record['cache_kind'] == CACHE_KIND_MISS:
                input_widget = QLineEdit()
                input_widget.setText(self._miss_input_cache.get(record_hash, ''))
                self.na_table.setCellWidget(row, 5, input_widget)
                self.na_table.setCellWidget(row, 6, self._build_miss_actions(record, input_widget))
            elif record['cache_kind'] == CACHE_KIND_SIMILAR_MATCH:
                self.na_table.setItem(row, 5, self._make_readonly_item(''))
                self.na_table.setCellWidget(row, 6, self._build_similar_actions(record))
            else:
                self.na_table.setItem(row, 5, self._make_readonly_item(''))
                self.na_table.setCellWidget(row, 6, self._build_database_actions(record))

    def _populate_similar_table(self, records: list[dict]) -> None:
        self.similar_table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.similar_table.setRowHeight(row, 44)
            self.similar_table.setCellWidget(row, 0, self._build_image_label(record['png_bytes']))
            self.similar_table.setItem(row, 1, self._make_readonly_item(str(record['title'])))
            self.similar_table.setItem(row, 2, self._make_readonly_item(str(record['hash'])))
            self.similar_table.setItem(row, 3, self._make_readonly_item(str(record['title_type'])))
            self.similar_table.setCellWidget(row, 4, self._build_similar_actions(record))

    def _populate_miss_table(self, records: list[dict]) -> None:
        self.miss_table.setRowCount(len(records))
        for row, record in enumerate(records):
            record_hash = str(record['hash'])
            self.miss_table.setRowHeight(row, 44)
            self.miss_table.setCellWidget(row, 0, self._build_image_label(record['png_bytes']))
            self.miss_table.setItem(row, 1, self._make_readonly_item(str(record['title'])))
            self.miss_table.setItem(row, 2, self._make_readonly_item(record_hash))
            self.miss_table.setItem(row, 3, self._make_readonly_item(str(record['title_type'])))

            input_widget = QLineEdit()
            input_widget.setText(self._miss_input_cache.get(record_hash, ''))
            self.miss_table.setCellWidget(row, 4, input_widget)
            self.miss_table.setCellWidget(row, 5, self._build_miss_actions(record, input_widget))

    def _resolve_source_label(self, record: dict) -> str:
        cache_kind = str(record['cache_kind'])
        if cache_kind == CACHE_KIND_PERSISTENT:
            return '正式记录'
        if cache_kind == CACHE_KIND_SIMILAR_MATCH:
            return '相似匹配'
        return '未分类'

    def _build_database_actions(self, record: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(6)

        edit_button = QPushButton('编辑标题')
        edit_button.clicked.connect(lambda _checked=False, payload=record: self._edit_database_record(payload))
        delete_button = QPushButton('删除')
        delete_button.clicked.connect(lambda _checked=False, payload=record: self._delete_database_record(payload))

        layout.addWidget(edit_button)
        layout.addWidget(delete_button)
        container.setLayout(layout)
        return container

    def _build_similar_actions(self, record: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(6)

        save_button = QPushButton('保存为正式记录')
        save_button.clicked.connect(lambda _checked=False, payload=record: self._save_live_record(payload, payload['title']))

        layout.addWidget(save_button)
        container.setLayout(layout)
        return container

    def _build_miss_actions(self, record: dict, input_widget: QLineEdit) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(6)

        save_button = QPushButton('保存')
        save_button.clicked.connect(
            lambda _checked=False, payload=record, editor=input_widget: self._save_live_record(payload, editor.text())
        )

        layout.addWidget(save_button)
        container.setLayout(layout)
        return container

    def _edit_database_record(self, record: dict) -> None:
        new_title, ok = QInputDialog.getText(self, '编辑标题', '请输入新的标题: ', text=str(record['title']))
        new_title = new_title.strip()
        if not ok or not new_title:
            return

        self.title_manager.update_record(
            str(record['hash']),
            valid_array=np.array(record['valid_array'], dtype=np.uint8),
            title_type=str(record['title_type']),
            title=new_title,
        )
        self.refresh_database_tabs()
        self.refresh_live_tabs(force=True)

    def _delete_database_record(self, record: dict) -> None:
        reply = QMessageBox.question(self, '确认删除', '确定要删除这条标题记录吗？')
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.title_manager.delete_record(str(record['hash']))
        self.refresh_database_tabs()
        self.refresh_live_tabs(force=True)

    def _save_live_record(self, record: dict, title: str) -> None:
        normalized_title = title.strip()
        if not normalized_title:
            QMessageBox.warning(self, '标题为空', '请先输入标题。')
            return

        self.title_manager.add_record(
            valid_array=np.array(record['valid_array'], dtype=np.uint8),
            title_type=str(record['title_type']),
            title=normalized_title,
            hash=str(record['hash']),
        )
        self._miss_input_cache.pop(str(record['hash']), None)
        self.refresh_database_tabs()
        self.refresh_live_tabs(force=True)

    def showEvent(self, event: QShowEvent) -> None:
        self._start_refresh_cycle()
        super().showEvent(event)

    def closeEvent(self, event) -> None:
        self.refresh_timer.stop()
        super().closeEvent(event)
