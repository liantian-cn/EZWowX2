"""依据独立冻结 JSON 摘录核验两坦克顺序、条件与宏；仅加载副本并在内存验证 Lua。"""

from __future__ import annotations

import ast
import json
import re
import tomllib
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.contracts import Value
from phantom.core.generator import render
from phantom.core.macro_keys import MACRO_KEYS
from phantom.core.pixels import PixelDecoder, ValueBar
from phantom.core.rotation import Rotation, load_rotation

ROOT = Path(__file__).resolve().parents[1]
SOURCE: dict[str, Any] = json.loads((ROOT / "tests/fixtures/tank_migration_source.json").read_text(encoding="utf-8"))
SPECS = ("blood", "protection")
PLAIN = {
    "enable",
    "delaying",
    "player_in_combat",
    "player_cast_progress",
    "player_is_empowering",
    "player_is_moving",
    "in_burst",
    "target_is_exists",
    "target_is_alive",
    "target_can_attack",
    "target_can_assist",
    "target_cast_interruptible",
    "focus_is_exists",
    "focus_is_alive",
    "focus_can_attack",
    "focus_can_assist",
    "focus_cast_interruptible",
    "spec_power_rune",
    "spec_power_holy_power",
    "interrupt_blacklist_icons",
}


def valid_unit(unit: str) -> str:
    return f"({unit}_is_exists and {unit}_is_alive and {unit}_can_attack and not {unit}_can_assist)"


def bindings(document: dict[str, Any], spec: str) -> dict[str, str]:
    """从插件身份提取语义名，同时以源定义和冻结量程核验全部参数。"""
    definitions = SOURCE[spec]["definitions"]
    auras = {entry["SpellIds"][-1]: entry for entry in definitions["player_auras"]}
    spells = {entry["SpellId"]: entry for entry in definitions["spells"]}
    durations = {entry["id"]: entry for entry in definitions["duration_references"]}
    result: dict[str, str] = {}
    for entry in document["conditions"]:
        plugin = entry["plugin"].removesuffix("@dev")
        assert entry["plugin"] == plugin + "@dev"
        args = entry.get("plugin_args", {})
        expected: dict[str, Any] = {}
        symbol = plugin
        if plugin in PLAIN:
            pass
        elif plugin in {"player_health_pct", "target_health_pct"}:
            expected = {"use_predicted": True}
        elif plugin in {"spec_power_runic_power", "spec_power_mana"}:
            expected = {"max_power": 120 if spec == "blood" else 100}
        elif plugin == "spell_cooldown":
            spell_id = args["spell_ids"][0]
            assert spell_id in spells and "MaxCharge" not in spells[spell_id]
            expected = {"spell_ids": [spell_id], "ignore_gcd": True}
            symbol = f"cooldown_{spell_id}"
        elif plugin == "spell_charges":
            spell_id = args["spell_ids"][0]
            expected = {"spell_ids": [spell_id], "max_charges": spells[spell_id]["MaxCharge"], "width": 1}
            symbol = f"charges_{spell_id}"
        elif plugin == "player_has_buff":
            aura_id = args["buff_ids"][-1]
            expected = {"buff_ids": auras[aura_id]["SpellIds"], "player_only": True}
            symbol = f"buff_{aura_id}"
        elif plugin == "aura_player_buff_stacks":
            aura_id = args["aura_ids"][0]
            expected = {"aura_ids": [aura_id], "max_value": auras[aura_id]["MaxApps"], "min_value": 0, "width": definitions["stack_widths"][str(aura_id)], "player_only": True}
            symbol = f"stacks_{aura_id}"
        elif plugin == "aura_player_buff_duration":
            aura_id = args["aura_ids"][0]
            expected = {"aura_ids": [aura_id], "duration": durations[aura_id]["duration"], "width": durations[aura_id]["width"], "player_only": True}
            symbol = f"duration_{aura_id}"
        elif plugin == "target_has_debuff":
            assert spec == "blood"
            expected = {"aura_ids": [55078]}
            symbol = "debuff_55078"
        elif plugin == "target_in_range":
            spell_id = args["spell_id"]
            assert spell_id in ({49998} if spec == "blood" else {31935, 96231})
            expected = {"spell_id": spell_id}
            symbol = f"range_{spell_id}"
        elif plugin == "item_cooldown_ready":
            assert spec == "blood" and definitions["items"] == [{"Name": "圣光潜力", "ItemId": 241308}]
            expected = {"item_id": 241308}
            symbol = "item_241308"
        else:
            pytest.fail(f"未授权的额外插件：{plugin}")
        assert args == expected, entry
        assert symbol not in result.values(), entry
        result[entry["title"]] = symbol
    return result


