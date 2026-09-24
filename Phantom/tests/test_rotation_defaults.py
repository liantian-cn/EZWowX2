import os
import tomllib
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import ClassVar, cast
from unittest.mock import Mock

import pytest

import phantom.core.rotation as rotation_module
from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output, Value
from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.rotation import RotationError, load_rotation

HEADER = """# 中文说明：默认参数补写
schema_version = 1
uuid = "550e8400-e29b-41d4-a716-446655440000"
macros = []
rotation = []

[profile]
title = "默认参数验证"
description = ""
unit_class = "DEATHKNIGHT"
unit_spec = 1
"""
DISPEL_PLUGINS = ("player_has_dispellable_debuff", "target_has_dispellable_buff", "focus_has_dispellable_buff")
DISPEL_DEFAULTS = dict.fromkeys(("Magic", "Poison", "Disease", "Curse", "Stealth", "Special", "Enrage"), False)


def condition(plugin: str, args: str = "", *, title: str = "条件") -> str:
    return f'\n[[conditions]]\ntitle = "{title}"\nplugin = "{plugin}@dev"\n{args}'


def write_rotation(tmp_path: Path, conditions: str) -> Path:
    path = tmp_path / "defaults.toml"
    path.write_text(HEADER + conditions, encoding="utf-8")
    return path


def saved_conditions(path: Path) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], tomllib.loads(path.read_text(encoding="utf-8"))["conditions"])


@pytest.mark.parametrize(
    ("plugin", "arguments", "expected"),
    [
        ("aura_player_buff_duration", "aura_ids = [1], duration = 12, player_only = false", 3),
        ("aura_player_buff_duration", "aura_ids = [1], duration = 13.5, player_only = true", 4),
        ("aura_target_debuff_duration", "aura_ids = [1], duration = 40", 8),
        ("spell_charges", "spell_ids = [1], max_charges = 3", 2),
        ("spec_power_soul_shards", "fractional = true", 25),
    ],
)
def test_derived_width_is_not_written_and_explicit_override_is_preserved(tmp_path: Path, plugin: str, arguments: str, expected: int) -> None:
    path = write_rotation(tmp_path, condition(plugin, f"plugin_args = {{ {arguments} }}\n", title="自动宽度") + condition(plugin, f"plugin_args = {{ {arguments}, width = 30 }}\n", title="显式宽度"))
    before = path.read_bytes()
    rotation = load_rotation(path)
    assert [entry.instance.output.widths for entry in rotation.conditions] == [(expected,), (30,)]
    assert path.read_bytes() == before
    assert "width" not in cast(dict[str, object], saved_conditions(path)[0]["plugin_args"])
    assert cast(dict[str, object], saved_conditions(path)[1]["plugin_args"])["width"] == 30


def test_soul_shards_static_default_does_not_persist_fractional_layout(tmp_path: Path) -> None:
    path = write_rotation(tmp_path, condition("spec_power_soul_shards"))
    rotation = load_rotation(path)
    assert saved_conditions(path)[0]["plugin_args"] == {"fractional": False}
    assert rotation.conditions[0].instance.output.value_type is int
    assert rotation.conditions[0].instance.output.output_type == "cell"


@pytest.mark.parametrize("invalid", ["0", "-1", "true", "1.5", '"2"'])
@pytest.mark.parametrize(
    "plugin,arguments",
    [("aura_player_buff_duration", "aura_ids=[1],duration=12"), ("aura_target_debuff_duration", "aura_ids=[1],duration=12"), ("spell_charges", "spell_ids=[1],max_charges=2"), ("spec_power_soul_shards", "fractional=true")],
)
def test_invalid_derived_width_prevents_other_defaults_writeback(tmp_path: Path, plugin: str, arguments: str, invalid: str) -> None:
    path = write_rotation(tmp_path, condition("player_health_pct", title="待补默认") + condition(plugin, f"plugin_args = {{ {arguments}, width = {invalid} }}\n"))
    before = path.read_bytes()
    with pytest.raises(RotationError):
        load_rotation(path)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    ("plugin", "args", "defaults"),
    [
        ("player_health_pct", "", {"use_predicted": True}),
        ("target_health_pct", "plugin_args = {}\n", {"use_predicted": True}),
        ("focus_health_pct", "[conditions.plugin_args]\n", {"use_predicted": True}),
        ("player_melee_enemies_count", "plugin_args = { spell_id = 49998 }\n", {"combat_only": False}),
        ("player_range_aura_units_count", "[conditions.plugin_args]\nspell_id = 49998\naura_id = 55078\n", {"combat_only": False}),
        ("player_has_buff", "plugin_args = { buff_ids = [195181] }\n", {"player_only": True}),
        ("aura_player_buff_duration", "plugin_args = { aura_ids = [195181], duration = 30 }\n", {"player_only": True}),
        ("aura_player_buff_stacks", "plugin_args = { aura_ids = [195181], max_value = 10 }\n", {"min_value": 0, "width": 2, "player_only": True}),
        ("aura_target_debuff_stacks", "[conditions.plugin_args]\naura_ids = [55078]\nmax_value = 10\n", {"min_value": 0, "width": 2}),
    ],
)
def test_builtin_top_level_defaults(tmp_path: Path, plugin: str, args: str, defaults: dict[str, object]) -> None:
    path = write_rotation(tmp_path, condition(plugin, args))
    before = saved_conditions(path)[0].get("plugin_args", {})
    assert isinstance(before, dict)
    rotation = load_rotation(path)
    assert saved_conditions(path)[0]["plugin_args"] == before | defaults
    for name, value in defaults.items():
        assert getattr(rotation.conditions[0].instance, name) == value
    assert "layout" not in saved_conditions(path)[0]
    assert "unit_class_id" not in path.read_text(encoding="utf-8")
    assert 'macro = "Idle"' not in path.read_text(encoding="utf-8")
    assert rotation.rules[-1].macro == "Idle"


