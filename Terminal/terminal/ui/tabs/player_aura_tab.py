from __future__ import annotations

from typing import Any, TypedDict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .status_tab_style import apply_status_tab_skin, mark_status_section_title, prepare_status_table


class AuraSectionWidgets(TypedDict):
    container: QWidget
    title_label: QLabel
    table: QTableWidget
    layout: QVBoxLayout


class PlayerAuraTab(QWidget):
    """展示玩家 buff 和 debuff 的页签。"""

    HEADERS = ["增/减益名称", "剩余时间", "类型", "层数"]

    def __init__(self) -> None:
        super().__init__()

        self.sections: dict[str, AuraSectionWidgets] = {}
        self.status_label = QLabel("暂无玩家增益/减益数据。")
        self.status_label.setWordWrap(True)

        self.buff_table = self._build_table()
        self.debuff_table = self._build_table()

        content_widget = QWidget()
        table_layout = QHBoxLayout()
        content_widget.setLayout(table_layout)

        self.sections["buff"] = self._build_section("Buff", self.buff_table)
        self.sections["debuff"] = self._build_section("Debuff", self.debuff_table)
        table_layout.addWidget(self.sections["buff"]["container"], 1)
        table_layout.addWidget(self.sections["debuff"]["container"], 1)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(content_widget, 1)
        self.setLayout(self.main_layout)

        apply_status_tab_skin(self, self.status_label)

    def refresh_from_decode_snapshot(self, snapshot: dict[str, Any]) -> None:
        decoded_data = snapshot.get("decoded_data")
        stale = bool(snapshot.get("decode_result_is_stale"))
        player_data = decoded_data.get("player") if isinstance(decoded_data, dict) else None

        if not isinstance(player_data, dict):
            self._clear_tables()
            self.status_label.setText("暂无玩家增益/减益数据。")
            return

        buff_rows = self._normalize_aura_list(player_data.get("buff"))
        debuff_rows = self._normalize_aura_list(player_data.get("debuff"))

        self._fill_table(self.buff_table, buff_rows)
        self._fill_table(self.debuff_table, debuff_rows)

        if not buff_rows and not debuff_rows:
            self.status_label.setText("暂无玩家增益/减益数据。")
            return

        if stale:
            self.status_label.setText("当前显示的是旧数据，最新帧还没解码成功。")
        else:
            self.status_label.setText(f"buff {len(buff_rows)} 个，debuff {len(debuff_rows)} 个。")

    def _build_section(self, title_text: str, table: QTableWidget) -> AuraSectionWidgets:
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        title_label = QLabel(title_text)
        mark_status_section_title(title_label)
        layout.addWidget(title_label)
        layout.addWidget(table, 1)
        layout.addStretch()

        return {
            "container": container,
            "title_label": title_label,
            "table": table,
            "layout": layout,
        }

    def _build_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(self.HEADERS))
        table.setHorizontalHeaderLabels(self.HEADERS)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setStretchLastSection(True)
        prepare_status_table(table)
        return table

    def _clear_tables(self) -> None:
        self.buff_table.setRowCount(0)
        self.debuff_table.setRowCount(0)

    def _normalize_aura_list(self, aura_data: Any) -> list[dict[str, Any]]:
        if isinstance(aura_data, list):
            rows = [value for value in aura_data if isinstance(value, dict)]
        elif isinstance(aura_data, dict):
            rows = [value for value in aura_data.values() if isinstance(value, dict)]
        else:
            return []

        rows.sort(key=self._sort_key_by_remain)
        return rows

    def _sort_key_by_remain(self, aura: dict[str, Any]) -> tuple[int, float]:
        remain_value = aura.get("remain")
        if remain_value is None:
            return (1, float("inf"))

        try:
            return (0, float(remain_value))
        except (TypeError, ValueError):
            return (1, float("inf"))

    def _fill_table(self, table: QTableWidget, aura_rows: list[dict[str, Any]]) -> None:
        table.setRowCount(len(aura_rows))
        for row_index, aura in enumerate(aura_rows):
            table.setItem(row_index, 0, self._make_readonly_item(self._format_value(aura.get("title"))))
            table.setItem(row_index, 1, self._make_readonly_item(self._format_value(aura.get("remain"))))
            table.setItem(row_index, 2, self._make_readonly_item(self._format_value(aura.get("type"))))
            table.setItem(row_index, 3, self._make_readonly_item(self._format_value(aura.get("count"))))

    def _make_readonly_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        return item

    def _format_value(self, value: Any) -> str:
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)
