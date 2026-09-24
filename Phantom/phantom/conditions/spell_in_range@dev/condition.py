"""
Summary:
    指定技能是否在目标单位射程内。
Description:
    spell_id 为正整数；unit_token 仅 target/focus/mouseover。输出一个 4×4 Cell、bool 标量。
    C_Spell.IsSpellInRange 的潜在秘密布尔值经 EvaluateColorFromBoolean 显示。
    0.1 秒轮询，无单位、无效技能、nil 或解码异常为 False；不等同实际距离。
Key Variables:
    spell_id: 检测技能 ID。
    unit_token: 经白名单验证的单位标识。
Change Log:
    2026-09-18: Added 通用单位技能射程条件。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields, PositiveInteger, String


class Plugin(Condition):
    """验证允许的单位标识，不接受任意 Lua 或单位表达式。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"spell_id", "unit_token"})).validate(args, "plugin_args")
        self.spell_id: int = PositiveInteger().validate(args["spell_id"], "spell_id")
        self.unit_token: str = String().validate(args["unit_token"], "unit_token")
        if self.unit_token not in {"target", "focus", "mouseover"}:
            raise ValueError("unit_token 仅允许 target、focus、mouseover")
        super().__init__(Output("cell", value_type=bool))

    def template_parameters(self) -> dict[str, str]:
        return {"spell_id": str(self.spell_id), "unit_token": f'"{self.unit_token}"'}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = cells[0]
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        """无法获得有效射程结果时返回否。"""
        return False
