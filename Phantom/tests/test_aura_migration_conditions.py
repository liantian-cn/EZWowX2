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
from phantom.core.pixels import Cell, PixelDecoder, ValueBar
from phantom.core.rotation import ConditionEntry, load_rotation

ROOT = Path(__file__).resolve().parents[1]
CASES: dict[str, dict[str, object]] = {
    "target_has_buff": {"aura_ids": [100, 200]},
    "focus_has_buff": {"aura_ids": [100, 200]},
    "target_has_debuff": {"aura_ids": [100, 200]},
    "focus_has_debuff": {"aura_ids": [100, 200]},
    "aura_player_buff_duration": {"aura_ids": [100, 200], "duration": 12},
    "aura_target_debuff_duration": {"aura_ids": [100, 200], "duration": 12},
    "aura_player_buff_stacks": {"aura_ids": [100, 200], "max_value": 5},
    "aura_target_debuff_stacks": {"aura_ids": [100, 200], "max_value": 5},
}

# 专属替身扩展：只检查初始化和官方显示绑定，不模拟秘密光环的内部筛选算法。
EXTENSION = """
local state, addon = ...
Enum.StatusBarInterpolation = {Immediate = 0}
Enum.StatusBarTimerDirection = {RemainingTime = 1}
addon.ValueBarLength = 0
addon.COLOR.RED = {GetRGBA = function() return 1, 0, 0, 1 end}
state.exists = true
state.assist = true
state.assistCalls = {}
UnitExists = function(unit) assert(unit == 'target' or unit == 'focus'); return state.exists end
UnitIsEnemy = function(player, unit)
    assert(player == 'player' and (unit == 'target' or unit == 'focus'))
    return state.enemy == true
end
UnitCanAssist = function(player, unit, immune, uninteractable)
    assert(player == 'player' and (unit == 'target' or unit == 'focus'))
    assert(immune == true and uninteractable == true)
    table.insert(state.assistCalls, unit)
    return state.assist
end
local original = CreateFrame
CreateFrame = function(kind, name, parent, template)
    local frame = original(kind, name, parent, template)
    function frame:Hide() self.hidden = true end
    function frame:SetShown(value) self.hidden = not value end
    function frame:SetOrientation(value) assert(value == 'HORIZONTAL'); self.orientation = value end
    function frame:SetColorFill(...) self.fillColor = {...} end
    function frame:SetUnit(unit)
        assert(unit == 'player' or unit == 'target' or unit == 'focus')
        self.unit = unit
    end
    function frame:RegisterUnitEvent(event, ...)
        self.events[event] = {...}
    end
    function frame:AddAuraSlot(key, filter, options)
        assert(kind == 'AuraContainer' and template == 'CustomAuraContainerTemplate')
        assert(self.slots[key] == nil)
        local button = CreateFrame('AuraButton', nil, self)
        options.initializeFrame(button)
        self.slots[key] = {filter = filter, options = options, button = button}
    end
    function frame:SetDurationBar(bar, options)
        assert(kind == 'AuraButton' and bar.parent == self and bar.kind == 'StatusBar')
        self.durationBar = bar
        self.durationOptions = options
    end
    function frame:SetApplicationBar(bar, options)
        assert(kind == 'AuraButton' and bar.parent == self and bar.kind == 'StatusBar')
        self.applicationBar = bar
        self.applicationOptions = options
    end
    return frame
end
function state:event(event, unit)
    for _, frame in ipairs(self.frames) do
        local filter = frame.events[event]
        local matches = filter == true
        if type(filter) == 'table' then
            for _, candidate in ipairs(filter) do if candidate == unit then matches = true end end
        end
        if matches and frame.OnEvent then frame.OnEvent(frame, event, unit) end
    end
end
"""


def create(name: str, args: dict[str, object] | None = None) -> Condition:
    return Registry().create(f"{name}@dev", CASES[name] if args is None else args)


def harness(plugins: list[Condition]) -> tuple[Any, Any, Any]:
    allocate(plugins)
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state, addon = lua.execute((ROOT / "tests/lua/player_conditions_harness.lua").read_text(encoding="utf-8"))
    lua.execute(EXTENSION, state, addon)
    execute: Any = lua.eval("function(source, addon) assert(loadstring(source))('PhantomTest', addon) end")
    for filename in ("07_cell_backplate.lua", "08_cell.lua", "09_value_bar_backplate.lua", "10_value_bar.lua"):
        execute((ROOT / "phantom/lua/runtime" / filename).read_text(encoding="utf-8"), addon)
    for index, plugin in enumerate(plugins):
        execute(plugin.generate_lua(f"aura-{index}"), addon)
    return lua, state, addon


@pytest.mark.parametrize("name", CASES)
def test_required_parameters(name: str) -> None:
    for field in CASES[name]:
        args = {key: value for key, value in CASES[name].items() if key != field}
        with pytest.raises(ValueError):
            create(name, args)
    with pytest.raises(ValueError):
        create(name, {**CASES[name], "unexpected": 1})


