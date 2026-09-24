"""目标／焦点与黑名单的生成、像素解码和 Lua 生命周期验证，不替代客户端验收。"""

import re
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.base import Condition
from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.generator import render
from phantom.core.pixels import Cell, IconTile, PixelDecoder
from phantom.core.rotation import ConditionEntry, load_rotation
from tests.test_player_conditions import decode, value

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = ("is_exists", "is_alive", "can_attack", "in_combat", "cast_progress", "cast_interruptible", "cast_icon", "has_dispellable_buff")
CASES: dict[str, dict[str, object]] = {f"{unit}_{suffix}": ({"dispel_types": {"Magic": True}} if suffix == "has_dispellable_buff" else {}) for unit in ("target", "focus") for suffix in SUFFIXES}
CASES["interrupt_blacklist_icons"] = {}


def create(name: str, args: dict[str, object] | None = None) -> Condition:
    return Registry().create(f"{name}@dev", CASES[name] if args is None else args)


def harness(plugins: list[Condition], *, initialize: bool = True) -> tuple[Any, Any, Any]:
    allocate(plugins)
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state, addon = lua.execute((ROOT / "tests/lua/player_conditions_harness.lua").read_text(encoding="utf-8"))
    lua.execute((ROOT / "tests/lua/target_focus_conditions_harness.lua").read_text(encoding="utf-8"), state, addon)
    execute: Any = lua.eval("function(source, addon) assert(loadstring(source))('PhantomTest', addon) end")
    for file in ("02_config.lua", "06_panel.lua", "07_cell_backplate.lua", "08_cell.lua", "11_icon_tile_backplate.lua", "12_icon_tile.lua"):
        execute((ROOT / "phantom/lua/runtime" / file).read_text(encoding="utf-8"), addon)
    for index, plugin in enumerate(plugins):
        execute(plugin.generate_lua(f"target-focus-{index}"), addon)
    if initialize:
        state.initialize(state)
    return lua, state, addon


@pytest.mark.parametrize("name", CASES)
def test_parameters_pixels_and_early_events(name: str) -> None:
    with pytest.raises(ValueError):
        create(name, {**CASES[name], "unknown": 1})
    plugin = create(name)
    _, state, _ = harness([plugin], initialize=False)
    state.event(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)
    state.initialize(state)
    decoder = PixelDecoder(np.zeros((20, 128, 3), dtype=np.uint8))
    assert plugin.value([], [], [], decoder=decoder) == plugin.fallback_value()
    if plugin.output.output_type == "cell":
        assert decode(plugin, 0) == plugin.fallback_value()
        assert decode(plugin, 255) == (100.0 if plugin.output.value_type is float else True)
        pixels = np.full((4, 4, 3), 255, dtype=np.uint8)
        pixels[1, 1] = [255, 0, 0]
        assert plugin.value([Cell(1, 2, pixels)], [], [], decoder=decoder) == plugin.fallback_value()


@pytest.mark.parametrize("unit", ["target", "focus"])
@pytest.mark.parametrize("suffix,field", [("is_exists", None), ("is_alive", "dead"), ("can_attack", "attackable"), ("in_combat", "combat")])
def test_unit_semantics_and_deferred_refresh(unit: str, suffix: str, field: str | None) -> None:
    plugin = create(f"{unit}_{suffix}")
    lua, state, _ = harness([plugin])
    assert value(plugin, state) is False
    state.units[unit] = lua.table_from({"dead": False, "attackable": True, "enemy": False, "combat": True})
    event = f"PLAYER_{unit.upper()}_CHANGED"
    state.event(state, event)
    assert value(plugin, state) is False
    state.flushTimers(state)
    assert value(plugin, state) is True
    if field:
        for boolean in (False, True):
            state.units[unit][field] = state.secret(state, boolean)
            state.event(state, "UNIT_FLAGS", unit)
            state.flushTimers(state)
            assert value(plugin, state) is (not boolean if suffix == "is_alive" else boolean)
    state.units[unit] = None
    state.event(state, event)
    state.flushTimers(state)
    assert value(plugin, state) is False


