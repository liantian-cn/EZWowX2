"""
Summary:
    焦点生命百分比。
Description:
    use_predicted 为 bool，默认 true。输出一个 4×4 Cell、float 标量。
    UnitHealthPercent 将潜在秘密比例经颜色曲线直接显示，Python 解为 0–100。
    API 契约沿用已确认目标版本 UnitDocumentation.lua；无单位或解码异常为 0.0。
Key Variables:
    use_predicted: 是否使用预测生命值。
Change Log:
    2026-09-19: Changed 显式声明配置默认值，构造与配置补写共用默认来源。
    2026-09-18: Added 焦点生命百分比条件。
"""

from collections.abc import Mapping
from typing import ClassVar

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Boolean, Fields


class Plugin(Condition):
    """校验预测选项并解释灰度生命百分比。"""

    config_defaults: ClassVar[Mapping[str, object]] = {"use_predicted": True}

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset(), frozenset({"use_predicted"})).validate(args, "plugin_args")
        self.use_predicted: bool = Boolean().validate(args.get("use_predicted", self.config_defaults["use_predicted"]), "use_predicted")
        super().__init__(Output("cell", value_type=float))

    def template_parameters(self) -> dict[str, str]:
        return {"use_predicted": str(self.use_predicted).lower()}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> float:
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        return cell.percent

    def fallback_value(self) -> float:
        """无单位或解码异常表示零生命百分比。"""
        return 0.0