@pytest.mark.parametrize("name", CASES)
@pytest.mark.parametrize("bad", [[], [0], [-1], [True], [1.5], ["100"], None, 100, "100"])
def test_invalid_aura_ids(name: str, bad: object) -> None:
    with pytest.raises(ValueError):
        create(name, {**CASES[name], "aura_ids": bad})


@pytest.mark.parametrize(
    "name,field",
    [(name, field) for name in CASES for field in ("duration", "max_value", "width") if (field in CASES[name] or (field == "width" and name.endswith(("stacks", "duration")))) and (name, field) != ("aura_player_buff_duration", "duration")],
)
@pytest.mark.parametrize("bad", [True, False, 0, -1, 1.5, "2", None, float("inf")])
def test_positive_integer_parameters(name: str, field: str, bad: object) -> None:
    with pytest.raises(ValueError):
        create(name, {**CASES[name], field: bad})


@pytest.mark.parametrize("name", [name for name in CASES if name.endswith("stacks")])
@pytest.mark.parametrize("bad", [True, False, 0.0, 1, -1, "0", None])
def test_stacks_reject_nonzero_or_noninteger_minimum(name: str, bad: object) -> None:
    with pytest.raises(ValueError):
        create(name, {**CASES[name], "min_value": bad})


@pytest.mark.parametrize("name", CASES)
def test_real_pixel_decoding_and_fallback(name: str) -> None:
    plugin = create(name)
    decoder = PixelDecoder(np.zeros((20, 256, 3), dtype=np.uint8))
    assert plugin.value([], [], [], decoder=decoder) == plugin.fallback_value()
    if plugin.output.value_type is bool:
        for brightness in (0, 255, 127):
            cell = Cell(1, 2, np.full((4, 4, 3), brightness, dtype=np.uint8))
            assert plugin.value([cell], [], [], decoder=decoder) is (brightness == 255)
        pixels = np.full((4, 4, 3), 255, dtype=np.uint8)
        pixels[1, 1] = 0
        assert plugin.value([Cell(1, 2, pixels)], [], [], decoder=decoder) is False
    else:
        width = plugin.output.widths[0]
        scale = CASES[name].get("duration", CASES[name].get("max_value"))
        assert isinstance(scale, int)
        for white_columns in (0, 1, width * 2, width * 4):
            pixels = np.zeros((4, (width + 1) * 4, 3), dtype=np.uint8)
            pixels[:, :2] = [255, 0, 0]
            pixels[:, -2:] = [255, 0, 0]
            pixels[:, 2 : 2 + white_columns] = 255
            bar = ValueBar(1, width, pixels)
            result = plugin.value([], [bar], [], decoder=decoder)
            assert type(result) is float
            assert result == pytest.approx(white_columns / (width * 4) * scale)
        invalid = ValueBar(1, width, np.full((4, (width + 1) * 4, 3), 127, dtype=np.uint8))
        assert plugin.value([], [invalid], [], decoder=decoder) == 0.0


@pytest.mark.parametrize("name", CASES)
def test_lua_slot_binding_and_backing(name: str) -> None:
    plugin = create(name)
    lua, state, addon = harness([plugin])
    state.event(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)
    state.initialize(state)
    containers = [frame for frame in state.frames.values() if frame.kind == "AuraContainer"]
    assert len(containers) == 1
    container = containers[0]
    assert len(list(container.slots.keys())) == 1
    slot = container.slots.aura
    assert dict(slot.options.candidateFilters.includeSpellIDs.items()) == {100: True, 200: True}
    assert slot.filter == ("PLAYER|HARMFUL" if "debuff" in name else ("HELPFUL|PLAYER" if "player" in name else "HELPFUL"))
    unit = "player" if "player" in name else ("focus" if "focus" in name else "target")
    assert container.unit == unit
    if plugin.output.output_type == "value_bar":
        assert not any(frame.kind == "StatusBar" for frame in container.parent.children.values())
        assert container.parent.level == addon.FrameLevel.Backplate
        assert container.level == addon.FrameLevel.AuraContainer
        assert slot.button.level == addon.FrameLevel.AuraButton
        button = slot.button
        if "duration" in name:
            assert dict(button.durationOptions.items()) == {"interpolation": 0, "direction": 1}
            bar = button.durationBar
        else:
            assert dict(button.applicationOptions.items()) == {"maxApplications": 5}
            bar = button.applicationBar
        assert bar.level == addon.FrameLevel.AuraContent
        assert lua.eval("function(left, right) return left == right end")(bar.parent, button)
        assert bar.orientation == "HORIZONTAL"
        assert list(bar.barColor.values()) == [1, 1, 1, 1]
        assert button.width == plugin.output.widths[0] * 4
        assert button.height == 4
        assert (bar.textures[1].r, bar.textures[1].g, bar.textures[1].b) == (0, 0, 0)