@pytest.mark.parametrize("plugin", DISPEL_PLUGINS)
@pytest.mark.parametrize(
    "args",
    [
        "plugin_args = { dispel_types = {} }\n",
        "plugin_args = { dispel_types = { Magic = true, Poison = false } }\n",
        "[conditions.plugin_args.dispel_types]\nMagic = true\nPoison = false\n",
        "plugin_args.dispel_types.Magic = true\nplugin_args.dispel_types.Poison = false\n",
        "[conditions.plugin_args.dispel_types]\nMagic = true\nPoison = false\n[conditions.plugin_args]\n# 父表晚于子表声明\n",
    ],
)
def test_nested_dispel_defaults(tmp_path: Path, plugin: str, args: str) -> None:
    path = write_rotation(tmp_path, condition(plugin, args))
    original = deepcopy(saved_conditions(path)[0]["plugin_args"])
    assert isinstance(original, dict)
    expected = DISPEL_DEFAULTS | original["dispel_types"]
    load_rotation(path)
    assert saved_conditions(path)[0]["plugin_args"] == {"dispel_types": expected}


@pytest.mark.parametrize(
    ("plugin", "args"),
    [
        ("player_health_pct", 'plugin_args = { use_predicted = "" }\n'),
        ("player_health_pct", "plugin_args = { use_predicted = 0 }\n"),
        ("player_health_pct", "plugin_args = { unknown = true }\n"),
        ("player_melee_enemies_count", "plugin_args = { combat_only = false }\n"),
        ("player_melee_enemies_count", "plugin_args = { spell_id = 1, combat_only = 0 }\n"),
        ("aura_player_buff_stacks", "plugin_args = { aura_ids = [], max_value = 10 }\n"),
        ("aura_target_debuff_stacks", "plugin_args = { aura_ids = [1], max_value = 10, width = 0 }\n"),
        ("aura_target_debuff_stacks", "plugin_args = { aura_ids = [1], max_value = 10, min_value = false }\n"),
        *[
            (plugin, args)
            for plugin in DISPEL_PLUGINS
            for args in ("", "plugin_args = {}\n", "plugin_args = { dispel_types = false }\n", "plugin_args = { dispel_types = { Magic = 0 } }\n", "plugin_args = { dispel_types = { Unknown = true } }\n")
        ],
    ],
)
def test_invalid_or_missing_arguments_prevent_all_writes(tmp_path: Path, plugin: str, args: str) -> None:
    path = write_rotation(tmp_path, condition("player_health_pct", title="待补默认") + condition(plugin, args))
    before = path.read_bytes()
    modified = path.stat().st_mtime_ns
    with pytest.raises(RotationError):
        load_rotation(path)
    assert path.read_bytes() == before
    assert path.stat().st_mtime_ns == modified


@pytest.mark.parametrize("stage", ["rule", "allocate"])
def test_late_validation_failure_does_not_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str) -> None:
    path = write_rotation(tmp_path, condition("player_health_pct"))
    if stage == "rule":
        path.write_text(path.read_text(encoding="utf-8").replace("rotation = []", 'rotation = [{ condition = "未知条件", macro = "Idle" }]'), encoding="utf-8")
    else:
        monkeypatch.setattr(rotation_module, "allocate", Mock(side_effect=ValueError("模拟布局冻结失败")))
    before = path.read_bytes()
    with pytest.raises(RotationError):
        load_rotation(path)
    assert path.read_bytes() == before


