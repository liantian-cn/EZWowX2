from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QScrollArea, QVBoxLayout, QWidget

from .status_tab_style import (
    apply_status_tab_skin,
    mark_status_field_label,
    mark_status_section_title,
    mark_status_value_input,
)


class PlayerStatusTab(QWidget):
    """展示玩家状态字段的页签。"""

    FIELD_DEFINITIONS = [
        ("unitExists", "存在"),
        ("unitIsAlive", "单位存在状态"),
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
        ("isPlayerCastingTarget", "是玩家当前施法目标"),
        ("unitHasBigDefense", "有大防御值"),
        ("unitHasDispellableDebuff", "有可驱散的减益效果"),
        ("unitCastIcon", "正在释放的技能"),
        ("unitCastDuration", "施法持续时间"),
        ("unitChannelIcon", "正在通道法术的技能"),
        ("unitChannelDuration", "通道持续时间"),
        ("unitIsEmpowering", "是否正在蓄力"),
        ("unitEmpoweringStage", "蓄力阶段"),
        ("unitIsMoving", "是否移动中"),
        ("unitIsMounted", "是否骑乘中"),
        ("unitEnemyCount", "近战敌人数量"),
        ("unitIsSpellTargeting", "正在选择目标"),
        ("unitIsChatInputActive", "正在聊天输入"),
        ("unitIsInGroupOrRaid", "在队伍/团队中"),
        ("unitTrinket1CooldownUsable", "饰品 1可用"),
        ("unitTrinket2CooldownUsable", "饰品 2可用"),
        ("unitHealthstoneCooldownUsable", "生命石可用"),
        ("unitHealingPotionCooldownUsable", "治疗药水可用"),
        ("damage_absorbs", "伤害吸收"),
        ("heal_absorbs", "治疗吸收"),
    ]
    FIELD_LABELS = dict(FIELD_DEFINITIONS)
    SECTION_DEFINITIONS = [
        (
            "basic",
            "基础信息",
            [
                "unitExists",
                "unitIsAlive",
                "unitClass",
                "unitRole",
                "unitHealthPercent",
                "unitPowerPercent",
                "damage_absorbs",
                "heal_absorbs",
            ],
        ),
        (
            "combat",
            "战斗与距离",
            [
                "unitIsEnemy",
                "unitCanAttack",
                "unitIsInRangedRange",
                "unitIsInMeleeRange",
                "unitIsInCombat",
                "unitIsTarget",
                "isPlayerCastingTarget",
                "unitHasBigDefense",
                "unitHasDispellableDebuff",
                "unitIsMoving",
                "unitIsMounted",
                "unitEnemyCount",
                "unitIsInGroupOrRaid",
            ],
        ),
        (
            "casting",
            "施法与其他",
            [
                "unitCastIcon",
                "unitCastDuration",
                "unitChannelIcon",
                "unitChannelDuration",
                "unitIsEmpowering",
                "unitEmpoweringStage",
                "unitIsSpellTargeting",
                "unitIsChatInputActive",
                "unitTrinket1CooldownUsable",
                "unitTrinket2CooldownUsable",
                "unitHealthstoneCooldownUsable",
                "unitHealingPotionCooldownUsable",
            ],
        ),
    ]
    FIELD_ORDER = [field_name for field_name, _label in FIELD_DEFINITIONS]

    def __init__(self) -> None:
        super().__init__()

        self.field_labels: dict[str, QLabel] = {}
        self.value_inputs: dict[str, QLineEdit] = {}
        self.field_rows: dict[str, QHBoxLayout] = {}
        self.field_section_keys: dict[str, str] = {}
        self.sections: dict[str, dict[str, Any]] = {}

        self.status_label = QLabel("暂无玩家状态数据。")
        self.status_label.setWordWrap(True)

        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_widget.setLayout(content_layout)

        for section_key, title_text, field_names in self.SECTION_DEFINITIONS:
            self.sections[section_key] = self._build_section(section_key, title_text, field_names)
            content_layout.addWidget(self.sections[section_key]["container"])

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
        player_data = decoded_data.get("player") if isinstance(decoded_data, dict) else None
        status_data = player_data.get("status") if isinstance(player_data, dict) else None

        if not isinstance(status_data, dict):
            self._set_all_values_to_none()
            self.status_label.setText("暂无玩家状态数据。")
            return

        self._fill_values(status_data)
        if stale:
            self.status_label.setText("当前显示的是旧数据，最新帧还没解码成功。")
        else:
            self.status_label.setText(f"共 {len(self.FIELD_ORDER)} 个状态字段。")

    def _build_section(self, section_key: str, title_text: str, field_names: list[str]) -> dict[str, Any]:
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        title_label = QLabel(title_text)
        mark_status_section_title(title_label)
        layout.addWidget(title_label)

        for field_name in field_names:
            field_label = QLabel(self.FIELD_LABELS[field_name])
            field_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            mark_status_field_label(field_label)

            value_input = QLineEdit("None")
            value_input.setReadOnly(True)
            value_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mark_status_value_input(value_input)

            field_row = QHBoxLayout()
            field_row.addWidget(field_label, 1)
            field_row.addWidget(value_input, 1)

            self.field_labels[field_name] = field_label
            self.value_inputs[field_name] = value_input
            self.field_rows[field_name] = field_row
            self.field_section_keys[field_name] = section_key
            layout.addLayout(field_row)

        layout.addStretch()
        return {
            "container": container,
            "title_label": title_label,
            "layout": layout,
        }

    def _set_all_values_to_none(self) -> None:
        for field_name in self.FIELD_ORDER:
            self.value_inputs[field_name].setText("None")

    def _fill_values(self, status_data: dict[str, Any]) -> None:
        for field_name in self.FIELD_ORDER:
            self.value_inputs[field_name].setText(self._format_value(status_data.get(field_name)))

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
