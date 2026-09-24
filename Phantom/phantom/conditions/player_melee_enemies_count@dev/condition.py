"""
Summary:
    玩家近战范围敌人数量。
Description:
    参数：spell_id 为检测射程的正整数技能 ID；combat_only 为 bool，默认 false。
    输出：cell，1 个区域，int scalar；4×4 像素，采样内部 2×2。
    API：inRange = C_Spell.IsSpellInRange(spellID, unitToken)；返回 bool 或 nil，可能秘密。UnitExists(unit)、UnitCanAttack("player", unit) 返回存在及可攻击布尔值。
    技能有效时扫描 nameplate1–40 中存在、可攻击、非死亡且符合战斗选项的单位。
    秘密或 nil 距离结果不计数；只报告可观察单位。灰度 count/40，Python 四舍五入至 0–40。
    核验：2026-09-15，@wow-ui-source，12.1.0.69587，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；具体来源和限制见 template.lua。
    解码：扫描 nameplate1–40；秘密或 nil 距离结果不计数。灰度 count/40，Python 四舍五入至 0–40。；不可用或异常兜底 0。
Key Variables:
    spell_id: 用于检测近战范围的技能 ID，正整数。
Change Log:
    2026-09-19: Changed 显式声明配置默认值，构造与配置补写共用默认来源。
    2026-09-18: Changed 增加 combat_only、技能有效性及非死亡筛选。
    2026-09-15: Added 按已确认的玩家条件迁移计划新增 player_melee_enemies_count@dev。
"""

from collections.abc import Mapping
from typing import ClassVar

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Boolean, Fields, PositiveInteger


class Plugin(Condition):
    """玩家近战范围敌人数量；参数、像素解码及异常兜底均属于本插件。"""

    config_defaults: ClassVar[Mapping[str, object]] = {"combat_only": False}

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"spell_id"}), frozenset({"combat_only"})).validate(args, "plugin_args")
        self.spell_id: int = PositiveInteger().validate(args["spell_id"], "spell_id")
        self.combat_only: bool = Boolean().validate(args.get("combat_only", self.config_defaults["combat_only"]), "combat_only")
        super().__init__(Output("cell", value_type=int))

    def template_parameters(self) -> dict[str, str]:
        """序列化已验证的配置；坐标由冻结布局注入。"""
        return {"spell_id": str(self.spell_id), "combat_only": str(self.combat_only).lower()}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> int:
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        return int(cell.ratio * 40 + 0.5)

    def fallback_value(self) -> int:
        """无法识别时表示没有可报告的数量或进度。"""
        return 0
