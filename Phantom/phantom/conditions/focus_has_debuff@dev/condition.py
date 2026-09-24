"""
Summary:
    判断不可辅助焦点是否存在指定减益。
Description:
    固定 PLAYER|HARMFUL；官方 PLAYER 包含玩家宠物和载具，不增加 player_only 参数。
    aura_ids 为非空正整数列表；官方单 AuraSlot 首匹配，输出一个 bool Cell。
    UnitCanAssist(player, focus, true, true) 分类；Lua 不读取光环数据或可见性。
    纯白为真、纯黑为假；异常像素与无光环均返回 False。
Key Variables:
    aura_ids: 官方候选减益 ID。
Change Log:
    2026-09-18: Added 冻结迁移计划中的焦点减益条件。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields, Items, PositiveInteger


class Plugin(Condition):
    """由官方容器显示减益存在状态，Python 读取黑白像素。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"aura_ids"})).validate(args, "plugin_args")
        self.aura_ids: tuple[int, ...] = tuple(Items(PositiveInteger(), nonempty=True).validate(args["aura_ids"], "aura_ids"))
        super().__init__(Output("cell", value_type=bool))

    def template_parameters(self) -> dict[str, str]:
        return {"aura_ids": ", ".join(str(value) for value in self.aura_ids)}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = cells[0]
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        return False