def source_expression(rule: dict[str, Any], spec: str) -> str:
    """仅作为本次冻结规则的测试判据，不输出配置或作为通用转换器。"""
    expression: str = rule["Condition"]
    children = rule.get("SubConditions", [])
    if children:
        expression = f"({expression}) && ({' || '.join(children)})"
    substitutions = {
        "目标类型 > 100 || 目标类型 == 0": "not " + valid_unit("target"),
        "目标类型 == 0 || 目标类型 > 100": "not " + valid_unit("target"),
        "焦点类型 > 0 && 焦点类型 < 100": valid_unit("focus"),
        "战斗时间 == 0": "not player_in_combat",
        "引导 != 0": "player_cast_progress > 0",
        "施法(正计时) > 0": "player_cast_progress > 0",
        "蓄力 != 0": "player_is_empowering",
        "延迟 != 0": "delaying",
        "焦点施法可打断 == 1": "focus_cast_interruptible",
        "焦点引导可打断 == 1": "focus_cast_interruptible",
        "目标施法可打断 == 1": "target_cast_interruptible",
        "目标引导可打断 == 1": "target_cast_interruptible",
        "爆发开关 == 1": "in_burst",
        "爆发药水开关 == 1": "in_burst",
        "移动 == false": "not player_is_moving",
        "圣光潜力 == 0": "item_241308",
        "目标距离 <= 25": "range_31935",
        "目标距离 <= 8": "range_49998",
        "目标距离 <= 5": "range_96231",
        "目标生命值": "target_health_pct",
        "生命值": "player_health_pct",
        "符文能量": "spec_power_runic_power",
        "符文": "spec_power_rune",
        "神圣能量": "spec_power_holy_power",
        "法力值": "spec_power_mana",
        "auras.target.harmful.55078.value == 0": "not debuff_55078",
    }
    for old, new in substitutions.items():
        expression = expression.replace(old, new)
    for reference in SOURCE[spec]["definitions"]["duration_references"]:
        aura_id = reference["id"]
        expression = expression.replace(f"auras.player.{aura_id}.value", f"duration_{aura_id}")
    expression = re.sub(r"auras\.player\.(\d+)\.value (?:> 0|>= 1)", r"buff_\1", expression)
    expression = re.sub(r"auras\.player\.(\d+)\.value == 0", r"not buff_\1", expression)
    expression = re.sub(r"auras\.player\.(\d+)\.apps", r"stacks_\1", expression)
    expression = re.sub(r"spells\.(\d+)\.cooldown", r"cooldown_\1", expression)
    expression = re.sub(r"spells\.(\d+)\.count", r"charges_\1", expression)
    return expression.replace("&&", "and").replace("||", "or")


