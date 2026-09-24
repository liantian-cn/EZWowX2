"""
Summary:
    目标是否存在。
Description:
    参数：无参数；拒绝多余字段。
    输出：cell，1 个区域，bool scalar；4×4 像素，采样内部 2×2。
    API：单位存在前置；具体 API 和安全渲染路径见 template.lua。
    布尔值直接交给 Cell:setCellBoolean，经 EvaluateColorFromBoolean 显示黑白。
    核验：2026-09-18，@wow-ui-source，12.1.0.69587，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；具体来源和限制见 template.lua。
    解码：严格全黑/全白；不可用或异常兜底 False。
Key Variables:
    None
Change Log:
    2026-09-18: Added 按已确认的目标条件迁移计划新增 target_is_exists@dev。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields


class Plugin(Condition):
    """目标是否存在；参数、像素解码及异常兜底均属于本插件。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset()).validate(args, "plugin_args")
        super().__init__(Output("cell", value_type=bool))

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = cells[0]
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        """无法识别时表示未确认条件成立。"""
        return False