@pytest.mark.parametrize("legacy", ["", 'key = "F1" # 保留旧字段但不生效\nbind_key = false\n'])
def test_format_comments_macros_order_and_crlf_preserved(tmp_path: Path, legacy: str) -> None:
    path = write_rotation(tmp_path, condition("player_health_pct", "# 参数说明\n[conditions.plugin_args] # 保留表注释\n", title="生命") + condition("spell_gcd", title="冷却"))
    macro = '''[[macros]]
name = "中文宏"
macro_text = """
/cast [@player] 灵界打击
/say 中文多行宏
""" # 宏注释

[[rotation]]
condition = "生命 < 50 and 冷却 == 0"
macro = "中文宏"
'''
    macro = macro.replace('name = "中文宏"\n', 'name = "中文宏"\n' + legacy)
    source = path.read_text(encoding="utf-8").replace("macros = []\nrotation = []\n", "") + "\n" + macro
    path.write_bytes(source.replace("\n", "\r\n").encode("utf-8"))
    rotation = load_rotation(path)
    saved = path.read_bytes().decode("utf-8")
    assert rotation.macros[0].key == "RCTRL-NUMPAD1"
    assert "\n" not in saved.replace("\r\n", "")
    assert macro.replace("\n", "\r\n") in saved
    assert "# 中文说明：默认参数补写\r\n" in saved
    assert "# 参数说明\r\n[conditions.plugin_args] # 保留表注释\r\n" in saved
    assert [entry.title for entry in rotation.conditions] == ["生命", "冷却"]
    assert [row["title"] for row in saved_conditions(path)] == ["生命", "冷却"]
    assert saved_conditions(path)[0]["plugin_args"] == {"use_predicted": True}
    assert "plugin_args" not in saved_conditions(path)[1]


@pytest.mark.parametrize(
    "legacy",
    [
        'layout = "错误类型" # 用户旧布局\n',
        'layout = { output_type = "wrong", regions = [{ x = 999, y = -1 }] } # 用户旧布局\n',
        '[conditions.layout] # 用户旧布局\noutput_type = "wrong"\n[[conditions.layout.regions]]\nx = 999\ny = -1\n[[conditions.layout.regions]]\nx = 42\ny = 99\n# 保留分组说明\n',
    ],
)
def test_legacy_layout_is_ignored_and_preserved(tmp_path: Path, legacy: str) -> None:
    path = write_rotation(tmp_path, condition("player_health_pct", legacy))
    rotation = load_rotation(path)
    assert legacy in path.read_text(encoding="utf-8")
    assert rotation.board_width == 28
    assert rotation.conditions[0].instance.regions[0].metadata() == {"x": 1, "y": 2}


def test_explicit_values_and_instances_are_independent(tmp_path: Path) -> None:
    path = write_rotation(
        tmp_path,
        condition("player_health_pct", "plugin_args = { use_predicted = false }\n", title="显式")
        + condition("player_health_pct", title="默认")
        + condition("aura_player_buff_stacks", "plugin_args = { aura_ids = [1], max_value = 10, min_value = 0, width = 4, player_only = false }\n", title="层数")
        + condition("player_has_dispellable_debuff", "plugin_args = { dispel_types = { Magic = true } }\n", title="驱散一")
        + condition("player_has_dispellable_debuff", "plugin_args = { dispel_types = {} }\n", title="驱散二"),
    )
    rotation = load_rotation(path)
    rows = saved_conditions(path)
    assert rows[0]["plugin_args"] == {"use_predicted": False}
    assert rows[1]["plugin_args"] == {"use_predicted": True}
    assert rows[2]["plugin_args"] == {"aura_ids": [1], "max_value": 10, "min_value": 0, "width": 4, "player_only": False}
    assert rows[3]["plugin_args"] == {"dispel_types": DISPEL_DEFAULTS | {"Magic": True}}
    assert rows[4]["plugin_args"] == {"dispel_types": DISPEL_DEFAULTS}
    assert rotation.conditions[0].instance is not rotation.conditions[1].instance


class CustomDefaults(Condition):
    config_defaults: ClassVar[Mapping[str, object]] = {"enabled": True, "count": 5, "text": "默认", "items": [1], "nested": {"deep": {"added": 2, "kept": 3}}, "optional": {"added": True}, "custom_key": 17}

    def __init__(self, args: dict[str, object]) -> None:
        super().__init__(Output("none", 0, bool, "scalar"))
        self.received: dict[str, object] = deepcopy(args)

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> Value:
        return False

    def fallback_value(self) -> Value:
        return False


