"""
Summary:
    首个匹配技能的剩余冷却秒数。
Description:
    参数：spell_ids 为非空正整数列表；ignore_gcd 为布尔。
    输出：cell，1 个区域，float scalar；4×4 像素。
    API：GetSpellCooldownDuration；SpellDocumentation.lua。秘密 duration 经颜色曲线渲染；法术书选择首个匹配。
    核验：2026-09-12，@wow-ui-source，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58，12.1.0.69587。
    解码：亮度255/155/105/55/0对应0/5/30/155/375秒，分段线性反算。
    不可用或解码异常兜底 375.0；冷却黑色兼容饱和与不可用，无额外状态位。
Key Variables:
    spells: 按配置优先顺序的候选技能。
    ignore_gcd: 是否排除公共冷却。
    COOLDOWN_POINTS: 本版本 Python 解码的固定亮度与剩余秒数节点。
Change Log:
    2026-09-14: Changed 直接读取像素属性并在插件内完成校验和业务转换，移除解码器封装。
    2026-09-14: Changed 解码接口接收同帧 PixelDecoder，保留原有业务解码。
    2026-09-13: Changed 组合校验器与解码器，保持 @1.0 配对语义。
    2026-09-12: Added spell_cooldown@1.0 配对编解码。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Boolean, Fields, Items, PositiveInteger, Validator


class SpellIDs(Validator[tuple[int, ...]]):
    """候选技能按配置顺序保留；非空且每个 ID 为正整数。"""

    def validate(self, value: object, name: str) -> tuple[int, ...]:
        return tuple(Items(PositiveInteger(), nonempty=True).validate(value, name))


# 本版本的亮度到剩余秒数配对节点；黑色兼有饱和与不可用含义。
COOLDOWN_POINTS: tuple[tuple[float, float], ...] = ((0.0, 375.0), (55.0, 155.0), (105.0, 30.0), (155.0, 5.0), (255.0, 0.0))


class Plugin(Condition):
    """校验实例参数，声明输出，再将像素解释为本条件业务值。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"spell_ids", "ignore_gcd"})).validate(args, "plugin_args")
        self.spells: tuple[int, ...] = SpellIDs().validate(args["spell_ids"], "spell_ids")
        self.ignore_gcd: bool = Boolean().validate(args["ignore_gcd"], "ignore_gcd")
        # 输出声明只依赖已验证参数，随后由核心分配并冻结区域。
        super().__init__(Output("cell", value_type=float))

    def template_parameters(self) -> dict[str, str]:
        """只序列化已验证的插件参数；布局坐标由核心另行注入。"""
        return {"spell_ids": ", ".join(str(spell) for spell in self.spells), "ignore_gcd": str(self.ignore_gcd).lower()}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> float:
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        brightness = cell.mean
        # 按本版本的亮度节点反算剩余秒数，保留黑色的饱和含义。
        for (low, end), (high, start) in zip(COOLDOWN_POINTS, COOLDOWN_POINTS[1:]):
            if brightness <= high:
                return start + (high - brightness) * (end - start) / (high - low)
        raise ValueError("无法定位冷却插值区间")

    def fallback_value(self) -> float:
        """本版本的不可用业务值，亦用于核心捕获的解码异常。"""
        return 375.0
