"""
Summary:
    玩家饰品是否准备就绪。
Description:
    参数：饰品位置 ID，只接受 13 或 14。
    输出：cell，1 个区域，bool scalar；4×4 像素，采样内部 2×2。
    API：itemID = GetInventoryItemID("player", slotID)；返回物品 ID 或 nil。start, duration, enabled = C_Item.GetItemCooldown(itemID)；usable, noMana = C_Item.IsUsableItem(itemID)。
    所选位置有物品、enabled 为真、duration 为零、usable 为真且 noMana 为假；不另查数量。
    核验：2026-09-15，@wow-ui-source，12.1.0.69587，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；具体来源和限制见 template.lua。
    解码：严格全黑/全白；不可用或异常兜底 False。
Key Variables:
    slot_id: 饰品位置 ID，只接受 13 或 14。
Change Log:
    2026-09-15: Added 按已确认的玩家条件迁移计划新增 player_trinket_ready@dev。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields, PositiveInteger


class Plugin(Condition):
    """玩家饰品是否准备就绪；参数、像素解码及异常兜底均属于本插件。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"slot_id"})).validate(args, "plugin_args")
        self.slot_id: int = PositiveInteger().validate(args["slot_id"], "slot_id")
        if self.slot_id not in (13, 14):
            raise ValueError("slot_id 只接受 13 或 14")
        super().__init__(Output("cell", value_type=bool))

    def template_parameters(self) -> dict[str, str]:
        """序列化已验证的配置；坐标由冻结布局注入。"""
        return {"slot_id": str(self.slot_id)}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = cells[0]
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        """无法识别时表示未确认条件成立。"""
        return False
