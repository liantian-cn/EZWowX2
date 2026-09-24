"""
Summary:
    死亡骑士可用符文数量。
Description:
    参数：无参数。
    输出：cell，1 个区域，int scalar；4×4 像素。
    API：GetRuneCooldown；PlayerScriptDocumentation.lua。runeReady 无秘密返回标记；忽略秘密事件参数。
    核验：2026-09-12，@wow-ui-source，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58，12.1.0.69587。
    解码：mean 四舍五入为0–6整数。
    不可用或解码异常兜底 0。
Key Variables:
    None
Change Log:
    2026-09-14: Changed 直接读取像素属性并在插件内完成校验和业务转换，移除解码器封装。
    2026-09-14: Changed 解码接口接收同帧 PixelDecoder，保留原有业务解码。
    2026-09-13: Changed 组合校验器与解码器，保持 @1.0 配对语义。
    2026-09-18: Changed 标识迁移为 spec_power_rune@dev，保留符文逻辑。
"""

import math

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields


class Plugin(Condition):
    """校验实例参数，声明输出，再将像素解释为本条件业务值。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset(set())).validate(args, "plugin_args")
        # 输出声明只依赖已验证参数，随后由核心分配并冻结区域。
        super().__init__(Output("cell", value_type=int))

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> int:
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        # 符文按非负四舍五入读取，编码值仍须符合业务范围。
        count = math.floor(cell.mean + 0.5)
        if not 0 <= count <= 6:
            raise ValueError("符文数量超出 0–6")
        return count

    def fallback_value(self) -> int:
        """本版本的不可用业务值，亦用于核心捕获的解码异常。"""
        return 0