@pytest.mark.parametrize("unit", ["target", "focus"])
@pytest.mark.parametrize("mode", ["casting", "channeling"])
def test_cast_progress_interruptible_icon_and_clear(unit: str, mode: str) -> None:
    plugins = [create(f"{unit}_{suffix}") for suffix in ("cast_progress", "cast_interruptible", "cast_icon")]
    lua, state, _ = harness(plugins)
    state.units[unit] = lua.table_from({"enemy": True})
    state.casts[unit] = lua.table_from({"mode": mode, "texture": state.secret(state, 456), "blocked": state.secret(state, False), "empowered": False})
    state.progress = 0.4
    state.secretDuration = True
    state.event(state, f"PLAYER_{unit.upper()}_CHANGED")
    state.flushTimers(state)
    assert value(plugins[0], state) == 40.0
    assert value(plugins[1], state, 2) is True
    assert state.lastDurationUnit == unit
    icon = state.icons[1]
    assert icon.textures[2].texture == 456
    assert icon.textures[2].hidden is False
    for blocked, expected in ((True, False), (False, True), (None, False)):
        state.casts[unit].blocked = blocked
        state.event(state, "UNIT_SPELLCAST_INTERRUPTIBLE", unit)
        state.flushTimers(state)
        assert value(plugins[1], state, 2) is expected
    state.casts[unit].blocked = state.secret(state, True)
    state.event(state, "UNIT_SPELLCAST_NOT_INTERRUPTIBLE", unit)
    state.flushTimers(state)
    assert value(plugins[1], state, 2) is False
    state.noDuration = True
    state.tick(state, 0.2)
    assert value(plugins[0], state) == 0.0
    state.noDuration = False
    state.units[unit] = None
    state.event(state, f"PLAYER_{unit.upper()}_CHANGED")
    state.flushTimers(state)
    assert value(plugins[0], state) == 0.0
    assert value(plugins[1], state, 2) is False
    assert icon.textures[2].hidden is True
    assert icon.textures[3].hidden is True
    state.units[unit] = lua.table_from({})
    state.casts[unit] = None
    state.event(state, "UNIT_SPELLCAST_STOP", unit)
    state.flushTimers(state)
    assert value(plugins[1], state, 2) is False


@pytest.mark.parametrize("unit", ["target", "focus"])
@pytest.mark.parametrize("types", [{}, {"Magic": False}, {"Magic": True, "Enrage": True}])
def test_dispel_filters_and_enemy_gate(unit: str, types: dict[str, bool]) -> None:
    plugin = create(f"{unit}_has_dispellable_buff", {"dispel_types": types})
    lua, state, _ = harness([plugin])
    container = next(frame for frame in state.frames.values() if frame.kind == "AuraContainer")
    assert container.hidden is True
    assert container.slots.aura.filter == "HELPFUL|RAID_PLAYER_DISPELLABLE"
    expected = dict.fromkeys(("Magic", "Poison", "Disease", "Curse", "Stealth", "Special", "Enrage"), False) | types
    assert dict(container.slots.aura.options.candidateFilters.includeDispelTypes.items()) == expected
    for enemy in (False, True):
        state.units[unit] = lua.table_from({"enemy": enemy, "attackable": not enemy})
        state.event(state, f"PLAYER_{unit.upper()}_CHANGED")
        state.flushTimers(state)
        assert container.hidden is not enemy
    state.units[unit].enemy = False
    state.event(state, "UNIT_FACTION", "player")
    state.flushTimers(state)
    assert container.hidden is True


@pytest.mark.parametrize("unit", ["target", "focus"])
@pytest.mark.parametrize("bad", [None, [], 1, {"Magic": 1}, {"Unknown": True}, {"Enrage": "true"}])
def test_dispel_rejects_invalid_mapping(unit: str, bad: object) -> None:
    with pytest.raises(ValueError):
        create(f"{unit}_has_dispellable_buff", {"dispel_types": bad})
    with pytest.raises(ValueError):
        create(f"{unit}_has_dispellable_buff", {})


