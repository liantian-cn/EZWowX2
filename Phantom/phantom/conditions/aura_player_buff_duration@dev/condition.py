"""
Summary:
    估计玩家首个匹配增益的剩余秒数。
Description:
    aura_ids 为非空正整数列表，duration 为有限正数秒；可选 width 为独立正整数内容宽度。
    player_only 默认 True，使用 HELPFUL|PLAYER；False 时使用 HELPFUL。
    width 省略时取 min(8, max(1, ceil(duration / 4)))，派生值不补写配置；显式宽度无此上限。
    输出为单个 ValueBar、float scalar；内容 4*width×4，含分隔 4*(width+1)×4 像素。
    官方 AuraSlot.SetDurationBar 使用 Immediate / RemainingTime 显示原生时长比例。
    Python 返回 ratio * 配置 duration 的 float；实际光环时长不同会有误差，名义步长为 duration/(4*width) 秒。
    永久光环交官方处理；无光环或解码异常返回 0.0，不读取秘密光环数据。
Key Variables:
    duration: 配置时长，非官方固定绝对量程。
    width: ValueBar 内容宽度，以 Cell 为单位，与解码量程独立。
Change Log:
    2026-09-19: Changed 时长允许有限正小数；增加默认开启的 player_only 来源过滤。
    2026-09-19: Changed 独立 width 参数及有上限的派生默认条宽，保持时长换算不变。
    2026-09-18: Added 冻结迁移计划中的玩家增益时长。
"""

from collections.abc import Mapping
from math import ceil
from typing import ClassVar

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Boolean, Fields, Items, PositiveInteger, PositiveNumber


class Plugin(Condition):
    """将官方时长条的像素比例换算为配置秒数估计。"""

    config_defaults: ClassVar[Mapping[str, object]] = {"player_only": True}

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"aura_ids", "duration"}), frozenset({"width", "player_only"})).validate(args, "plugin_args")
        self.aura_ids: tuple[int, ...] = tuple(Items(PositiveInteger(), nonempty=True).validate(args["aura_ids"], "aura_ids"))
        self.duration: float = PositiveNumber().validate(args["duration"], "duration")
        self.player_only: bool = Boolean().validate(args.get("player_only", self.config_defaults["player_only"]), "player_only")
        # 只有省略 width 时才按时长派生条宽，小数时长同样向上取整。
        self.width: int = PositiveInteger().validate(args["width"], "width") if "width" in args else min(8, max(1, ceil(self.duration / 4)))
        super().__init__(Output("value_bar", value_type=float, widths=(self.width,)))

    def template_parameters(self) -> dict[str, str]:
        return {"aura_ids": ", ".join(str(value) for value in self.aura_ids), "aura_filter": '"HELPFUL|PLAYER"' if self.player_only else '"HELPFUL"'}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> float:
        return value_bars[0].ratio * self.duration

    def fallback_value(self) -> float:
        return 0.0
