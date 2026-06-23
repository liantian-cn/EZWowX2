from __future__ import annotations

from typing import Any

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


class PluginSpecTab(QWidget):
    """展示 setting 和 spec 原始 cell 列表。"""

    HEADERS = ["序号", "mean", "黑色", "颜色值", "decimal", "percent", "白色"]
    SECTION_TITLES = {
        "setting": "插件设置",
        "spec": "专精属性",
    }

    def __init__(self) -> None:
        super().__init__()

        self.sections: dict[str, dict[str, Any]] = {}
        self.status_label = QLabel("暂无插件/专精数据。")
        self.status_label.setWordWrap(True)

        self.setting_table = self._build_table()
        self.spec_table = self._build_table()

        content_widget = QWidget()
        self.content_layout = QHBoxLayout()
        content_widget.setLayout(self.content_layout)

        self.sections["setting"] = self._build_section("setting", self.setting_table)
        self.sections["spec"] = self._build_section("spec", self.spec_table)
        self.content_layout.addWidget(self.sections["setting"]["container"], 1)
        self.content_layout.addWidget(self.sections["spec"]["container"], 1)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(content_widget, 1)
        self.setLayout(self.main_layout)

        apply_status_tab_skin(self, self.status_label)

    def refresh_from_decode_snapshot(self, snapshot: dict[str, Any]) -> None:
        decoded_data = snapshot.get("decoded_data")
        stale = bool(snapshot.get("decode_result_is_stale"))

        if not isinstance(decoded_data, dict):
            self._clear_tables()
            self.status_label.setText("暂无插件/专精数据。")
            return

        setting_rows = self._normalize_rows(decoded_data.get("setting"))
        spec_rows = self._normalize_rows(decoded_data.get("spec"))

        self._fill_table(self.setting_table, setting_rows)
        self._fill_table(self.spec_table, spec_rows)

        if not setting_rows and not spec_rows:
            self.status_label.setText("暂无插件/专精数据。")
            return

        if stale:
            self.status_label.setText("当前显示的是旧数据，最新帧还没解码成功。")
        else:
            self.status_label.setText(f"插件设置 {len(setting_rows)} 行，专精属性 {len(spec_rows)} 行。")

    def _build_section(self, section_key: str, table: QTableWidget) -> dict[str, Any]:
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        title_label = QLabel(self.SECTION_TITLES[section_key])
        mark_status_section_title(title_label)
        layout.addWidget(title_label)
        layout.addWidget(table, 1)

        return {
            "container": container,
            "title_label": title_label,
            "table": table,
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
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        prepare_status_table(table)
        return table

    def _clear_tables(self) -> None:
        self.setting_table.setRowCount(0)
        self.spec_table.setRowCount(0)

    def _normalize_rows(self, raw_data: Any) -> list[tuple[str, dict[str, Any] | None]]:
        if not isinstance(raw_data, dict):
            return []
        return [(str(key), value if isinstance(value, dict) else None) for key, value in raw_data.items()]

    def _fill_table(self, table: QTableWidget, rows: list[tuple[str, dict[str, Any] | None]]) -> None:
        table.setRowCount(len(rows))
        for row_index, (row_key, value) in enumerate(rows):
            table.setItem(row_index, 0, self._make_readonly_item(row_key))
            table.setItem(row_index, 1, self._make_readonly_item(self._format_float_field(value, "mean")))
            table.setItem(row_index, 2, self._make_readonly_item(self._format_value(None if value is None else value.get("is_black"))))
            table.setItem(row_index, 3, self._make_readonly_item(self._format_value(None if value is None else value.get("color_string"))))
            table.setItem(row_index, 4, self._make_readonly_item(self._format_float_field(value, "decimal")))
            table.setItem(row_index, 5, self._make_readonly_item(self._format_float_field(value, "percent")))
            table.setItem(row_index, 6, self._make_readonly_item(self._format_value(None if value is None else value.get("is_white"))))

    def _format_float_field(self, value: dict[str, Any] | None, field_name: str) -> str:
        if value is None:
            return "None"

        field_value = value.get(field_name)
        if field_value is None:
            return "None"

        try:
            return f"{float(field_value):.2f}"
        except (TypeError, ValueError):
            return str(field_value)

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