def semantic_tree(expression: str, names: dict[str, str] | None = None) -> tuple[Any, ...]:
    """忽略同运算符的括号层数，保留 AND/OR 结合及叶子相对顺序。"""

    def visit(node: ast.AST) -> tuple[Any, ...]:
        if isinstance(node, ast.Name):
            return ("name", names[node.id] if names is not None else node.id)
        if isinstance(node, ast.Constant):
            return ("literal", node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return ("not", visit(node.operand))
        if isinstance(node, ast.Compare):
            assert len(node.ops) == len(node.comparators) == 1
            return (type(node.ops[0]).__name__, visit(node.left), visit(node.comparators[0]))
        assert isinstance(node, ast.BoolOp)
        operator = type(node.op).__name__
        items: list[tuple[Any, ...]] = []
        for value in node.values:
            item = visit(value)
            items.extend(item[1:] if item[0] == operator else [item])
        # 同一合一打断插件代表源施法 OR 引导，唯此处可去掉完全相同的 OR 分支。
        if operator == "Or" and len(set(items)) == 1:
            return items[0]
        return (operator, *items)

    return visit(ast.parse(expression, mode="eval").body)


def source_macro(rule: dict[str, Any]) -> str | None:
    spell: str = rule["Spell"]
    if spell == "暂停":
        return None
    if spell == "圣言祭礼":
        return "/cast 圣言祭礼\n/use 16"
    if spell == "圣光潜力":
        return "/cast item:241308\n/cast item:241309"
    unit = {31: "player", 32: "target", 33: "focus"}.get(rule.get("Unit", 0))
    return "/cast " + (f"[@{unit}] " if unit else "") + spell


def document_for(spec: str) -> dict[str, Any]:
    return tomllib.loads((ROOT / "rotations" / (SOURCE[spec]["title"] + ".toml")).read_text(encoding="utf-8"))


@pytest.mark.parametrize("spec", SPECS)
def test_frozen_rules_parameters_order_and_exact_macros(spec: str) -> None:
    source = SOURCE[spec]
    document = document_for(spec)
    names = bindings(document, spec)
    assert document["uuid"] == source["uuid"]
    assert document["profile"] == {"title": source["title"], "description": "作者：liantian-cn", "unit_class": source["class"], "unit_class_id": source["class_id"], "unit_spec": source["spec"]}
    assert len(source["rules"]) == (30 if spec == "blood" else 26)
    assert [rule["index"] for rule in source["rules"]] == list(range(1, len(source["rules"]) + 1))
    groups = source["source_groups"]
    retained = [index for group in groups for index in group]
    assert retained == [index for index in range(1, len(source["rules"]) + 1) if not (spec == "protection" and index == 3)]
    assert len(document["rotation"]) == (29 if spec == "blood" else 26)
    first, *middle, last = document["rotation"]
    assert semantic_tree(first["condition"], names) == semantic_tree("not enable")
    assert first["macro"] == last["macro"] == "Idle"
    assert last["condition"] == ""
    macros = {macro["name"]: macro["macro_text"] for macro in document["macros"]}
    expected_macros: list[str] = []
    for group, actual in zip(groups, middle, strict=True):
        rules = [source["rules"][index - 1] for index in group]
        expected = semantic_tree(source_expression(rules[0], spec))
        for rule in rules:
            assert semantic_tree(source_expression(rule, spec)) == expected, group
            assert source_macro(rule) == source_macro(rules[0])
        assert semantic_tree(actual["condition"], names) == expected, group
        macro = source_macro(rules[0])
        if macro is None:
            assert actual["macro"] == "Idle"
        else:
            assert macros[actual["macro"]] == macro, group
            if macro not in expected_macros:
                expected_macros.append(macro)
    assert list(macros.values()) == expected_macros
    observed = document["conditions"][-1]
    assert observed == {"title": "打断黑名单图标", "plugin": "interrupt_blacklist_icons@dev"}
    referenced = {node.id for row in document["rotation"] if row["condition"] for node in ast.walk(ast.parse(row["condition"], mode="eval")) if isinstance(node, ast.Name)}
    assert referenced == set(names) - {observed["title"]}
    text = (ROOT / "rotations" / (source["title"] + ".toml")).read_text(encoding="utf-8")
    assert text.startswith("schema_version = 1")
    assert "一键辅助" not in text and "迁移" not in text
    if spec == "protection":
        assert middle[21] == middle[23]


@pytest.fixture(params=SPECS)
def loaded(request: pytest.FixtureRequest, tmp_path: Path) -> tuple[str, Rotation, dict[str, str]]:
    spec = str(request.param)
    original = (ROOT / "rotations" / (SOURCE[spec]["title"] + ".toml")).read_bytes()
    copied = tmp_path / "rotation.toml"
    copied.write_bytes(original)
    rotation = load_rotation(copied)
    assert copied.read_bytes() == original
    return spec, rotation, bindings(document_for(spec), spec)


def test_copy_render_lua51_and_keys(loaded: tuple[str, Rotation, dict[str, str]]) -> None:
    spec, rotation, _ = loaded
    # 使用加载器认可的空条件显式兜底，不能再追加不可达的隐含 Idle。
    configured_count = len(SOURCE[spec]["source_groups"]) + 2
    assert len(rotation.rules) == configured_count
    assert rotation.rules[-1].condition == ""
    assert rotation.rules[-1].expression is None and rotation.rules[-1].macro == "Idle"
    assert [macro.key for macro in rotation.macros] == list(MACRO_KEYS[: len(rotation.macros)])
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    compile_lua: Any = lua.eval("function(source) local fn,err=loadstring(source); assert(fn,err); return true end")
    for path, content in render(rotation, "Phantom").items():
        if path.endswith(".lua"):
            assert compile_lua(content), path


def neutral_values(rotation: Rotation, names: dict[str, str]) -> dict[str, Value]:
    """明确的全未命中快照，不根据当前规则反推满足值。"""
    values: dict[str, Value] = {names[entry.title]: entry.instance.fallback_value() for entry in rotation.conditions}
    values.update(enable=True, player_in_combat=True, target_is_exists=True, target_is_alive=True, target_can_attack=True)
    for name in values:
        if name.startswith("cooldown_"):
            values[name] = 60.0
        elif name.endswith("health_pct"):
            values[name] = 100.0
    if "duration_195181" in values:
        values.update(duration_195181=30.0, stacks_195181=12.0)
    else:
        values.update(buff_433550=True, duration_132403=13.5, duration_188370=4.0)
    return values


def assert_decision(loaded: tuple[str, Rotation, dict[str, str]], updates: dict[str, Value], source_index: int | None, *, disabled: bool = False) -> None:
    spec, rotation, names = loaded
    values = neutral_values(rotation, names)
    assert set(updates) <= set(values)
    values.update(updates)
    # 按真实插件声明转为 float；不能以 bool 冒充资源值。
    snapshot: list[Value] = []
    for entry in rotation.conditions:
        value = values[names[entry.title]]
        if entry.instance.output.value_type is float and isinstance(value, (float, int)) and not isinstance(value, bool):
            value = float(value)
        elif entry.instance.output.value_type is int and isinstance(value, float):
            assert value.is_integer(), (entry.title, value)
            value = int(value)
        snapshot.append(value)
    decision = rotation.decide(snapshot)
    groups = SOURCE[spec]["source_groups"]
    expected_index = 1 if disabled else len(groups) + 2 if source_index is None else next(index + 2 for index, group in enumerate(groups) if source_index in group)
    assert decision.rule_index == expected_index, (spec, updates, decision.rule)
    # 观测黑名单从空变为非空，不能改变本帧决策。
    snapshot[-1] = ["0123456789abcdef"]
    assert rotation.decide(snapshot).rule_index == expected_index


def test_control_priority_and_invalid_units(loaded: tuple[str, Rotation, dict[str, str]]) -> None:
    spec, _, _ = loaded
    assert_decision(loaded, {}, None)
    assert_decision(loaded, {"enable": False, "player_health_pct": 1.0}, None, disabled=True)
    combat, casting, empower, target = (1, 2, 4, 5) if spec == "blood" else (4, 5, 7, 8)
    assert_decision(loaded, {"player_in_combat": False}, combat)
    assert_decision(loaded, {"player_cast_progress": 0.1, "player_is_empowering": True}, casting)
    assert_decision(loaded, {"player_is_empowering": True}, empower)
    for name, value in [("target_is_exists", False), ("target_is_alive", False), ("target_can_attack", False), ("target_can_assist", True)]:
        assert_decision(loaded, {name: value, "player_health_pct": 1.0}, target)
    if spec == "protection":
        assert_decision(loaded, {"buff_433550": False, "player_in_combat": False, "target_is_exists": False, "player_cast_progress": 50.0}, 2)
        assert_decision(loaded, {"delaying": True, "buff_433550": False}, 1)
        assert_decision(loaded, {"buff_433550": False, "enable": False}, None, disabled=True)


def test_healing_interrupt_order_and_focus_validity(loaded: tuple[str, Rotation, dict[str, str]]) -> None:
    spec, _, _ = loaded
    interrupts: dict[str, Value] = {"focus_is_exists": True, "focus_is_alive": True, "focus_can_attack": True, "focus_cast_interruptible": True, "target_cast_interruptible": True}
    if spec == "blood":
        interrupts["cooldown_47528"] = 0.0
        healing: dict[str, Value] = {"player_health_pct": 55.0, "spec_power_runic_power": 42.0}
        heal_index, focus_index, target_index = 6, 7, 9
    else:
        interrupts.update(cooldown_31935=0.0, cooldown_96231=0.0, range_31935=True, range_96231=True)
        healing = {"player_health_pct": 75.0, "stacks_327510": 2.0, "spec_power_mana": 20.0}
        heal_index, focus_index, target_index = 10, 13, 14
    assert_decision(loaded, interrupts | healing, heal_index)
    assert_decision(loaded, interrupts, focus_index)
    for name, value in [("focus_is_exists", False), ("focus_is_alive", False), ("focus_can_attack", False), ("focus_can_assist", True), ("focus_cast_interruptible", False)]:
        assert_decision(loaded, interrupts | {name: value}, target_index)
    if spec == "protection":
        assert_decision(loaded, interrupts | {"focus_cast_interruptible": False, "cooldown_31935": 1.0}, 15)
        assert_decision(loaded, interrupts | {"spec_power_holy_power": 3, "duration_132403": 4.0} | healing, 9)


@pytest.mark.parametrize("duration,stacks", [(5.0, 12.0), (30.0, 5.0), (5.0, 5.0)])
@pytest.mark.parametrize("loaded", ["blood"], indirect=True)
def test_blood_or_branches_keep_subcondition(loaded: tuple[str, Rotation, dict[str, str]], duration: float, stacks: float) -> None:
    weak: dict[str, Value] = {"duration_195181": duration, "stacks_195181": stacks}
    assert_decision(loaded, weak | {"cooldown_439843": 0.0, "spec_power_rune": 3, "cooldown_195292": 0.0}, 11)
    assert_decision(loaded, weak | {"spec_power_rune": 3, "cooldown_195292": 0.0}, 13)
    assert_decision(loaded, weak | {"cooldown_195292": 0.0}, 14)
    assert_decision(loaded, weak, None)


@pytest.mark.parametrize("loaded", ["blood"], indirect=True)
def test_blood_resources_potion_range_and_movement(loaded: tuple[str, Rotation, dict[str, str]]) -> None:
    cases: list[tuple[dict[str, Value], int | None]] = [
        ({"player_health_pct": 55.0, "spec_power_runic_power": 41.9}, None),
        ({"player_health_pct": 55.1, "spec_power_runic_power": 42.0}, None),
        ({"spec_power_runic_power": 99.9}, None),
        ({"spec_power_runic_power": 100.0}, 23),
        ({"buff_441416": True, "spec_power_rune": 1}, None),
        ({"buff_441416": True, "spec_power_rune": 2}, 16),
        ({"item_241308": True}, None),
        ({"in_burst": True}, None),
        ({"item_241308": True, "in_burst": True}, 15),
        ({"item_241308": True, "in_burst": True, "player_is_moving": True}, None),
        ({"cooldown_49028": 0.0, "in_burst": True, "item_241308": True}, 12),
        ({"cooldown_49028": 0.0, "in_burst": True, "player_is_moving": True}, None),
        ({"charges_50842": 1.0, "range_49998": True}, 17),
        ({"charges_50842": 1.0, "range_49998": False}, 30),
        ({"charges_50842": 1.0, "range_49998": True, "debuff_55078": True}, 30),
        ({"charges_43265": 2.0, "buff_81136": True, "player_is_moving": True}, 19),
        ({"charges_43265": 2.0}, 20),
        ({"charges_43265": 2.0, "player_is_moving": True}, None),
        ({"buff_81136": True}, 21),
        ({"buff_81136": True, "player_is_moving": True}, None),
        ({"charges_50842": 1.0, "buff_1265968": True}, 22),
        ({"buff_1264407": True, "spec_power_rune": 1}, 24),
        ({"spec_power_rune": 3}, 25),
        ({"spec_power_rune": 1}, 29),
        ({"cooldown_195292": 0.0, "stacks_195181": 9.0}, 26),
        ({"cooldown_46585": 0.0}, 27),
        ({"charges_50842": 2.0}, 28),
        ({"cooldown_439843": 0.0, "target_health_pct": 19.9}, None),
        ({"cooldown_439843": 0.0, "target_health_pct": 20.0}, 18),
    ]
    for updates, expected in cases:
        assert_decision(loaded, updates, expected)


@pytest.mark.parametrize("loaded", ["protection"], indirect=True)
def test_protection_resources_duplicates_and_movement(loaded: tuple[str, Rotation, dict[str, str]]) -> None:
    cases: list[tuple[dict[str, Value], int | None]] = [
        ({"spec_power_holy_power": 2, "duration_132403": 4.0}, None),
        ({"spec_power_holy_power": 3, "duration_132403": 4.0}, 9),
        ({"spec_power_holy_power": 3, "duration_132403": 4.1}, None),
        ({"player_health_pct": 75.0, "stacks_327510": 2.0, "spec_power_mana": 19.9}, None),
        ({"player_health_pct": 75.1, "stacks_327510": 2.0, "spec_power_mana": 20.0}, None),
        ({"player_health_pct": 55.0, "stacks_327510": 1.0, "spec_power_mana": 5.0}, 11),
        ({"player_health_pct": 55.0, "stacks_327510": 1.0, "spec_power_mana": 4.9}, None),
        ({"player_health_pct": 90.0, "stacks_327510": 2.0, "stacks_182104": 2.0, "spec_power_holy_power": 3, "spec_power_mana": 50.0}, 12),
        ({"player_health_pct": 90.0, "stacks_327510": 2.0, "stacks_182104": 3.0, "spec_power_holy_power": 3, "spec_power_mana": 50.0}, None),
        ({"duration_188370": 1.0, "cooldown_26573": 0.0}, 16),
        ({"duration_188370": 1.0, "cooldown_26573": 0.0, "player_is_moving": True}, None),
        ({"charges_275779": 2.0, "in_burst": True, "cooldown_389539": 0.0}, 17),
        ({"in_burst": True, "cooldown_389539": 0.0}, 18),
        ({"in_burst": True, "cooldown_389539": 0.0, "player_is_moving": True}, None),
        ({"cooldown_375576": 0.0}, None),
        ({"in_burst": True, "cooldown_375576": 0.0, "spec_power_holy_power": 2}, 19),
        ({"in_burst": True, "cooldown_375576": 0.0, "spec_power_holy_power": 3}, None),
        ({"in_burst": True, "cooldown_375576": 0.0, "player_is_moving": True}, None),
        ({"in_burst": True, "charges_432459": 2.0, "charges_432472": 2.0}, 20),
        ({"in_burst": True, "charges_432472": 2.0}, 21),
        ({"charges_432459": 2.0, "charges_432472": 2.0}, None),
        ({"cooldown_31935": 0.0, "range_31935": False}, 22),
        ({"charges_275779": 1.0}, 23),
        ({"spec_power_holy_power": 5, "charges_204019": 1.0}, 24),
        ({"charges_204019": 1.0}, 25),
    ]
    for updates, expected in cases:
        assert_decision(loaded, updates, expected)


@pytest.mark.parametrize("loaded", ["protection"], indirect=True)
def test_small_shining_light_two_stacks_survives_pixel_roundtrip(loaded: tuple[str, Rotation, dict[str, str]]) -> None:
    _, rotation, names = loaded
    plugin = next(entry.instance for entry in rotation.conditions if names[entry.title] == "stacks_182104")
    assert plugin.output.widths == (3,)
    decoder = PixelDecoder(np.zeros((20, 256, 3), dtype=np.uint8))
    for stacks in range(4):
        # 三格十二列，每层四列；完整区域包含左右各两列红色分隔。
        pixels = np.zeros((4, 16, 3), dtype=np.uint8)
        pixels[:, :2] = [255, 0, 0]
        pixels[:, -2:] = [255, 0, 0]
        pixels[:, 2 : 2 + stacks * 4] = 255
        value = plugin.value([], [ValueBar(1, 3, pixels)], [], decoder=decoder)
        assert type(value) is float and value == float(stacks)
        assert_decision(loaded, {"player_health_pct": 90.0, "stacks_327510": 2.0, "stacks_182104": value, "spec_power_holy_power": 3, "spec_power_mana": 50.0}, 12 if stacks == 2 else None)