class CustomRegistry(Registry):
    def create(self, identifier: str, args: dict[str, object]) -> Condition:
        assert identifier == "custom@dev"
        return CustomDefaults(args)


@pytest.mark.parametrize("nested", [{"a": False}, [{"a": False}], {"deep": {"a": False}}])
def test_new_nested_default_under_dotted_keys_keeps_its_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, nested: object) -> None:
    defaults = {"flag": True, "nested": nested}
    monkeypatch.setattr(CustomDefaults, "config_defaults", defaults)
    legacy = 'layout = { output_type = "none", regions = [] } # 旧布局留在条件内\n'
    path = write_rotation(tmp_path, condition("custom", "plugin_args.flag = false\n" + legacy))
    expected = tomllib.loads(path.read_text(encoding="utf-8"))
    expected["conditions"][0]["plugin_args"]["nested"] = nested
    registry = CustomRegistry(tmp_path / "plugins")

    load_rotation(path, registry)

    assert tomllib.loads(path.read_text(encoding="utf-8")) == expected
    assert legacy in path.read_text(encoding="utf-8")
    before = path.read_bytes()
    load_rotation(path, registry)
    assert path.read_bytes() == before
    assert defaults == {"flag": True, "nested": nested}


def test_instance_defaults_without_metadata_preserve_empty_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = write_rotation(tmp_path, condition("custom", 'plugin_args = { enabled = false, count = 0, text = "", items = [], nested = { deep = { kept = 0 } }, optional = "" }\n'))
    original_defaults = deepcopy(CustomDefaults.config_defaults)
    original_args = deepcopy(saved_conditions(path)[0]["plugin_args"])
    registry = CustomRegistry(tmp_path / "无元数据插件目录")
    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(file: Path) -> bytes:
        assert file.name != "plugin.toml"
        return original_read_bytes(file)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    rotation = load_rotation(path, registry)
    assert saved_conditions(path)[0]["plugin_args"] == {"enabled": False, "count": 0, "text": "", "items": [], "nested": {"deep": {"kept": 0, "added": 2}}, "optional": "", "custom_key": 17}
    instance = rotation.conditions[0].instance
    assert isinstance(instance, CustomDefaults)
    assert instance.received == original_args
    assert CustomDefaults.config_defaults == original_defaults
    assert not registry.root.exists()


@pytest.mark.parametrize("needs_defaults", [False, True])
def test_no_write_when_unchanged_or_loaded_again(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, needs_defaults: bool) -> None:
    path = write_rotation(tmp_path, condition("player_health_pct" if needs_defaults else "spell_gcd"))
    if needs_defaults:
        load_rotation(path)
    before = path.read_bytes()
    modified = path.stat().st_mtime_ns
    writer = Mock(side_effect=AssertionError("相同配置不得触发写入"))
    monkeypatch.setattr(rotation_module, "atomic_write", writer)
    load_rotation(path)
    writer.assert_not_called()
    assert path.read_bytes() == before
    assert path.stat().st_mtime_ns == modified
    if not needs_defaults:
        assert "plugin_args" not in saved_conditions(path)[0]


@pytest.mark.parametrize("failure", ["atomic_write", "replace"])
def test_write_failure_aborts_load_without_damaging_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    path = write_rotation(tmp_path, condition("player_health_pct"))
    before = path.read_bytes()
    # 仅模拟权限失败，不触发真实 Windows 权限操作。
    writer = Mock(side_effect=PermissionError("模拟写入失败"))
    if failure == "atomic_write":
        monkeypatch.setattr(rotation_module, "atomic_write", writer)
    else:
        monkeypatch.setattr(os, "replace", writer)
    with pytest.raises(RotationError, match="模拟写入失败"):
        load_rotation(path)
    writer.assert_called_once()
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def test_concurrent_source_change_is_not_overwritten(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = write_rotation(tmp_path, condition("player_health_pct"))
    concurrent = path.read_bytes() + "\n# 用户同时修改\n".encode()

    def allocate_and_edit(conditions: list[Condition]) -> int:
        width = allocate(conditions)
        path.write_bytes(concurrent)
        return width

    writer = Mock(side_effect=AssertionError("并发修改后不得覆盖文件"))
    monkeypatch.setattr(rotation_module, "allocate", allocate_and_edit)
    monkeypatch.setattr(rotation_module, "atomic_write", writer)
    with pytest.raises(RotationError):
        load_rotation(path)
    writer.assert_not_called()
    assert path.read_bytes() == concurrent
