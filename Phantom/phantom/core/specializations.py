"""
Summary:
    定义固定的十三职业、四十专精及应用配置组合键。
Description:
    按职业亮度 ID、专精顺序索引排列；配置命名与游戏内索引共享同一映射。
Key Variables:
    SPECIALIZATIONS: 稳定排序的合法组合及中英文名称。
    SPECIALIZATION_BY_KEY: phantom.toml 平铺组合键的查找表。
Change Log:
    2026-09-19: Added 多份循环共用的职业专精映射。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Specialization:
    key: str
    unit_class: str
    unit_class_id: int
    unit_spec: int
    class_name: str
    name: str


_CLASSES = (
    ("WARRIOR", "战士", (("arms", "武器"), ("fury", "狂怒"), ("protection", "防护"))),
    ("PALADIN", "圣骑士", (("holy", "神圣"), ("protection", "防护"), ("retribution", "惩戒"))),
    ("HUNTER", "猎人", (("beastmastery", "野兽控制"), ("marksmanship", "射击"), ("survival", "生存"))),
    ("ROGUE", "潜行者", (("assassination", "奇袭"), ("outlaw", "狂徒"), ("subtlety", "敏锐"))),
    ("PRIEST", "牧师", (("discipline", "戒律"), ("holy", "神圣"), ("shadow", "暗影"))),
    ("DEATHKNIGHT", "死亡骑士", (("blood", "鲜血"), ("frost", "冰霜"), ("unholy", "邪恶"))),
    ("SHAMAN", "萨满祭司", (("elemental", "元素"), ("enhancement", "增强"), ("restoration", "恢复"))),
    ("MAGE", "法师", (("arcane", "奥术"), ("fire", "火焰"), ("frost", "冰霜"))),
    ("WARLOCK", "术士", (("affliction", "痛苦"), ("demonology", "恶魔学识"), ("destruction", "毁灭"))),
    ("MONK", "武僧", (("brewmaster", "酒仙"), ("mistweaver", "织雾"), ("windwalker", "踏风"))),
    ("DRUID", "德鲁伊", (("balance", "平衡"), ("feral", "野性"), ("guardian", "守护"), ("restoration", "恢复"))),
    ("DEMONHUNTER", "恶魔猎手", (("havoc", "浩劫"), ("vengeance", "复仇"), ("devourer", "噬灭"))),
    ("EVOKER", "唤魔师", (("devastation", "湮灭"), ("preservation", "恩护"), ("augmentation", "增辉"))),
)

CLASS_IDS = {token: index for index, (token, _, _) in enumerate(_CLASSES, 1)}
SPECIALIZATIONS = tuple(Specialization(f"{token.lower()}.{slug}", token, class_id, spec_id, class_name, name) for class_id, (token, class_name, specs) in enumerate(_CLASSES, 1) for spec_id, (slug, name) in enumerate(specs, 1))
SPECIALIZATION_BY_KEY = {spec.key: spec for spec in SPECIALIZATIONS}
SPECIALIZATION_BY_PROFILE = {(spec.unit_class, spec.unit_spec): spec for spec in SPECIALIZATIONS}
