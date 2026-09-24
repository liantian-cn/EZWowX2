"""
Summary:
    玩家施法或通道进度。
Description:
    参数：无参数；拒绝多余字段。
    输出：cell，1 个区域，float scalar；4×4 像素，采样内部 2×2。
    API：UnitCastingInfo("player") 第 11 项 delayTimeMs、UnitChannelInfo("player") 第 9 项 isEmpowered 是 NeverSecret 状态哨兵；UnitCastingDuration/UnitChannelDuration("player") 返回 duration 或无值。color = duration:EvaluateElapsedPercent(curve) 接受颜色曲线并返回可能秘密的颜色。
    CreateColorCurve 黑色 0、白色 1；直接渲染颜色。Python 返回 0–100，空闲为 0.0。
    核验：2026-09-15，@wow-ui-source，12.1.0.69587，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；具体来源和限制见 template.lua。
    解码：CreateColorCurve 黑色 0、白色 1；直接渲染颜色。Python 返回 0–100，空闲为 0.0。；不可用或异常兜底 0.0。
Key Variables:
    None
Change Log:
    2026-09-15: Added 按已确认的玩家条件迁移计划新增 player_cast_progress@dev。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields


class Plugin(Condition):
    """玩家施法或通道进度；参数、像素解码及异常兜底均属于本插件。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset()).validate(args, "plugin_args")
        super().__init__(Output("cell", value_type=float))

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> float:
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        return cell.percent

    def fallback_value(self) -> float:
        """无法识别时表示没有可报告的数量或进度。"""
        return 0.0
