"""以冻结 TXT 核验保留的三十八份映射，并对全部四十专精做离线通用验证。"""

from __future__ import annotations

import ast
import hashlib
import json
import keyword
import re
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.contracts import Value
from phantom.core.generator import render
from phantom.core.macro_keys import MACRO_KEYS
from phantom.core.rotation import load_rotation

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/assisted_rotations_source.json"
MIGRATED_UUIDS = {"死亡骑士-鲜血": "15a37eea-e9f2-59cc-8e83-bbfd03fe866e", "圣骑士-防护": "1daf2f41-18fa-55d5-83f0-69dc71343da7"}
PLAYER_AURA_PLUGINS = {"player_has_buff@dev", "aura_player_buff_stacks@dev", "aura_player_buff_duration@dev"}

# 独立列明全部专精、索引与来源步数，不能以当前 TOML 文件反推预期集合。
EXPECTED = [
    ("deathknight/blood", "死亡骑士-鲜血", "DEATHKNIGHT", 6, 1, 16),
    ("deathknight/frost", "死亡骑士-冰霜", "DEATHKNIGHT", 6, 2, 21),
    ("deathknight/unholy", "死亡骑士-邪恶", "DEATHKNIGHT", 6, 3, 20),
    ("demonhunter/havoc", "恶魔猎手-浩劫", "DEMONHUNTER", 12, 1, 19),
    ("demonhunter/vengeance", "恶魔猎手-复仇", "DEMONHUNTER", 12, 2, 13),
    ("demonhunter/devourer", "恶魔猎手-噬灭", "DEMONHUNTER", 12, 3, 11),
    ("druid/balance", "德鲁伊-平衡", "DRUID", 11, 1, 28),
    ("druid/feral", "德鲁伊-野性", "DRUID", 11, 2, 23),
    ("druid/guardian", "德鲁伊-守护", "DRUID", 11, 3, 15),
    ("druid/restoration", "德鲁伊-恢复", "DRUID", 11, 4, 13),
    ("evoker/devastation", "唤魔师-湮灭", "EVOKER", 13, 1, 16),
    ("evoker/preservation", "唤魔师-恩护", "EVOKER", 13, 2, 4),
    ("evoker/augmentation", "唤魔师-增辉", "EVOKER", 13, 3, 14),
    ("hunter/beastmastery", "猎人-野兽控制", "HUNTER", 3, 1, 11),
    ("hunter/marksmanship", "猎人-射击", "HUNTER", 3, 2, 17),
    ("hunter/survival", "猎人-生存", "HUNTER", 3, 3, 14),
    ("mage/arcane", "法师-奥术", "MAGE", 8, 1, 19),
    ("mage/fire", "法师-火焰", "MAGE", 8, 2, 18),
    ("mage/frost", "法师-冰霜", "MAGE", 8, 3, 13),
    ("monk/brewmaster", "武僧-酒仙", "MONK", 10, 1, 12),
    ("monk/mistweaver", "武僧-织雾", "MONK", 10, 2, 12),
    ("monk/windwalker", "武僧-踏风", "MONK", 10, 3, 21),
    ("paladin/holy", "圣骑士-神圣", "PALADIN", 2, 1, 10),
    ("paladin/protection", "圣骑士-防护", "PALADIN", 2, 2, 13),
    ("paladin/retribution", "圣骑士-惩戒", "PALADIN", 2, 3, 18),
    ("priest/discipline", "牧师-戒律", "PRIEST", 5, 1, 9),
    ("priest/holy", "牧师-神圣", "PRIEST", 5, 2, 8),
    ("priest/shadow", "牧师-暗影", "PRIEST", 5, 3, 28),
    ("rogue/assassination", "潜行者-奇袭", "ROGUE", 4, 1, 35),
    ("rogue/outlaw", "潜行者-狂徒", "ROGUE", 4, 2, 25),
    ("rogue/subtlety", "潜行者-敏锐", "ROGUE", 4, 3, 21),
    ("shaman/elemental", "萨满祭司-元素", "SHAMAN", 7, 1, 29),
    ("shaman/enhancement", "萨满祭司-增强", "SHAMAN", 7, 2, 28),
    ("shaman/restoration", "萨满祭司-恢复", "SHAMAN", 7, 3, 10),
    ("warlock/affliction", "术士-痛苦", "WARLOCK", 9, 1, 21),
    ("warlock/demonology", "术士-恶魔学识", "WARLOCK", 9, 2, 13),
    ("warlock/destruction", "术士-毁灭", "WARLOCK", 9, 3, 22),
    ("warrior/arms", "战士-武器", "WARRIOR", 1, 1, 19),
    ("warrior/fury", "战士-狂怒", "WARRIOR", 1, 2, 20),
    ("warrior/protection", "战士-防护", "WARRIOR", 1, 3, 14),
]
LEGACY_EXPECTED = [row for row in EXPECTED if row[1] not in MIGRATED_UUIDS]
IGNORED = {"AURA_COUNT_NEAR_PLAYER_GREATER", "AURA_COUNT_NEAR_PLAYER_LESS", "TARGET_COUNT_NEAR_TARGET_GREATER", "TARGET_COUNT_NEAR_TARGET_LESS"}
DURATION_REFERENCE = {268877: 10, 257622: 20, 191634: 15, 264571: 12, 335467: 6, 980: 18, 433891: 20}
STACK_REFERENCE = {195181: 12, 51124: 2, 1254252: 8, 203981: 20, 1245577: 15, 359618: 2, 1242974: 25, 1221389: 20, 202090: 4, 325202: 2, 393039: 20, 344179: 10, 264571: 2, 117828: 2}
NUMERIC_OPERATORS = {"大于等于": ">=", "小于等于": "<=", "大于": ">", "小于": "<"}
AST_OPERATORS: dict[type[ast.cmpop], str] = {ast.Eq: "==", ast.Gt: ">", ast.GtE: ">=", ast.Lt: "<", ast.LtE: "<="}
type Atom = tuple[str, dict[str, object], str, bool | int | float]


