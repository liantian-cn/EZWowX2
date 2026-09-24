"""
Summary:
    玩家灵魂碎片数量，可选择包含十分之一碎片的模式。
Description:
    fractional 为严格 bool，缺省 false：一个 4×4 Cell、int scalar，保留原整数契约。
    fractional=true：一个 ValueBar、float scalar；width 为可选正整数，仅此模式接受，派生缺省为 25。
    内容为 4*width×4 像素，含分隔占位 4*(width+1)×4；实际片段精度受宽度和渲染影响。
    UnitPower 固定 SoulShards；false 路径先检查 secret，再验证 0..255 整数，非法返回直接 error。
    true 路径将原始片段直接交给固定 0..50 的 StatusBar，不在 Lua 检查或计算秘密值。
    Python 将 ValueBar.ratio 恢复至最近整数片段格点，再除以 10，返回 0.0..5.0。
    API 来源：UnitDocumentation.lua、SimpleStatusBarAPIDocumentation.lua、Mainline/ShardBar.lua；
    2026-09-19 核验本地 12.1.0.69587，revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
    目标 12.1.0.69814 未游戏实测。像素异常兜底分别为 0 或 0.0，不保证 <= 条件不命中。
Key Variables:
    fractional: 构造时选择输出与解码契约，运行时不自动切换。
Change Log:
    2026-09-19: Added 可选小数碎片模式，直接显示原始片段并在 Python 恢复十分之一碎片。
    2026-09-18: Added 固定整灵魂碎片的资源条件。
"""

import math
from collections.abc import Mapping
from typing import ClassVar

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Boolean, Fields, PositiveInteger


class Plugin(Condition):
    """按构造参数冻结整碎片 Cell 或片段 ValueBar。"""

    config_defaults: ClassVar[Mapping[str, object]] = {"fractional": False}

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset(), frozenset({"fractional", "width"})).validate(args, "plugin_args")
        self.fractional: bool = Boolean().validate(args.get("fractional", self.config_defaults["fractional"]), "fractional")
        if self.fractional:
            # 宽度仅在小数模式派生，不能静态补写到旧 Cell 配置。
            width = PositiveInteger().validate(args.get("width", 25), "width")
            super().__init__(Output("value_bar", value_type=float, widths=(width,)))
        else:
            if "width" in args:
                raise ValueError("width 仅适用于 fractional=true")
            super().__init__(Output("cell", value_type=int))

    def template_parameters(self) -> dict[str, str]:
        # 两种区域分别具有 y 或 width，以同一占位符读取核心冻结布局，不另建坐标来源。
        region = self.regions[0]
        dimension = region.width if self.fractional else region.y
        assert dimension is not None
        return {"fractional": str(self.fractional).lower(), "output_dimension": str(dimension)}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> int | float:
        if self.fractional:
            # 先恢复整数片段，避免浮点比例误差让 1.5、4.0 等阈值落在错误一侧。
            return math.floor(value_bars[0].ratio * 50 + 0.5) / 10
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        return int(cell.mean)

    def fallback_value(self) -> int | float:
        """像素不可用时返回对应类型的零；零仍可能命中 <= 上限条件。"""
        return 0.0 if self.fractional else 0
