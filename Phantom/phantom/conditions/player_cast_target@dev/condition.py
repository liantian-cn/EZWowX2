"""
Summary:
    玩家施法目标。
Description:
    参数：无参数；拒绝多余字段。
    输出：cell，1 个区域，str scalar；4×4 像素，采样内部 2×2。
    API：UNIT_SPELLCAST_SENT(unit, targetName, castGUID, spellID) 提供可能秘密的目标名；UnitName(unit) 返回可能秘密的单位名。UnitExists(unit) 检查候选单位。
    匹配 player、party1–4、raid1–40；秘密目标暂留旧值，成功/停止/失败与每秒兜底清空，长施法可能提前清空。编码 0 未知、1 玩家、2–5 队员、6–45 团员，各乘 5。
    核验：2026-09-15，@wow-ui-source，12.1.0.69587，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；具体来源和限制见 template.lua。
    解码：匹配 player、party1–4、raid1–40；秘密目标暂留旧值，成功/停止/失败与每秒兜底清空，长施法可能提前清空。编码 0 未知、1 玩家、2–5 队员、6–45 团员，各乘 5。；不可用或异常兜底 ""。
Key Variables:
    None
Change Log:
    2026-09-15: Added 按已确认的玩家条件迁移计划新增 player_cast_target@dev。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields


class Plugin(Condition):
    """玩家施法目标；参数、像素解码及异常兜底均属于本插件。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset()).validate(args, "plugin_args")
        super().__init__(Output("cell", value_type=str))

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> str:
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        brightness = int(cell.mean)
        if brightness % 5 or brightness > 225:
            raise ValueError("无效施法目标灰度")
        code = brightness // 5
        if code == 0:
            return ""
        if code == 1:
            return "player"
        if code <= 5:
            return f"party{code - 1}"
        return f"raid{code - 5}"

    def fallback_value(self) -> str:
        """无法识别时表示没有可报告的目标或图标。"""
        return ""
