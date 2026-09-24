"""
Summary:
    玩家神圣能量整数值。
Description:
    无参数；输出一个 4×4 Cell、int scalar。UnitPower 固定 HolyPower、非原始单位。
    API 来源：UnitDocumentation.lua；遵循 todo_list2.md 已确认的目标版本约定。
    Lua 先检查 secret，再验证 0..255 整数，非法返回直接 error；普通值除以 255 渲染。
    Python 校验纯灰色后读取整数亮度；像素解码失败兜底 0，不代替 Lua 硬错误。
Key Variables:
    None。
Change Log:
    2026-09-18: Added 固定神圣能量类型的资源条件。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields


class Plugin(Condition):
    """以整数灰度读取次要资源。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset()).validate(args, "plugin_args")
        super().__init__(Output("cell", value_type=int))

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> int:
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        return int(cell.mean)

    def fallback_value(self) -> int:
        """像素不可用时按没有可用次要资源处理。"""
        return 0
