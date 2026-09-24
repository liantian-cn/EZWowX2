"""
Summary:
    玩家漩涡值的灰度估计。
Description:
    max_power 必填有限正数；输出一个 4×4 Cell、float scalar。
    UnitPowerPercent 固定 Maelstrom，经颜色曲线直接渲染秘密值，Python 按 ratio*max_power 还原。
    API 来源：UnitDocumentation.lua；遵循 todo_list2.md 已确认的目标版本约定。
    灰度量化步长为 max_power/255；解码异常兜底 0.0。
Key Variables:
    max_power: 配置的资源换算上限，不自动读取实际上限。
Change Log:
    2026-09-18: Added 固定漩涡值类型的资源条件。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields, PositiveNumber


class Plugin(Condition):
    """将固定资源的灰度比例换算为配置量程内的估计值。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"max_power"})).validate(args, "plugin_args")
        self.max_power: float = PositiveNumber().validate(args["max_power"], "max_power")
        super().__init__(Output("cell", value_type=float))

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> float:
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        return cell.ratio * self.max_power

    def fallback_value(self) -> float:
        """像素不可用时按没有可用资源估计处理。"""
        return 0.0
