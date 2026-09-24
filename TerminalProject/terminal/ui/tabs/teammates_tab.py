from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
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


class TeammatesTab(QWidget):
    """展示 party1 到 party4 的状态、buff 和 debuff。"""

    BUFF_HEADERS = ["增/减益名称", "剩余时间", "类型", "层数"]
    BUFF_TABLE_HEIGHT = 256
    DEBUFF_TABLE_HEIGHT = 128
    MAX_BUFF_ROWS = 7
    MAX_DEBUFF_ROWS = 3
    PARTY_KEYS = ("party1", "party2", "party3", "party4")
    STATUS_FIELDS = [
        ("unitExists", "存在"),
        ("unitIsAlive", "存活"),
        ("unitClass", "职业"),
        ("unitRole", "职责"),
        ("unitHealthPercent", "血量百分比"),
        ("unitPowerPercent", "能量百分比"),
        ("unitIsEnemy", "敌人"),
        ("unitCanAttack", "可以被攻击"),
        ("unitIsInRangedRange", "远程范围"),
        ("unitIsInMeleeRange", "近战范围"),
        ("unitIsInCombat", "战斗中"),
        ("unitIsTarget", "当前目标"),
        ("isPlayerCastingTarget", "是玩家当前施法目标"),
        ("unitHasBigDefense", "有大防御"),
        ("unitHasDispellableDebuff", "可驱散减益"),
        ("damage_absorbs", "伤害吸收"),
        ("heal_absorbs", "治疗吸收"),
    ]

    def __init__(self) -> None:
        super().__init__()

        self.sections: dict[str, dict[str, Any]] = {}
        self.status_label = QLabel("暂无队友数据。")
        self.status_label.setWordWrap(True)

        content_widget = QWidget()
        self.content_layout = QHBoxLayout()
        content_widget.setLayout(self.content_layout)

        for party_key in self.PARTY_KEYS:
            section = self._build_section(party_key)
            self.sections[party_key] = section
            self.content_layout.addWidget(section["container"], 1)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(content_widget, 1)
        self.setLayout(self.main_layout)

        apply_status_tab_skin(self, self.status_label)

    def refresh_from_decode_snapshot(self, snapshot: dict[str, Any]) -> None:
        decoded_data = snapshot.get("decoded_data")
        stale = bool(snapshot.get("decode_result_is_stale"))
        party_data = decoded_data.get("party") if isinstance(decoded_data, dict) else None

        if not isinstance(party_data, dict):
            for party_key in self.PARTY_KEYS:
                self._reset_section(party_key)
            self.status_label.setText("暂无队友数据。")
            return

        exists_count = 0
        for party_key in self.PARTY_KEYS:
            current_party = party_data.get(party_key)
            self._refresh_section(party_key, current_party)
            if isinstance(current_party, dict) and bool(current_party.get("exists")):
                exists_count += 1

        if stale:
            self.status_label.setText("当前显示的是旧数据，最新帧还没解码成功。")
        else:
            self.status_label.setText(f"当前队友 {exists_count} 个。")

    def _build_section(self, party_key: str) -> dict[str, Any]:
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        title_label = QLabel(party_key.replace("party", "Party"))
        mark_status_section_title(title_label)

        exists_label = QLabel("当前不存在该队友。")
        exists_label.setWordWrap(True)
        mark_status_note_label(exists_label)

        field_labels: dict[str, QLabel] = {}
        value_inputs: dict[str, QLineEdit] = {}
        for field_name, label_text in self.STATUS_FIELDS:
            field_label = QLabel(label_text)
            field_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            mark_status_field_label(field_label)

            value_input = QLineEdit("None")
            value_input.setReadOnly(True)
            value_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mark_status_value_input(value_input)

            row_layout = QHBoxLayout()
            row_layout.addWidget(field_label, 1)
            row_layout.addWidget(value_input, 1)
            layout.addLayout(row_layout)
            field_labels[field_name] = field_label
            value_inputs[field_name] = value_input

        buff_title = QLabel("Buff")
        mark_status_section_title(buff_title)
        buff_table = self._build_aura_table(self.BUFF_TABLE_HEIGHT)

        debuff_title = QLabel("Debuff")
        mark_status_section_title(debuff_title)
        debuff_table = self._build_aura_table(self.DEBUFF_TABLE_HEIGHT)

        layout.insertWidget(0, title_label)
        layout.insertWidget(1, exists_label)
        layout.addWidget(buff_title)
        layout.addWidget(buff_table)
        layout.addWidget(debuff_title)
        layout.addWidget(debuff_table)
        layout.addStretch()

        return {
            "container": container,
            "title_label": title_label,
            "exists_label": exists_label,
            "field_labels": field_labels,
            "value_inputs": value_inputs,
            "buff_table": buff_table,
            "debuff_table": debuff_table,
        }

    def _build_aura_table(self, height: int) -> QTableWidget:
        table = QTableWidget()
        table.setMinimumHeight(height)
        table.setMaximumHeight(height)
        table.setColumnCount(len(self.BUFF_HEADERS))
        table.setHorizontalHeaderLabels(self.BUFF_HEADERS)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setStretchLastSection(True)
        prepare_status_table(table)
        return table

    def _refresh_section(self, party_key: str, party_data: Any) -> None:
        section = self.sections[party_key]
        if not isinstance(party_data, dict) or not party_data.get("exists"):
            self._set_status_values(section, None)
            section["buff_table"].setRowCount(0)
            section["debuff_table"].setRowCount(0)
            section["exists_label"].setText("当前不存在该队友。")
            return

        status_data = party_data.get("status") if isinstance(party_data.get("status"), dict) else {}
        buff_rows = self._normalize_aura_list(party_data.get("buff"), self.MAX_BUFF_ROWS)
        debuff_rows = self._normalize_aura_list(party_data.get("debuff"), self.MAX_DEBUFF_ROWS)

        self._set_status_values(section, status_data)
        self._fill_aura_table(section["buff_table"], buff_rows)
        self._fill_aura_table(section["debuff_table"], debuff_rows)
        section["exists_label"].setText(f"当前存在该队友，buff {len(buff_rows)} 个，debuff {len(debuff_rows)} 个。")

    def _reset_section(self, party_key: str) -> None:
        section = self.sections[party_key]
        self._set_status_values(section, None)
        section["buff_table"].setRowCount(0)
        section["debuff_table"].setRowCount(0)
        section["exists_label"].setText("当前不存在该队友。")

    def _set_status_values(self, section: dict[str, Any], status_data: dict[str, Any] | None) -> None:
        for field_name, _label in self.STATUS_FIELDS:
            value = None if status_data is None else status_data.get(field_name)
            section["value_inputs"][field_name].setText(self._format_value(value))

    def _normalize_aura_list(self, aura_data: Any, max_rows: int) -> list[dict[str, Any]]:
        if isinstance(aura_data, list):
            rows = [value for value in aura_data if isinstance(value, dict)]
        elif isinstance(aura_data, dict):
            rows = [value for value in aura_data.values() if isinstance(value, dict)]
        else:
            return []

        rows.sort(key=self._sort_key_by_remain)
        return rows[:max_rows]

    def _sort_key_by_remain(self, aura: dict[str, Any]) -> tuple[int, float]:
        remain_value = aura.get("remain")
        if remain_value is None:
            return (1, float("inf"))

        try:
            return (0, float(remain_value))
        except (TypeError, ValueError):
            return (1, float("inf"))

    def _fill_aura_table(self, table: QTableWidget, aura_rows: list[dict[str, Any]]) -> None:
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
