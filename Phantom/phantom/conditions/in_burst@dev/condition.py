"""
Summary:
    从当前帧的通用 Cell 读取Lua 爆发状态。
Description:
    参数：无参数；不包含 Lua，不分配新像素区域。
    输出：none，0 个区域，bool scalar；读取已有 Cell(4, 1) 的 4×4 像素。
    来源：phantom/lua/general/04_in_burst.lua，现有 Lua 框架持续维护该状态。
    不调用 WoW API、不处理 Secret Value，只读取框架已经渲染的像素。
    解码：中心 2×2 严格全白为 True、全黑为 False。
    非黑白值或额外读取异常兜底 False，rotation 继续按配置求值，不隐式暂停。
Key Variables:
    STATE_X: 保留的第一行状态 Cell 横坐标。
Change Log:
    2026-09-14: Changed 直接读取像素属性并在插件内完成校验和业务转换，移除解码器封装。
    2026-09-14: Added 按确认计划将爆发开启读取改为可命名的 Python 条件插件。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields

STATE_X: int = 4


class Plugin(Condition):
    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset()).validate(args, "plugin_args")
        super().__init__(Output("none", output_count=0, value_type=bool))

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = decoder.getCell(STATE_X, 1)
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        """按已确认业务语义兜底，并允许 rotation 继续求值。"""
        return False
