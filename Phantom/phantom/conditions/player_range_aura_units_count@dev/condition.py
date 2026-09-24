"""
Summary:
    技能射程内带指定减益的可观察敌人数。
Description:
    spell_id/aura_id 为必填正整数；combat_only 为严格 bool，默认 False。
    输出一个 4×4 Cell，int scalar；灰度 count/40，四舍五入还原 0–40，异常兜底 0。
    仅 nameplate1..40 存在、可攻击且存活的单位，按选项过滤战斗状态。
    API、NeverSecret 初始化硬错误和秘密结果排除边界见 template.lua。
Key Variables:
    spell_id: 检测射程的技能。
    aura_id: 必须为 NeverSecret 的减益技能。
    combat_only: 是否排除脱战单位。
Change Log:
    2026-09-19: Changed 显式声明配置默认值，构造与配置补写共用默认来源。
    2026-09-18: Added 按冻结迁移约定新增条件。
"""

from collections.abc import Mapping
from typing import ClassVar

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Boolean, Fields, PositiveInteger


class Plugin(Condition):
    """仅统计可观察敌人减益，不代表全部附近单位。"""

    config_defaults: ClassVar[Mapping[str, object]] = {"combat_only": False}

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"spell_id", "aura_id"}), frozenset({"combat_only"})).validate(args, "plugin_args")
        self.spell_id: int = PositiveInteger().validate(args["spell_id"], "spell_id")
        self.aura_id: int = PositiveInteger().validate(args["aura_id"], "aura_id")
        self.combat_only: bool = Boolean().validate(args.get("combat_only", self.config_defaults["combat_only"]), "combat_only")
        super().__init__(Output("cell", value_type=int))

    def template_parameters(self) -> dict[str, str]:
        """仅序列化已校验参数，布局坐标由核心注入。"""
        return {"spell_id": str(self.spell_id), "aura_id": str(self.aura_id), "combat_only": str(self.combat_only).lower()}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> int:
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        return int(cell.ratio * 40 + 0.5)

    def fallback_value(self) -> int:
        """无有效像素时没有可报告的可观察数量。"""
        return 0
