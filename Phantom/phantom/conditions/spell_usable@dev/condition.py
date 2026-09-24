"""
Summary:
    首个匹配技能的可用性。
Description:
    参数：spell_ids 为非空正整数列表。
    输出：cell，1 个区域，bool scalar；4×4 像素。
    API：IsSpellUsable；SpellDocumentation.lua。秘密布尔经 EvaluateColorFromBoolean 渲染，不单独读取 insufficientPower。
    核验：2026-09-12，@wow-ui-source，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58，12.1.0.69587。
    解码：严格黑白布尔。
    不可用或解码异常兜底 False。
Key Variables:
    spells: 按配置优先顺序的候选技能。
Change Log:
    2026-09-14: Changed 直接读取像素属性并在插件内完成校验和业务转换，移除解码器封装。
    2026-09-14: Changed 解码接口接收同帧 PixelDecoder，保留原有业务解码。
    2026-09-13: Changed 组合校验器与解码器，保持 @1.0 配对语义。
    2026-09-12: Added spell_usable@1.0 配对编解码。
"""

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
        Fields(frozenset({"spell_ids"})).validate(args, "plugin_args")
        self.spells: tuple[int, ...] = SpellIDs().validate(args["spell_ids"], "spell_ids")
        # 输出声明只依赖已验证参数，随后由核心分配并冻结区域。
        super().__init__(Output("cell", value_type=bool))

    def template_parameters(self) -> dict[str, str]:
        """只序列化已验证的插件参数；布局坐标由核心另行注入。"""
        return {"spell_ids": ", ".join(str(spell) for spell in self.spells)}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = cells[0]
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        """本版本的不可用业务值，亦用于核心捕获的解码异常。"""
        return False