def test_blacklist_panel_defaults_existing_profile_sort_failure_and_events() -> None:
    plugin = create("interrupt_blacklist_icons")
    lua, state, addon = harness([plugin], initialize=False)
    assert len(addon.ConfigRows) == 1
    assert addon.ConfigRows[1].type == "spell_list"
    config = addon.Config("interrupt_blacklist")
    config.set_value(config, lua.table_from({id_: True for id_ in range(100, 112)}))
    state.requests = lua.table_from([])
    for id_ in range(100, 112):
        state.spellTextures[id_] = id_ + 1000
    state.spellTextures[101] = None
    state.failedTextures[1102] = True
    state.initialize(state)
    assert list(state.requests.values()) == list(range(100, 112))
    assert len(state.icons) == 10
    assert len(list(config.get_value(config).keys())) == 12
    assert list(config.default_value.keys()) != []
    for index in range(1, 11):
        icon = state.icons[index]
        failed = index in (2, 3)
        assert icon.textures[2].hidden is failed
        assert icon.textures[3].hidden is failed
        if not failed:
            assert icon.textures[2].texture == 1099 + index
            assert icon.textures[3].r == 0.8
    state.spellTextures[101] = 1101
    state.event(state, "SPELL_DATA_LOAD_RESULT", 101, False)
    state.flushTimers(state)
    assert state.icons[2].textures[2].hidden is True
    state.event(state, "SPELL_DATA_LOAD_RESULT", 101, True)
    assert state.icons[2].textures[2].hidden is True
    state.flushTimers(state)
    assert state.icons[2].textures[2].hidden is False
    assert len(state.requests) == 12
    state.event(state, "SPELL_DATA_LOAD_RESULT", 100, True)
    config.set_value(config, lua.table_from({}))
    state.flushTimers(state)
    assert all(icon.textures[2].hidden and icon.textures[3].hidden for icon in state.icons.values())
    state.switchProfile(state, "other")
    assert sorted(config.get_value(config).keys()) == [468962, 1248327, 1254669, 1258436, 1262510, 1262526]
    config.set_value(config, lua.table_from({999: True}))
    state.switchProfile(state, "default")
    assert len(config.get_value(config)) == 0
    state.switchProfile(state, "other")
    assert dict(config.get_value(config).items()) == {999: True}


@pytest.mark.parametrize("unit", ["target", "focus"])
def test_cast_icon_uses_display_only_texture_path(unit: str) -> None:
    # 普通 Lua 的 table 替身不能模拟秘密布尔的分支错误，静态约束补充返回值回归保护。
    plugin = create(f"{unit}_cast_icon")
    allocate([plugin])
    source = plugin.generate_lua("cast-icon-regression")
    source = re.sub(r"--\[\[.*?\]\]|--[^\n]*", "", source, flags=re.DOTALL)
    assert "SetTexture" not in source
    calls = [line.strip() for line in source.splitlines() if "SetIcon" in line]
    assert calls
    assert all(re.fullmatch(r"display:SetIcon\(\w+\)", line) for line in calls)


@pytest.mark.parametrize("unit", ["target", "focus"])
@pytest.mark.parametrize("mode", ["casting", "channeling"])
@pytest.mark.parametrize("texture_result", [True, False, None])
@pytest.mark.parametrize("clear_reason", ["idle", "missing_unit"])
def test_cast_icon_ignores_texture_result_and_clears_on_state_change(unit: str, mode: str, texture_result: bool | None, clear_reason: str) -> None:
    plugin = create(f"{unit}_cast_icon")
    lua, state, _ = harness([plugin])
    state.units[unit] = lua.table_from({})
    state.casts[unit] = lua.table_from({"mode": mode, "texture": state.secret(state, 456), "empowered": False})
    event = f"PLAYER_{unit.upper()}_CHANGED"
    state.event(state, event)
    state.flushTimers(state)
    icon = state.icons[1]
    assert icon.textures[2].hidden is False
    assert icon.textures[3].hidden is False
    state.overrideTextureResult = True
    state.textureResult = texture_result
    state.casts[unit].texture = state.secret(state, 789)
    state.event(state, event)
    assert icon.textures[2].hidden is False
    state.flushTimers(state)
    assert icon.textures[2].texture == 789
    assert icon.textures[2].hidden is False
    assert icon.textures[3].hidden is False
    if clear_reason == "idle":
        state.casts[unit] = None
    else:
        state.units[unit] = None
    state.event(state, event)
    state.flushTimers(state)
    assert icon.textures[2].hidden is True
    assert icon.textures[3].hidden is True
    state.units[unit] = lua.table_from({})
    state.casts[unit] = lua.table_from({"mode": mode, "texture": state.secret(state, 456), "empowered": False})
    state.event(state, event)
    state.flushTimers(state)
    assert icon.textures[2].texture == 456
    assert icon.textures[2].hidden is False
    assert icon.textures[3].hidden is False


