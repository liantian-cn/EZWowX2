"""
Summary:
    输出游戏面板打断黑名单的十个固定图标槽。
Description:
    无业务参数；固定共享配置键 interrupt_blacklist，每份循环只声明一次。
    输出 icon_tile，10 个 8×8 区域；list[str] 过滤全黑槽，保留顺序及重复 hash。
    Lua 按配置技能 ID 数值升序选前十项；失败不补位，黄色角标只表示类别。
    C_Spell.GetSpellTexture/RequestLoadSpellData 与 SetTexture 的核验详见模板。
    解码内部 6×6 RGB 的 xxh3 hash；全空或异常兜底 []，不执行匹配或打断。
Key Variables:
    output_count: 固定十槽，与面板保存配置数量无关。
Change Log:
    2026-09-18: Added 按已确认契约新增打断黑名单图标输出。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output, Scalar
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields


class Plugin(Condition):
    """固定十槽，空槽过滤仅发生在业务解码层。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset()).validate(args, "plugin_args")
        super().__init__(Output("icon_tile", output_count=10, value_type=str, value_shape="list"))

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> list[Scalar]:
        # 基类列表元素注解为 Scalar；本版本 Output 与实际元素始终限定为 str。
        return [value for tile in icon_tiles if (value := tile.hash) is not None]

    def fallback_value(self) -> list[Scalar]:
        """无有效图标或解码异常时不确认任何黑名单图标。"""
        return []
