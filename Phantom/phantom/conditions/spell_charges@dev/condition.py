"""
Summary:
    首个匹配技能的充能层数。
Description:
    参数：spell_ids 为非空正整数列表；max_charges 为正整数；可选 width 为独立正整数内容宽度。
    width 省略时取 max(1, ceil(max_charges / 2))，无上限且派生值不补写配置。
    输出：value_bar，1 个区域，int scalar；内容 4*width×4，含分隔 4*(width+1)×4 像素。
    API：GetSpellCharges；SpellDocumentation.lua、SpellSharedDocumentation.lua。秘密 currentCharges 直接传给 StatusBar。
    核验：2026-09-12，@wow-ui-source，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58，12.1.0.69587。
    解码：ratio*max_charges 四舍五入。
    不可用或解码异常兜底 0。
Key Variables:
    spells: 按配置优先顺序的候选技能。
    max_charges: Lua 数值条与 Python 解码共用的业务量程。
    width: ValueBar 内容宽度，以 Cell 为单位，与充能量程独立。
Change Log:
    2026-09-19: Changed 独立 width 参数及派生默认条宽，Lua 保持 max_charges 量程。
    2026-09-14: Changed 直接读取像素属性并在插件内完成校验和业务转换，移除解码器封装。
    2026-09-14: Changed 解码接口接收同帧 PixelDecoder，保留原有业务解码。
    2026-09-13: Changed 组合校验器与解码器，保持 @1.0 配对语义。
    2026-09-12: Added spell_charges@1.0 配对编解码。
"""

import math

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields, Items, PositiveInteger, Validator


class SpellIDs(Validator[tuple[int, ...]]):
    """候选技能按配置顺序保留；非空且每个 ID 为正整数。"""

    def validate(self, value: object, name: str) -> tuple[int, ...]:
        return tuple(Items(PositiveInteger(), nonempty=True).validate(value, name))


class Plugin(Condition):
    """校验实例参数，声明输出，再将像素解释为本条件业务值。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"spell_ids", "max_charges"}), frozenset({"width"})).validate(args, "plugin_args")
        self.spells: tuple[int, ...] = SpellIDs().validate(args["spell_ids"], "spell_ids")
        self.max_charges: int = PositiveInteger().validate(args["max_charges"], "max_charges")
        # 正整数除法实现向上取整；物理宽度不再充当充能量程。
        self.width: int = PositiveInteger().validate(args["width"], "width") if "width" in args else max(1, (self.max_charges + 1) // 2)
        # 输出声明只依赖已验证参数，随后由核心分配并冻结区域。
        super().__init__(Output("value_bar", value_type=int, widths=(self.width,)))

    def template_parameters(self) -> dict[str, str]:
        """只序列化已验证的插件参数；布局坐标由核心另行注入。"""
        return {"spell_ids": ", ".join(str(spell) for spell in self.spells), "max_charges": str(self.max_charges)}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> int:
        # 使用非负四舍五入，避免银行家舍入改变充能层数。
        return math.floor(value_bars[0].ratio * self.max_charges + 0.5)

    def fallback_value(self) -> int:
        """本版本的不可用业务值，亦用于核心捕获的解码异常。"""
        return 0