@pytest.mark.parametrize("name", [name for name in CASES if "player" not in name])
def test_unit_classification_events_and_absence(name: str) -> None:
    _, state, _ = harness([create(name)])
    state.initialize(state)
    container = next(frame for frame in state.frames.values() if frame.kind == "AuraContainer")
    unit = "focus" if "focus" in name else "target"
    change = "PLAYER_FOCUS_CHANGED" if unit == "focus" else "PLAYER_TARGET_CHANGED"
    for assist in (True, False):
        state.assist = assist
        for event, event_unit in ((change, None), ("UNIT_FACTION", unit), ("UNIT_FACTION", "player"), ("UNIT_FLAGS", unit)):
            state.event(state, event, event_unit)
            state.flushTimers(state)
            assert container.hidden is (assist if "debuff" in name else not assist)
    calls = len(state.assistCalls)
    state.exists = False
    state.event(state, change)
    state.flushTimers(state)
    assert container.hidden is True
    assert len(state.assistCalls) == calls


def test_custom_stacks_width_and_zero_minimum() -> None:
    for name in (name for name in CASES if name.endswith("stacks")):
        plugin = create(name, {**CASES[name], "min_value": 0, "width": 7})
        assert plugin.output.widths == (7,)
        _, state, _ = harness([plugin])
        state.initialize(state)
        container = next(frame for frame in state.frames.values() if frame.kind == "AuraContainer")
        assert container.slots.aura.button.width == 28


@pytest.mark.parametrize("name", ["aura_player_buff_duration", "aura_player_buff_stacks"])
@pytest.mark.parametrize("player_only", [None, True, False])
def test_player_aura_source_filter(name: str, player_only: bool | None) -> None:
    args = CASES[name].copy()
    if player_only is not None:
        args["player_only"] = player_only
    plugin = create(name, args)
    _, state, _ = harness([plugin])
    state.initialize(state)
    container = next(frame for frame in state.frames.values() if frame.kind == "AuraContainer")
    assert plugin.config_defaults["player_only"] is True
    assert container.slots.aura.filter == ("HELPFUL" if player_only is False else "HELPFUL|PLAYER")
    assert dict(container.slots.aura.options.candidateFilters.includeSpellIDs.items()) == {100: True, 200: True}


@pytest.mark.parametrize("name", ["aura_player_buff_duration", "aura_player_buff_stacks"])
@pytest.mark.parametrize("bad", [None, 0, 1, "true", [], {}])
def test_player_aura_source_filter_requires_boolean(name: str, bad: object) -> None:
    with pytest.raises(ValueError, match="player_only"):
        create(name, {**CASES[name], "player_only": bad})


def test_player_fractional_duration_keeps_official_bar_binding() -> None:
    plugin = create("aura_player_buff_duration", {"aura_ids": [132403], "duration": 13.5})
    _, state, _ = harness([plugin])
    state.initialize(state)
    container = next(frame for frame in state.frames.values() if frame.kind == "AuraContainer")
    assert plugin.output.widths == (4,)
    assert container.slots.aura.button.width == 16
    assert dict(container.slots.aura.button.durationOptions.items()) == {"interpolation": 0, "direction": 1}


@pytest.mark.parametrize("name", [name for name in CASES if name.endswith("duration")])
@pytest.mark.parametrize("duration,width,expected_width", [(12, None, 3), (40, None, 8), (40, 1, 1), (40, 12, 12)])
def test_duration_lua_uses_independent_width(name: str, duration: int, width: int | None, expected_width: int) -> None:
    args: dict[str, object] = {**CASES[name], "duration": duration}
    if width is not None:
        args["width"] = width
    plugin = create(name, args)
    assert plugin.output.widths == (expected_width,)
    _, state, addon = harness([plugin])
    state.initialize(state)
    container = next(frame for frame in state.frames.values() if frame.kind == "AuraContainer")
    assert container.slots.aura.button.width == expected_width * 4
    assert addon.ValueBarLength == expected_width + 1


def test_combined_generation_and_frozen_layout(tmp_path: Path) -> None:
    entries = tuple(ConditionEntry(name, f"{name}@dev", create(name)) for name in CASES)
    width = allocate([entry.instance for entry in entries])
    rotation_path = tmp_path / "rotation.toml"
    rotation_path.write_bytes((ROOT / "tests/fixtures/engine-rotation.toml").read_bytes())
    rotation = replace(load_rotation(rotation_path), conditions=entries, macros=(), board_width=width)
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    compile_lua: Any = lua.eval("function(source) assert(loadstring(source)); return true end")
    for filename, source in render(rotation, "PhantomTest").items():
        if filename.endswith(".lua"):
            assert compile_lua(source), filename
            assert "{{" not in source
    bars = [entry.instance for entry in entries if entry.instance.output.output_type == "value_bar"]
    assert [plugin.regions[0].x for plugin in bars] == [1, 5, 9, 12]
    assert [plugin.output.widths for plugin in bars] == [(3,), (3,), (2,), (2,)]
