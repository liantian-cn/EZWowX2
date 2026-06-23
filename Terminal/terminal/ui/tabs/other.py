from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QScrollArea, QVBoxLayout, QWidget

from .status_tab_style import (
    apply_status_tab_skin,
    mark_status_field_label,
    mark_status_multiline_value_input,
    mark_status_section_title,
    mark_status_value_input,
)


class OtherTab(QWidget):
    """显示 extractor 导出的综合信息。"""

    SCALAR_FIELD_DEFINITIONS = [
        ("combat_time", "战斗时间"),
        ("use_mouse", "正在使用鼠标"),
        ("assisted_combat", "一键辅助推荐技能"),
        ("delay", "脚本延迟"),
        ("testCell", "测试单元"),
        ("enable", "全局开关"),
        ("spell_queue_window", "施法队列窗口"),
        ("burst_time", "爆发状态倒计时"),
        ("UTF_hash", "UTF_hash"),
        ("UTF_string", "UTF_string"),
        ("latest_succeeded_cast", "最后的施法技能"),
    ]
    BLACKLIST_FIELD_DEFINITIONS = [
        ("dispel_blacklist", "驱散黑名单"),
        ("interrupt_blacklist", "打断黑名单"),
        ("spell_stop_list", "中断法术技能"),
    ]
    FIELD_LABELS = dict(SCALAR_FIELD_DEFINITIONS + BLACKLIST_FIELD_DEFINITIONS)

    def __init__(self) -> None:
        super().__init__()

        self.field_labels: dict[str, QLabel] = {}
        self.value_inputs: dict[str, QLineEdit] = {}
        self.blacklist_inputs: dict[str, QPlainTextEdit] = {}
        self.sections: dict[str, dict[str, Any]] = {}

        self.status_label = QLabel("暂无其他数据。")
        self.status_label.setWordWrap(True)

        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_widget.setLayout(content_layout)

        self.sections["runtime"] = self._build_runtime_section()
        self.sections["blacklist"] = self._build_blacklist_section()
        content_layout.addWidget(self.sections["runtime"]["container"])
        content_layout.addWidget(self.sections["blacklist"]["container"])

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(scroll_area)
        self.setLayout(self.main_layout)

        apply_status_tab_skin(self, self.status_label)
        self._set_all_values_to_none()
        self._clear_blacklists()

    def refresh_from_decode_snapshot(self, snapshot: dict[str, Any]) -> None:
        decoded_data = snapshot.get("decoded_data")
        stale = bool(snapshot.get("decode_result_is_stale"))

        if not isinstance(decoded_data, dict):
            self._set_all_values_to_none()
            self._clear_blacklists()
            self.status_label.setText("暂无其他数据。")
            return

        misc_data = decoded_data.get("misc") if isinstance(decoded_data.get("misc"), dict) else {}
        runtime_data = {
            "combat_time": misc_data.get("combat_time"),
            "use_mouse": misc_data.get("use_mouse"),
            "assisted_combat": decoded_data.get("assisted_combat"),
            "delay": decoded_data.get("delay"),
            "testCell": decoded_data.get("testCell"),
            "enable": decoded_data.get("enable"),
            "spell_queue_window": decoded_data.get("spell_queue_window"),
            "burst_time": decoded_data.get("burst_time"),
            "UTF_hash": decoded_data.get("UTF_hash"),
            "UTF_string": decoded_data.get("UTF_string"),
            "latest_succeeded_cast": decoded_data.get("latest_succeeded_cast"),
        }
        self._fill_scalar_values(runtime_data)
        self._fill_blacklist_value("dispel_blacklist", decoded_data.get("dispel_blacklist"))
        self._fill_blacklist_value("interrupt_blacklist", decoded_data.get("interrupt_blacklist"))
        self._fill_blacklist_value("spell_stop_list", decoded_data.get("spell_stop_list"))

        if stale:
            self.status_label.setText("当前显示的是旧数据，最新帧还没解码成功。")
        else:
            self.status_label.setText("共 12 个综合字段。")

    def _build_runtime_section(self) -> dict[str, Any]:
        return self._build_scalar_section("运行信息", self.SCALAR_FIELD_DEFINITIONS)

    def _build_blacklist_section(self) -> dict[str, Any]:
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        title_label = QLabel("黑名单")
        mark_status_section_title(title_label)
        layout.addWidget(title_label)

        for field_name, label_text in self.BLACKLIST_FIELD_DEFINITIONS:
            field_label = QLabel(label_text)
            mark_status_field_label(field_label)

            value_input = QPlainTextEdit()
            value_input.setReadOnly(True)
            value_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            value_input.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
            value_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            value_input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            value_input.setMinimumHeight(86)
            mark_status_multiline_value_input(value_input)

            layout.addWidget(field_label)
            layout.addWidget(value_input)
            self.field_labels[field_name] = field_label
            self.blacklist_inputs[field_name] = value_input

        layout.addStretch()
        return {
            "container": container,
            "title_label": title_label,
            "layout": layout,
        }

    def _build_scalar_section(self, title_text: str, field_definitions: list[tuple[str, str]]) -> dict[str, Any]:
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        title_label = QLabel(title_text)
        mark_status_section_title(title_label)
        layout.addWidget(title_label)

        for field_name, label_text in field_definitions:
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
            layout.addLayout(field_row)

            self.field_labels[field_name] = field_label
            self.value_inputs[field_name] = value_input

        layout.addStretch()
        return {
            "container": container,
            "title_label": title_label,
            "layout": layout,
        }

    def _set_all_values_to_none(self) -> None:
        for field_name, _label_text in self.SCALAR_FIELD_DEFINITIONS:
            self.value_inputs[field_name].setText("None")

    def _clear_blacklists(self) -> None:
        for field_name, _label_text in self.BLACKLIST_FIELD_DEFINITIONS:
            self.blacklist_inputs[field_name].setPlainText("")

    def _fill_scalar_values(self, values: dict[str, Any]) -> None:
        for field_name, _label_text in self.SCALAR_FIELD_DEFINITIONS:
            self.value_inputs[field_name].setText(self._format_value(values.get(field_name)))

    def _fill_blacklist_value(self, field_name: str, value: Any) -> None:
        if isinstance(value, list):
            text = ";".join(str(item) for item in value)
        else:
            text = ""
        self.blacklist_inputs[field_name].setPlainText(text)

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
