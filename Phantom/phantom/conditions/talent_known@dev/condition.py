"""
Summary:
    玩家是否掌握任一候选天赋技能。
Description:
    参数：非空正整数技能 ID 列表，任一已知或在法术书中即为真。
    输出：cell，1 个区域，bool scalar；4×4 像素，采样内部 2×2。
    API：known = C_SpellBook.IsSpellKnown(spellID)；inBook = C_SpellBook.IsSpellInSpellBook(spellID)；默认玩家法术书，返回布尔值，后者含覆盖技能。C_Timer.After(0, callback) 延后刷新。
    按技能 ID 判断，不解析天赋树；与 spell_known 行为完全相同，事件后延至下一帧刷新。
    核验：2026-09-15，@wow-ui-source，12.1.0.69587，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；具体来源和限制见 template.lua。
    解码：严格全黑/全白；不可用或异常兜底 False。
Key Variables:
    spell_ids: 非空正整数技能 ID 列表，任一已知或在法术书中即为真。
Change Log:
    2026-09-18: Changed 标识迁移为 talent_known@dev，保留已知技能判断逻辑。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields, Items, PositiveInteger


class Plugin(Condition):
    """玩家是否掌握任一候选天赋技能；参数、像素解码及异常兜底均属于本插件。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"spell_ids"})).validate(args, "plugin_args")
        self.spell_ids: tuple[int, ...] = tuple(Items(PositiveInteger(), nonempty=True).validate(args["spell_ids"], "spell_ids"))
        super().__init__(Output("cell", value_type=bool))

    def template_parameters(self) -> dict[str, str]:
        """序列化已验证的配置；坐标由冻结布局注入。"""
        return {"spell_ids": ", ".join(str(value) for value in self.spell_ids)}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = cells[0]
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        """无法识别时表示未确认条件成立。"""
        return False
