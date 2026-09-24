from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class SpellTab(QWidget):
    """展示 frame_decode_worker 解码后 spell 的页签。"""

    HEADERS = ['技能名称', '冷却时间', '充能技能', '充能层数', '高亮状态', '可用', '学会']

    def __init__(self) -> None:
        super().__init__()

        self.status_label = QLabel('暂无技能数据。')
        self.status_label.setWordWrap(True)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(self.table)
        self.setLayout(self.main_layout)

    def refresh_from_decode_snapshot(self, snapshot: dict[str, Any]) -> None:
        decoded_data = snapshot.get('decoded_data')
        spell_list = decoded_data.get('spell', []) if isinstance(decoded_data, dict) else []
        stale = bool(snapshot.get('decode_result_is_stale'))

        if not spell_list:
            self.table.setRowCount(0)
            self.status_label.setText('暂无技能数据。')
            return

        self.table.setRowCount(len(spell_list))
        for row, spell in enumerate(spell_list):
            self.table.setItem(row, 0, self._make_readonly_item(str(spell.get('title', ''))))
            self.table.setItem(row, 1, self._make_readonly_item(self._format_cooldown(spell.get('cooldown', 0))))
            self.table.setItem(row, 2, self._make_readonly_item(self._format_bool(spell.get('is_charge', False))))
            self.table.setItem(row, 3, self._make_readonly_item(str(spell.get('charges', 0))))
            self.table.setItem(row, 4, self._make_readonly_item(self._format_bool(spell.get('highlight', False))))
            self.table.setItem(row, 5, self._make_readonly_item(self._format_bool(spell.get('is_usable', False))))
            self.table.setItem(row, 6, self._make_readonly_item(self._format_bool(spell.get('is_known', False))))

        if stale:
            self.status_label.setText('当前显示的是旧数据，最新帧还没解码成功。')
        else:
            self.status_label.setText(f'共 {len(spell_list)} 个技能。')

    def _make_readonly_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        return item

    def _format_bool(self, value: Any) -> str:
        return '是' if bool(value) else '否'

    def _format_cooldown(self, value: Any) -> str:
        cooldown = float(value)
        if cooldown.is_integer():
            return str(int(cooldown))
        return f'{cooldown:.1f}'
