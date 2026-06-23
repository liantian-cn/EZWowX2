from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .status_tab_style import (
    apply_status_tab_skin,
    mark_status_field_label,
    mark_status_note_label,
    mark_status_section_title,
    mark_status_value_input,
    prepare_status_table,
)


class TargetStatusTab(QWidget):
    """展示 target、focus、mouseover 状态和 debuff 的页签。"""

    DEBUFF_TABLE_MIN_HEIGHT = 384
    STATUS_FIELDS = [
        ("unitExists", "单位存在状态"),
        ("unitIsAlive", "单位是否存活"),
        ("unitClass", "职业"),
        ("unitRole", "职责"),
        ("unitHealthPercent", "血量百分比"),
        ("unitPowerPercent", "能量百分比"),
        ("unitIsEnemy", "敌人"),
        ("unitCanAttack", "可以被攻击"),
        ("unitIsInRangedRange", "在远程范围"),
        ("unitIsInMeleeRange", "在近战范围"),
        ("unitIsInCombat", "在战斗中"),
        ("unitIsTarget", "是当前目标"),
        ("unitCastIcon", "正在释放的技能"),
        ("unitCastDuration", "施法持续时间"),
        ("unitCastIsInterruptible", "施法是否可中断"),
        ("unitChannelIcon", "正在通道法术的技能"),
        ("unitChannelDuration", "通道持续时间"),
        ("unitChannelIsInterruptible", "通道是否可中断"),
    ]
    STATUS_FIELD_ORDER = [field_name for field_name, _label in STATUS_FIELDS]
    DEBUFF_HEADERS = ["增/减益名称", "剩余时间", "类型", "层数"]
    SECTION_TITLES = {
        "target": "Target",
        "focus": "Focus",
        "mouseover": "Mouseover",
    }

    def __init__(self) -> None:
        super().__init__()

        self.sections: dict[str, dict[str, Any]] = {}
        self.status_label = QLabel("暂无目标状态数据。")
        self.status_label.setWordWrap(True)

        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_widget.setLayout(content_layout)

        for unit_key in ("target", "focus", "mouseover"):
            self.sections[unit_key] = self._build_section(unit_key)
            content_layout.addWidget(self.sections[unit_key]["container"])

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(scroll_area)
        self.setLayout(self.main_layout)

        apply_status_tab_skin(self, self.status_label)

    def refresh_from_decode_snapshot(self, snapshot: dict[str, Any]) -> None:
        decoded_data = snapshot.get("decoded_data")
        stale = bool(snapshot.get("decode_result_is_stale"))

        if not isinstance(decoded_data, dict):
            for unit_key in self.sections:
                self._reset_section(unit_key)
            self.status_label.setText("暂无目标状态数据。")
            return

        for unit_key in self.sections:
            self._refresh_section(unit_key, decoded_data.get(unit_key))

        if stale:
            self.status_label.setText("当前显示的是旧数据，最新帧还没解码成功。")
        else:
            self.status_label.setText(self._build_presence_summary(decoded_data))

    def _build_section(self, unit_key: str) -> dict[str, Any]:
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        title_label = QLabel(self.SECTION_TITLES[unit_key])
        mark_status_section_title(title_label)

        exists_label = QLabel("当前不存在该单位。")
        exists_label.setWordWrap(True)
        mark_status_note_label(exists_label)

        field_labels: dict[str, QLabel] = {}
        value_inputs: dict[str, QLineEdit] = {}
        field_rows: dict[str, QHBoxLayout] = {}
        for field_name, label_text in self.STATUS_FIELDS:
            field_label = QLabel(label_text)
            field_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            mark_status_field_label(field_label)

            value_input = QLineEdit("None")
            value_input.setReadOnly(True)
            value_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mark_status_value_input(value_input)

            field_row = QHBoxLayout()
            field_row.addWidget(field_label, 1)
            field_row.addWidget(value_input, 1)
            field_labels[field_name] = field_label
            value_inputs[field_name] = value_input
            field_rows[field_name] = field_row
            layout.addLayout(field_row)

        debuff_title = QLabel("Debuff")
        mark_status_section_title(debuff_title)
        debuff_table = self._build_debuff_table()

        layout.insertWidget(0, title_label)
        layout.insertWidget(1, exists_label)
        layout.addWidget(debuff_title)
        layout.addWidget(debuff_table)
        layout.addStretch()

        return {
            "container": container,
            "title_label": title_label,
            "exists_label": exists_label,
            "field_labels": field_labels,
            "value_inputs": value_inputs,
            "field_rows": field_rows,
            "debuff_table": debuff_table,
        }

    def _build_debuff_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setMinimumHeight(self.DEBUFF_TABLE_MIN_HEIGHT)
        table.setColumnCount(len(self.DEBUFF_HEADERS))
        table.setHorizontalHeaderLabels(self.DEBUFF_HEADERS)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setStretchLastSection(True)
        prepare_status_table(table)
        return table

    def _refresh_section(self, unit_key: str, unit_data: Any) -> None:
        section = self.sections[unit_key]
        if not isinstance(unit_data, dict) or not unit_data.get("exists"):
            self._set_section_values(section, None)
            section["debuff_table"].setRowCount(0)
            section["exists_label"].setText("当前不存在该单位。")
            return

        status_data = unit_data.get("status") if isinstance(unit_data.get("status"), dict) else {}
        debuff_rows = self._normalize_aura_list(unit_data.get("debuff"))

        self._set_section_values(section, status_data)
        self._fill_debuff_table(section["debuff_table"], debuff_rows)
        section["exists_label"].setText(f"当前存在该单位，debuff {len(debuff_rows)} 个。")

    def _reset_section(self, unit_key: str) -> None:
        section = self.sections[unit_key]
        self._set_section_values(section, None)
        section["debuff_table"].setRowCount(0)
        section["exists_label"].setText("当前不存在该单位。")

    def _set_section_values(self, section: dict[str, Any], status_data: dict[str, Any] | None) -> None:
        for field_name in self.STATUS_FIELD_ORDER:
            value = None if status_data is None else status_data.get(field_name)
            section["value_inputs"][field_name].setText(self._format_value(value))

    def _fill_debuff_table(self, table: QTableWidget, debuff_rows: list[dict[str, Any]]) -> None:
        table.setRowCount(len(debuff_rows))
        for row_index, aura in enumerate(debuff_rows):
            table.setItem(row_index, 0, self._make_readonly_item(self._format_value(aura.get("title"))))
            table.setItem(row_index, 1, self._make_readonly_item(self._format_value(aura.get("remain"))))
            table.setItem(row_index, 2, self._make_readonly_item(self._format_value(aura.get("type"))))
            table.setItem(row_index, 3, self._make_readonly_item(self._format_value(aura.get("count"))))

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

    def _build_presence_summary(self, decoded_data: dict[str, Any]) -> str:
        parts: list[str] = []
        for unit_key, title in self.SECTION_TITLES.items():
            unit_data = decoded_data.get(unit_key)
            exists = isinstance(unit_data, dict) and bool(unit_data.get("exists"))
            parts.append(f"{title} {'存在' if exists else '不存在'}")
        return "，".join(parts) + "。"

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