def test_blacklist_and_cast_icon_real_pixels() -> None:
    decoder = PixelDecoder(np.zeros((20, 128, 3), dtype=np.uint8))
    empty = np.zeros((8, 8, 3), dtype=np.uint8)
    full = np.full((8, 8, 3), 100, dtype=np.uint8)
    tiles = [IconTile(index + 1, full if index in (0, 3, 9) else empty) for index in range(10)]
    plugin = create("interrupt_blacklist_icons")
    assert plugin.value([], [], tiles, decoder=decoder) == [tiles[0].hash] * 3
    assert plugin.value([], [], [IconTile(index + 1, empty) for index in range(10)], decoder=decoder) == []
    assert plugin.value([], [], tiles[:9], decoder=decoder) == []
    for unit in ("target", "focus"):
        icon = create(f"{unit}_cast_icon")
        assert icon.value([], [], [tiles[0]], decoder=decoder) == tiles[0].hash
        assert icon.value([], [], [tiles[1]], decoder=decoder) == ""


def test_blacklist_initial_defaults_applied_once_by_real_panel() -> None:
    lua, state, addon = harness([create("interrupt_blacklist_icons")], initialize=False)
    config = addon.Config("interrupt_blacklist")
    lua.execute("local config = ...; local original = config.set_default; function config:set_default(value) self.defaultCalls = (self.defaultCalls or 0) + 1; original(self, value) end", config)
    assert config.get_value(config) is None
    defaults = [468962, 1248327, 1254669, 1258436, 1262510, 1262526]
    for id_ in defaults:
        state.spellTextures[id_] = id_ + 1
    state.initialize(state)
    assert list(state.requests.values()) == defaults
    assert sorted(config.default_value.keys()) == defaults
    assert [state.icons[index].textures[2].texture for index in range(1, 7)] == [id_ + 1 for id_ in defaults]
    assert all(state.icons[index].textures[2].hidden for index in range(7, 11))
    buttons = [frame for frame in state.frames.values() if frame.name and "spellListSettingButton" in frame.name]
    assert len(buttons) == 1
    state.tick(state, 20)
    assert list(state.requests.values()) == defaults
    state.switchProfile(state, "other")
    assert config.defaultCalls == 1


@pytest.mark.parametrize("unit", ["target", "focus"])
def test_progress_polling_preserves_remainder_and_unit_event_filter(unit: str) -> None:
    plugin = create(f"{unit}_cast_progress")
    lua, state, _ = harness([plugin])
    state.units[unit] = lua.table_from({})
    state.casts[unit] = lua.table_from({"mode": "casting"})
    state.progress = 0.6
    state.event(state, "UNIT_SPELLCAST_START", "pet")
    state.flushTimers(state)
    assert value(plugin, state) == 0.0
    state.tick(state, 0.1)
    assert value(plugin, state) == 0.0
    state.tick(state, 0.02)
    assert value(plugin, state) == 60.0
    state.progress = 1.0
    state.tick(state, 0.1)
    assert value(plugin, state) == 100.0


def test_documented_minimal_fragment_loads_and_generates(tmp_path: Path) -> None:
    document = (ROOT / ".agents/skills/phantom-plugin-dev/references/target-focus-example.md").read_text(encoding="utf-8")
    fragment = document.split("```toml\n", 1)[1].split("```", 1)[0]
    base = (ROOT / "tests/fixtures/engine-rotation.toml").read_text(encoding="utf-8").split("[[conditions]]", 1)[0]
    path = tmp_path / "example.toml"
    path.write_text("macros = []\nrotation = []\n" + base + fragment, encoding="utf-8")
    rotation = load_rotation(path)
    assert len(rotation.conditions) == 13
    assert len([entry for entry in rotation.conditions if entry.plugin == "interrupt_blacklist_icons@dev"]) == 1
    assert render(rotation, "PhantomTest")


def test_combined_generation_exact_versions(tmp_path: Path) -> None:
    entries = tuple(ConditionEntry(name, f"{name}@dev", create(name)) for name in CASES)
    width = allocate([entry.instance for entry in entries])
    rotation_path = tmp_path / "rotation.toml"
    rotation_path.write_bytes((ROOT / "tests/fixtures/engine-rotation.toml").read_bytes())
    rotation = replace(load_rotation(rotation_path), conditions=entries, macros=(), board_width=width)
    files = render(rotation, "PhantomTest")
    lua: Any = LuaRuntime()
    compile_lua: Any = lua.eval("function(source) assert(loadstring(source)) end")
    for path, data in files.items():
        if str(path).endswith(".lua"):
            compile_lua(data)