@dataclass
class SourceStep:
    index: int
    name: str
    spell_id: int
    cd: float
    line: int
    rules: list[tuple[str, str, int]]


def source_steps(text: str) -> list[SourceStep]:
    """独立读取 fixture；此处不调用生成器的解析或映射实现。"""
    result: list[SourceStep] = []
    for number, line in enumerate(text.splitlines()[1:], 2):
        if ": Spell: " in line:
            index, label = line.split(": Spell: ", 1)
            name, tags = label.rsplit("[id:", 1)
            spell_id, *cooldown = tags.rstrip("]").split(",cd:")
            result.append(SourceStep(int(index), name, int(spell_id), float(cooldown[0]) if cooldown else 0, number, []))
        elif line.strip():
            text, rule_type = line.strip().split("        -- ASSISTED_COMBAT_RULE_TYPE_")
            result[-1].rules.append((rule_type, text, number))
    return result


@pytest.fixture(scope="module")
def sources() -> dict[str, str]:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert data["format"] == 1
    result: dict[str, str] = {}
    for source in data["sources"]:
        assert hashlib.sha256(source["text"].encode("utf-8")).hexdigest() == source["sha256"]
        assert source["path"] not in result
        result[source["path"]] = source["text"]
    return result


def raw_rotation(stem: str) -> dict[str, Any]:
    return tomllib.loads((ROOT / "rotations" / (stem + ".toml")).read_text(encoding="utf-8"))


