"""
Summary:
    指定技能是否能覆盖焦点距离。
Description:
    spell_id 为正整数，输出一个 4×4 Cell 的 bool 标量，不代表实际距离。
    C_Spell.IsSpellInRange 的潜在秘密布尔值经 EvaluateColorFromBoolean 显示。
    无单位、无效技能、nil 或解码异常为 False；仅严格黑白可解码。
Key Variables:
    spell_id: 用于检测射程的技能 ID。
Change Log:
    2026-09-18: Added 焦点技能射程条件。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields, PositiveInteger


class Plugin(Condition):
    """校验技能并读取严格黑白射程结果。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"spell_id"})).validate(args, "plugin_args")
        self.spell_id: int = PositiveInteger().validate(args["spell_id"], "spell_id")
        super().__init__(Output("cell", value_type=bool))

    def template_parameters(self) -> dict[str, str]:
        return {"spell_id": str(self.spell_id)}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = cells[0]
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        """无法获得有效射程结果时返回否。"""
        return False
