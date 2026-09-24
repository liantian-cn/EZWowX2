"""
Summary:
    指定物品有库存且冷却已结束。
Description:
    item_id 为正整数；输出一个 Cell、bool 标量，严格黑白解码，异常 False。
    C_Item.GetItemCount 不计各类银行和使用次数；GetItemCooldown 必须返回有效且启用的冷却。
    不检查 usable 或资源，仅使用静态公开 ID 的已核验普通返回路径；普通数据无效或 API 异常显示 False。
    核验：2026-09-19，官方 12.1.0.69587，revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；见模板。
Key Variables:
    item_id: 本实例唯一物品 ID。
Change Log:
    2026-09-19: Added 通用单物品库存与冷却就绪条件。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields, PositiveInteger


class Plugin(Condition):
    """只声明指定物品的库存与冷却就绪，不增加可用性条件。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"item_id"})).validate(args, "plugin_args")
        self.item_id: int = PositiveInteger().validate(args["item_id"], "item_id")
        super().__init__(Output("cell", value_type=bool))

    def template_parameters(self) -> dict[str, str]:
        return {"item_id": str(self.item_id)}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = cells[0]
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        """不可用或像素异常时，表示未确认物品冷却就绪。"""
        return False