def expected_atom(spec: str, step: SourceStep, kind: str, text: str) -> Atom | None:
    """直接依据冻结 TXT 文字与已批准契约，核对每个原子完整插件参数与比较。"""
    if kind in IGNORED or kind == "AUTOMATION_ONLY":
        return None
    label_id = re.search(r"\[id:(\d+)", text)
    spell_id = int(label_id[1]) if label_id else 0
    numeric = re.search(r"(大于等于|小于等于|大于|小于) (\d+(?:\.\d+)?)", text)
    op = NUMERIC_OPERATORS[numeric[1]] if numeric else "=="
    value: bool | int | float = float(numeric[2]) if numeric else True
    args: dict[str, object]
    if kind == "SPELL_LEARNED":
        return ("talent_known@dev" if "天赋" in text else "spell_known@dev", {"spell_ids": [spell_id]}, "==", True)
    if kind in {"AFFORD_COST", "COOLDOWN_ALLOW_CASTING_SUCCESS"}:
        return "spell_usable@dev", {"spell_ids": [spell_id]}, "==", True
    if kind in {"SPELL_OFF_COOLDOWN", "SPELL_ON_COOLDOWN", "COOLDOWN_REMAINING_GREATER", "COOLDOWN_REMAINING_LESS"}:
        if kind == "SPELL_OFF_COOLDOWN":
            op, value = "==", 0
        elif kind == "SPELL_ON_COOLDOWN":
            op, value = ">", 0
        else:
            value /= 1000
        return "spell_cooldown@dev", {"spell_ids": [spell_id], "ignore_gcd": True}, op, value
    if kind.startswith("TARGET_DISTANCE_"):
        return "target_in_range@dev", {"spell_id": step.spell_id}, "==", kind.endswith("LESS")
    if kind == "SPELL_IN_RANGE":
        return "spell_in_range@dev", {"spell_id": step.spell_id, "unit_token": "target"}, "==", True
    if kind.startswith("TARGET_COUNT_NEAR_PLAYER_"):
        return "player_melee_enemies_count@dev", {"spell_id": step.spell_id, "combat_only": False}, op, value
    if kind in {"AURA_ON_PLAYER", "AURA_MISSING_PLAYER", "AURA_ON_TARGET", "AURA_MISSING_TARGET"}:
        return ("player_has_buff@dev", {"buff_ids": [spell_id]}, "==", "MISSING" not in kind) if kind.endswith("PLAYER") else ("target_has_debuff@dev", {"aura_ids": [spell_id]}, "==", "MISSING" not in kind)
    if kind.startswith("AURA_DURATION_") or "_AURA_APPLICATION_" in kind:
        unit = "player_buff" if "PLAYER" in kind else "target_debuff"
        duration = kind.startswith("AURA_DURATION_")
        maximum = (DURATION_REFERENCE if duration else STACK_REFERENCE)[spell_id]
        args = {"aura_ids": [spell_id], "width": min(8, (maximum + 3) // 4)}
        if duration:
            args["duration"] = maximum
            value /= 1000
        else:
            args.update(max_value=maximum, min_value=0)
        return f"aura_{unit}_{'duration' if duration else 'stacks'}@dev", args, op, value
    if kind.startswith("SPELL_CHARGES_"):
        assert op == ">=" and value == 2
        return "spell_charges@dev", {"spell_ids": [step.spell_id], "max_charges": 2, "width": 1}, op, value
    if "HEALTH_PCT_" in kind:
        return ("player_health_pct@dev" if kind.startswith("PLAYER_") else "target_health_pct@dev", {"use_predicted": False}, op, value)
    if kind in {"HAS_PET", "HAS_NO_PET"}:
        return "player_has_pet@dev", {}, "==", kind == "HAS_PET"
    if kind == "HOSTILE_TARGET":
        return "target_is_enemy@dev", {}, "==", True
    resource = kind.rsplit("_", 1)[0]
    assert resource in {"ARCANE_CHARGES", "CHI", "COMBO_POINTS", "ENERGY", "ESSENCE", "FOCUS", "HOLY_POWER", "INSANITY", "LUNAR_POWER", "MANA", "RAGE", "RUNIC_POWER", "SOUL_SHARDS"}, kind
    args = {}
    if resource == "SOUL_SHARDS":
        args = {"fractional": spec == "warlock/destruction"}
        if args["fractional"]:
            args["width"] = 25
    elif resource not in {"ARCANE_CHARGES", "CHI", "COMBO_POINTS", "ESSENCE", "HOLY_POWER"}:
        args = {"max_power": {("deathknight/blood", "RUNIC_POWER"): 115, ("monk/windwalker", "ENERGY"): 120, ("priest/shadow", "INSANITY"): 150, ("rogue/outlaw", "ENERGY"): 200}.get((spec, resource), 100)}
    if resource in {"RAGE", "RUNIC_POWER", "SOUL_SHARDS", "LUNAR_POWER", "MANA"}:
        value /= 10
    elif resource == "INSANITY":
        value /= 100
    return f"spec_power_{resource.lower()}@dev", args, op, value


def actual_atoms(expression: str, conditions: dict[str, dict[str, Any]]) -> list[Atom]:
    result: list[Atom] = []
    # 限定每个原子都被括号包住，且顶层只有 AND，避免 OR/隐含优先级混入。
    clauses = expression.split(" and ")
    root = ast.parse(expression, mode="eval").body
    if len(clauses) > 1:
        assert isinstance(root, ast.BoolOp) and isinstance(root.op, ast.And)
        assert len(root.values) == len(clauses)
    for clause in clauses:
        assert clause.startswith("(") and clause.endswith(")")
        node = ast.parse(clause, mode="eval").body
        assert isinstance(node, ast.Compare) and isinstance(node.left, ast.Name)
        assert len(node.ops) == len(node.comparators) == 1
        value = node.comparators[0]
        assert isinstance(value, ast.Constant) and isinstance(value.value, (int, float))
        condition = conditions[node.left.id]
        result.append((condition["plugin"], condition.get("plugin_args", {}), AST_OPERATORS[type(node.ops[0])], value.value))
    return result


def test_frozen_population_totals_and_independent_uuids(sources: dict[str, str]) -> None:
    assert len(EXPECTED) == 40
    assert len({row[2] for row in EXPECTED}) == 13
    assert set(sources) == {row[0] + ".txt" for row in EXPECTED}
    assert {path.stem for path in (ROOT / "rotations").glob("*.toml") if any("\u4e00" <= char <= "\u9fff" for char in path.stem)} == {row[1] for row in EXPECTED}
    steps = [step for text in sources.values() for step in source_steps(text)]
    counts = Counter(kind for step in steps for kind, _, _ in step.rules)
    assert len(steps) == 693
    assert sum(counts.values()) == 3116
    assert sum(step.cd >= 60 for step in steps) == 80
    assert sum(not step.rules for step in steps) == 39
    assert counts["AUTOMATION_ONLY"] == 46
    assert sum(counts[kind] for kind in IGNORED if kind.startswith("AURA")) == 11
    assert sum(counts[kind] for kind in IGNORED if kind.startswith("TARGET")) == 57
    identifiers = [raw_rotation(row[1])["uuid"] for row in EXPECTED]
    assert len(set(identifiers)) == 40
    legacy_fixture = tomllib.loads((ROOT / "tests/fixtures/condition-observations.toml").read_text(encoding="utf-8"))
    assert legacy_fixture["uuid"] not in identifiers
    for (spec, stem, *_), identifier in zip(EXPECTED, identifiers, strict=True):
        assert str(UUID(identifier)) == identifier
        if stem in MIGRATED_UUIDS:
            assert identifier == MIGRATED_UUIDS[stem]
        else:
            assert identifier == str(uuid5(NAMESPACE_URL, "phantom:assisted-txt:" + spec))


@pytest.mark.parametrize("spec,stem,token,class_id,spec_index,step_count", LEGACY_EXPECTED, ids=[row[0] for row in LEGACY_EXPECTED])
def test_every_source_step_and_atom(sources: dict[str, str], spec: str, stem: str, token: str, class_id: int, spec_index: int, step_count: int) -> None:
    document = raw_rotation(stem)
    assert document["schema_version"] == 1
    assert document["profile"] == {"title": stem, "description": stem.split("-")[0] + "一键辅助", "unit_class": token, "unit_class_id": class_id, "unit_spec": spec_index}
    steps = source_steps(sources[spec + ".txt"])
    assert len(steps) == step_count
    assert len(document["rotation"]) == step_count + 1
    assert document["rotation"][-1]["condition"] == "" and document["rotation"][-1]["macro"] == "Idle"
    conditions = {condition["title"]: condition for condition in document["conditions"]}
    assert len(conditions) == len(document["conditions"])
    unique_instances: set[str] = set()
    for title, condition in conditions.items():
        assert title.isidentifier() and not keyword.iskeyword(title)
        assert "layout" not in condition
        signature = json.dumps([condition["plugin"], condition.get("plugin_args", {})], sort_keys=True)
        assert signature not in unique_instances
        unique_instances.add(signature)
        assert condition["plugin"] != "delaying@dev"
    names = list(dict.fromkeys(step.name for step in steps))
    assert document["macros"] == [{"name": name, "macro_text": "/cast " + name} for name in names]
    text = (ROOT / "rotations" / (stem + ".toml")).read_text(encoding="utf-8")
    referenced: set[str] = set()
    for step, row in zip(steps, document["rotation"][:-1], strict=True):
        assert row["macro"] == step.name
        assert row["annotate"] == f"来源步骤 {step.index}：{step.name}（ID {step.spell_id}）"
        assert f"{spec}.txt:{step.line}" in text
        expected: list[Atom] = [("enable@dev", {}, "==", True)]
        if step.cd >= 60:
            expected.append(("in_burst@dev", {}, "==", True))
        for kind, rule_text, number in step.rules:
            atom = expected_atom(spec, step, kind, rule_text)
            if atom is not None:
                expected.append(atom)
                metadata = tomllib.loads((ROOT / "phantom/conditions" / atom[0] / "plugin.toml").read_text(encoding="utf-8"))
                assert "ASSISTED_COMBAT_RULE_TYPE_" + kind in metadata["assisted_combat_rule_types"]
            else:
                assert f"来源行 {number}：{kind}" in text
        actual = actual_atoms(row["condition"], conditions)
        assert actual == expected, (spec, step.index)
        for actual_atom, expected_item in zip(actual, expected, strict=True):
            assert isinstance(actual_atom[-1], bool) == isinstance(expected_item[-1], bool)
        referenced.update(node.id for node in ast.walk(ast.parse(row["condition"], mode="eval")) if isinstance(node, ast.Name))
    blacklist = {"title": "打断黑名单图标", "plugin": "interrupt_blacklist_icons@dev"}
    assert [condition for condition in document["conditions"] if condition["plugin"] == blacklist["plugin"]] == [blacklist]
    assert document["conditions"][-1] == blacklist
    assert referenced == set(conditions) - {blacklist["title"]}


@pytest.mark.parametrize("stem", [row[1] for row in EXPECTED])
def test_copy_load_render_and_lua51_with_only_approved_defaults(tmp_path: Path, stem: str) -> None:
    original = (ROOT / "rotations" / (stem + ".toml")).read_bytes()
    copied = tmp_path / "rotation.toml"
    copied.write_bytes(original)
    rotation = load_rotation(copied)
    # 用户保留其他配置原文，副本加载只允许补入新批准的来源过滤默认值。
    expected_document = tomllib.loads(original.decode("utf-8"))
    for condition in expected_document["conditions"]:
        if condition["plugin"] in PLAYER_AURA_PLUGINS:
            condition.setdefault("plugin_args", {}).setdefault("player_only", True)
    assert tomllib.loads(copied.read_text(encoding="utf-8")) == expected_document
    if stem in MIGRATED_UUIDS:
        assert copied.read_bytes() == original
    assert (ROOT / "rotations" / (stem + ".toml")).read_bytes() == original
    assert [macro.key for macro in rotation.macros] == list(MACRO_KEYS[: len(rotation.macros)])
    blacklist_entries = [entry for entry in rotation.conditions if entry.plugin == "interrupt_blacklist_icons@dev"]
    assert len(blacklist_entries) == 1
    blacklist_entry = blacklist_entries[0]
    blacklist = blacklist_entry.instance
    assert blacklist.output.output_type == "icon_tile"
    assert blacklist.output.value_type is str and blacklist.output.value_shape == "list"
    assert blacklist.output.output_count == len(blacklist.regions) == 10
    assert blacklist.fallback_value() == []
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    compile_lua: Any = lua.eval("function(source) local fn,err=loadstring(source); assert(fn,err); return true end")
    for name, content in render(rotation, "Phantom").items():
        assert "{{" not in content
        if name.endswith(".lua"):
            assert compile_lua(content), name
    values: list[Value] = [entry.instance.fallback_value() for entry in rotation.conditions]
    enabled = next(index for index, entry in enumerate(rotation.conditions) if entry.plugin == "enable@dev")
    values[enabled] = False
    assert rotation.decide(values).rule.macro == "Idle"
    # 历史配置验证首步动作；新配置的首步为禁用暂停，动作优先级由独立基准验证。
    first = rotation.rules[0]
    assert first.expression is not None
    snapshot = {entry.title: value for entry, value in zip(rotation.conditions, values, strict=True)}
    for node in () if stem in MIGRATED_UUIDS else ast.walk(first.expression):
        if not isinstance(node, ast.Compare):
            continue
        assert isinstance(node.left, ast.Name) and isinstance(node.comparators[0], ast.Constant)
        target = node.comparators[0].value
        assert isinstance(target, (int, float))
        matching = target + 1 if isinstance(node.ops[0], ast.Gt) else target
        output_type = next(entry.instance.output.value_type for entry in rotation.conditions if entry.title == node.left.id)
        snapshot[node.left.id] = float(matching) if output_type is float else matching
    decision = rotation.decide([snapshot[entry.title] for entry in rotation.conditions])
    assert decision.rule_index == 1
    assert decision.rule.macro == first.macro
    # 观测值从空列表变为非空列表，仍须保持相同的首条动作决策。
    snapshot[blacklist_entry.title] = ["0123456789abcdef"]
    observed = rotation.decide([snapshot[entry.title] for entry in rotation.conditions])
    assert observed.rule_index == decision.rule_index and observed.macro == decision.macro
    for entry in rotation.conditions:
        if entry.instance.output.output_type == "value_bar":
            args = next(condition["plugin_args"] for condition in raw_rotation(stem)["conditions"] if condition["title"] == entry.title)
            assert entry.instance.output.widths == (args["width"],)


def test_critical_fractional_unknown_and_duplicate_name_cases(sources: dict[str, str]) -> None:
    balance = raw_rotation("德鲁伊-平衡")
    assert sum("<= 59.9)" in row["condition"] for row in balance["rotation"]) == 2
    destruction = raw_rotation("术士-毁灭")
    assert any(">= 1.5)" in row["condition"] for row in destruction["rotation"])
    assert sum(macro["name"] == "火焰之雨" for macro in destruction["macros"]) == 1
    same_name_ids = {tuple(condition["plugin_args"]["spell_ids"]) for condition in destruction["conditions"] if condition["plugin"] == "spell_cooldown@dev" and condition["title"].startswith("火焰之雨")}
    assert same_name_ids == {(5740,), (1214467,)}
    for stem, plugin, parameter, spell_id in [("死亡骑士-邪恶", "target_has_debuff@dev", "aura_ids", 194310), ("武僧-织雾", "player_has_buff@dev", "buff_ids", 389387), ("萨满祭司-增强", "player_has_buff@dev", "buff_ids", 470058)]:
        assert any(condition["plugin"] == plugin and condition.get("plugin_args", {}).get(parameter) == [spell_id] and str(spell_id) in condition["title"] for condition in raw_rotation(stem)["conditions"])
    # 同名动作冷却只看本步骤标签，无标签的超凡之盟不能借用其他职业或技能名称冷却。
    steps = source_steps(sources["druid/balance.txt"])
    unlabelled = next(index for index, step in enumerate(steps) if step.spell_id == 194223)
    assert "爆发开启" not in balance["rotation"][unlabelled]["condition"]
