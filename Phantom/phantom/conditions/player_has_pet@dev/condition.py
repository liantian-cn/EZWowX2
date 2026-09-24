"""
Summary:
    玩家是否有存活宠物。
Description:
    无参数；输出一个 4×4 Cell，bool scalar，严格黑白解码，异常兜底 False。
    UnitExists(pet) 且非 UnitIsDeadOrGhost(pet)；API 来源及事件刷新见 template.lua。
    仅报告 pet 单位，不统计守护者或其他召唤物。
Key Variables:
    None
Change Log:
    2026-09-18: Added 按冻结迁移约定新增条件。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields


class Plugin(Condition):
    """存活宠物存在性的严格布尔输出。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset()).validate(args, "plugin_args")
        super().__init__(Output("cell", value_type=bool))

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = cells[0]
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        """无有效像素时未确认存在存活宠物。"""
        return False
