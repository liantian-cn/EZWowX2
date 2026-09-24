"""
Summary:
    玩家伤害吸收量是否超过阈值。
Description:
    参数：非负整数 N，0–9007199254740990；保证 Lua 中 N 与 N+1 可区分。
    输出：cell，1 个区域，bool scalar；4×4 像素，采样内部 2×2。
    API：value = UnitGetTotalAbsorbs("player")；返回秘密数值，直接送入 StatusBar:SetValue(value)。SetMinMaxValues(N, N+1) 固定阈值显示范围。
    白色 StatusBar 覆盖黑底；整数吸收量不超过 N 为黑色，至少 N+1 为白色，Lua 不比较或计算吸收值。
    核验：2026-09-15，@wow-ui-source，12.1.0.69587，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；具体来源和限制见 template.lua。
    解码：严格全黑/全白；不可用或异常兜底 False。
Key Variables:
    threshold: 非负整数 N，0–9007199254740990；保证 Lua 中 N 与 N+1 可区分。
Change Log:
    2026-09-15: Added 按已确认的玩家条件迁移计划新增 player_damage_absorb@dev。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields, PositiveInteger


class Plugin(Condition):
    """玩家伤害吸收量是否超过阈值；参数、像素解码及异常兜底均属于本插件。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"threshold"})).validate(args, "plugin_args")
        value = args["threshold"]
        self.threshold: int = 0 if type(value) is int and value == 0 else PositiveInteger().validate(value, "threshold")
        if self.threshold > 9007199254740990:
            raise ValueError("threshold 太大，Lua 无法保证 N 与 N+1 精确区分")
        super().__init__(Output("cell", value_type=bool))

    def template_parameters(self) -> dict[str, str]:
        """序列化已验证的配置；坐标由冻结布局注入。"""
        return {"threshold": str(self.threshold)}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = cells[0]
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        """无法识别时表示未确认条件成立。"""
        return False
