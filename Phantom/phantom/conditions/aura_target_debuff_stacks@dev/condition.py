"""
Summary:
    估计不可辅助目标首个匹配减益的层数。
Description:
    固定 PLAYER|HARMFUL；官方 PLAYER 包含玩家宠物和载具，不增加 player_only 参数。
    aura_ids 为非空正整数列表；max_value 与 width 为正整数，width 默认 2。
    min_value 默认 0 且仅允许整数 0；SetApplicationBar 仅指定 maxApplications。
    官方容器管理秘密层数，Python 返回 float ratio * max_value，步长 max_value / (4 * width)。
    无光环或解码异常返回 0.0；ValueBarBackplate 仅提供背板，不创建默认填充。
Key Variables:
    max_value: 层数显示上限。
Change Log:
    2026-09-19: Changed 显式声明配置默认值，构造与配置补写共用默认来源。
    2026-09-18: Added 冻结迁移计划中的目标减益层数。
"""

from collections.abc import Mapping
from typing import ClassVar

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields, Items, PositiveInteger


class Plugin(Condition):
    """将官方层数条像素比例换算为浮点层数估计。"""

    config_defaults: ClassVar[Mapping[str, object]] = {"min_value": 0, "width": 2}

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"aura_ids", "max_value"}), frozenset({"min_value", "width"})).validate(args, "plugin_args")
        self.aura_ids: tuple[int, ...] = tuple(Items(PositiveInteger(), nonempty=True).validate(args["aura_ids"], "aura_ids"))
        self.max_value: int = PositiveInteger().validate(args["max_value"], "max_value")
        self.width: int = PositiveInteger().validate(args.get("width", self.config_defaults["width"]), "width")
        minimum = args.get("min_value", self.config_defaults["min_value"])
        if type(minimum) is not int or minimum != 0:
            raise ValueError("min_value 仅允许整数 0")
        self.min_value: int = minimum
        super().__init__(Output("value_bar", value_type=float, widths=(self.width,)))

    def template_parameters(self) -> dict[str, str]:
        return {"aura_ids": ", ".join(str(value) for value in self.aura_ids), "max_value": str(self.max_value)}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> float:
        return value_bars[0].ratio * self.max_value

    def fallback_value(self) -> float:
        return 0.0
