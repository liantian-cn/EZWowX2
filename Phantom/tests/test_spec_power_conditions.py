"""固定资源插件的参数、真实 Cell 编解码、事件及秘密值边界离线验证。"""

from pathlib import Path
from typing import Any

import numpy as np
import pytest
from lupa.lua51 import LuaError, LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Value
from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.pixels import Cell, PixelDecoder

ROOT = Path(__file__).resolve().parents[1]
PRIMARY: dict[str, tuple[str, int]] = {
    "mana": ("Mana", 0),
    "rage": ("Rage", 1),
    "focus": ("Focus", 2),
    "energy": ("Energy", 3),
    "runic_power": ("RunicPower", 6),
    "lunar_power": ("LunarPower", 8),
    "maelstrom": ("Maelstrom", 11),
    "insanity": ("Insanity", 13),
    "fury": ("Fury", 17),
    "pain": ("Pain", 18),
}
SECONDARY: dict[str, tuple[str, int]] = {"combo_points": ("ComboPoints", 4), "soul_shards": ("SoulShards", 7), "holy_power": ("HolyPower", 9), "chi": ("Chi", 12), "essence": ("Essence", 19), "arcane_charges": ("ArcaneCharges", 16)}
RESOURCES = PRIMARY | SECONDARY
EVENTS = ("PLAYER_ENTERING_WORLD", "UNIT_POWER_UPDATE", "UNIT_MAXPOWER", "UNIT_DISPLAYPOWER")

# 仅在本测试运行时扩展既有替身，不修改共享 harness。
POWER_APIS = """
local state = ...
state.powerValues = {}
state.powerRatios = {}
state.powerCalls = {}
state.percentCalls = {}
UnitPowerType = function() error("不得查询当前首要资源类型") end
UnitPower = function(unit, powerType, unmodified)
    assert(unit == "player" and unmodified == false)
    state.powerCalls[powerType] = (state.powerCalls[powerType] or 0) + 1
    return state.powerValues[powerType]
end
UnitPowerPercent = function(unit, powerType, unmodified, curve)
    assert(unit == "player" and unmodified == false)
    assert(#curve.points == 2)
    assert(curve.points[1][1] == 0 and curve.points[1][2].value == 0)
    assert(curve.points[2][1] == 1 and curve.points[2][2].value == 1)
    state.percentCalls[powerType] = (state.percentCalls[powerType] or 0) + 1
    local ratio = assert(state.powerRatios[powerType])
    -- 模拟受支持的颜色消费者：只允许 GetRGBA 将不透明通道传给真实 Cell。
    return setmetatable({GetRGBA = function()
        local channel = state.secretPower and state:secret(ratio) or ratio
        return channel, channel, channel, 1
    end}, {__index = function() error("不得检查曲线结果") end})
end
"""


def create(name: str, args: dict[str, object] | None = None) -> Condition:
    if args is None:
        args = {"max_power": 120.5} if name in PRIMARY else {}
    return Registry().create(f"spec_power_{name}@dev", args)


def harness(plugins: list[Condition], *, initialize: bool = True) -> tuple[Any, Any]:
    allocate(plugins)
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state: Any
    addon: Any
    state, addon = lua.execute((ROOT / "tests/lua/player_conditions_harness.lua").read_text(encoding="utf-8"))
    lua.execute(POWER_APIS, state)
    lua.globals().Enum.PowerType = lua.table_from({enum: number for enum, number in RESOURCES.values()})
    for _, number in RESOURCES.values():
        state.powerValues[number] = 3
        state.powerRatios[number] = 1 / 3
    execute: Any = lua.eval("function(source, addon) assert(loadstring(source))('PhantomTest', addon) end")
    execute((ROOT / "phantom/lua/runtime/07_cell_backplate.lua").read_text(encoding="utf-8"), addon)
    execute((ROOT / "phantom/lua/runtime/08_cell.lua").read_text(encoding="utf-8"), addon)
    for index, plugin in enumerate(plugins):
        execute(plugin.generate_lua(f"power-{index}"), addon)
    if initialize:
        state.initialize(state)
    return lua, state


def value(plugin: Condition, state: Any, x: int = 1) -> Value:
    image = np.zeros((20, 128, 3), dtype=np.uint8)
    image[4:8, 4 * x : 4 * x + 4] = int(state.brightness(state, x) + 0.5)
    decoder = PixelDecoder(image)
    cells, bars, icons = plugin.raw_value(decoder)
    return plugin.value(cells, bars, icons, decoder=decoder)


@pytest.mark.parametrize("name", PRIMARY)
@pytest.mark.parametrize("bad", [None, True, False, 0, -1, float("inf"), float("nan"), "120", [], {}])
def test_primary_requires_finite_positive_maximum(name: str, bad: object) -> None:
    with pytest.raises(ValueError):
        create(name, {"max_power": bad})


@pytest.mark.parametrize("name", PRIMARY)
def test_primary_missing_and_unknown_arguments(name: str) -> None:
    cases: list[dict[str, object]] = [{}, {"maxValue": 120}, {"max_power": 120, "power_type": 6}]
    for args in cases:
        with pytest.raises(ValueError):
            create(name, args)


@pytest.mark.parametrize("name", SECONDARY)
@pytest.mark.parametrize("args", [{"max_power": 5}, {"maxValue": 5}, {"power_type": 7}])
def test_secondary_has_no_parameters(name: str, args: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        create(name, args)


@pytest.mark.parametrize("name", PRIMARY)
@pytest.mark.parametrize("secret", [False, True])
@pytest.mark.parametrize("ratio", [0.0, 1 / 255, 1 / 3, 0.5, 254 / 255, 1.0])
def test_primary_curve_roundtrip(name: str, secret: bool, ratio: float) -> None:
    plugin = create(name)
    _, state = harness([plugin], initialize=False)
    number = PRIMARY[name][1]
    state.powerRatios[number] = ratio
    state.secretPower = secret
    state.initialize(state)
    actual = value(plugin, state)
    assert type(actual) is float
    assert actual == pytest.approx(int(ratio * 255 + 0.5) / 255 * 120.5)
    assert state.percentCalls[number] == 1
    assert list(state.powerCalls.items()) == []


@pytest.mark.parametrize("name", SECONDARY)
@pytest.mark.parametrize("power", [0, 1, 3, 5, 6, 127, 254, 255])
def test_secondary_integer_roundtrip(name: str, power: int) -> None:
    plugin = create(name)
    _, state = harness([plugin], initialize=False)
    number = SECONDARY[name][1]
    state.powerValues[number] = power
    state.initialize(state)
    actual = value(plugin, state)
    assert type(actual) is int
    assert actual == power
    assert state.powerCalls[number] == 1
    assert list(state.percentCalls.items()) == []


@pytest.mark.parametrize("name", SECONDARY)
@pytest.mark.parametrize("bad", [-1, 256, 0.5, float("inf"), float("nan"), None, True, "3"])
def test_secondary_invalid_values_are_hard_lua_errors(name: str, bad: object) -> None:
    plugin = create(name)
    _, state = harness([plugin])
    state.powerValues[SECONDARY[name][1]] = bad
    state.event(state, "UNIT_POWER_UPDATE", "player")
    with pytest.raises(LuaError, match=r"0\.\.255"):
        state.flushTimers(state)
    # 硬错误不伪装成有效的零资源。
    assert value(plugin, state) == 3


@pytest.mark.parametrize("name", SECONDARY)
@pytest.mark.parametrize("initialize", [False, True])
def test_secondary_secret_checked_before_type_range_and_arithmetic(name: str, initialize: bool) -> None:
    plugin = create(name)
    _, state = harness([plugin], initialize=initialize)
    state.powerValues[SECONDARY[name][1]] = state.secret(state, 999)
    with pytest.raises(LuaError, match="次要资源返回秘密值"):
        if initialize:
            state.event(state, "UNIT_POWER_UPDATE", "player")
            state.flushTimers(state)
        else:
            state.initialize(state)


@pytest.mark.parametrize("name", RESOURCES)
@pytest.mark.parametrize("event", EVENTS)
def test_event_lifecycle_player_filter_and_deferred_refresh(name: str, event: str) -> None:
    plugin = create(name)
    _, state = harness([plugin], initialize=False)
    number = RESOURCES[name][1]
    calls = state.percentCalls if name in PRIMARY else state.powerCalls
    state.event(state, event, "player", state.secret(state, "资源事件参数"))
    state.flushTimers(state)
    assert calls[number] is None
    state.initialize(state)
    assert calls[number] == 1
    if event.startswith("UNIT_"):
        state.event(state, event, "target")
        state.flushTimers(state)
        assert calls[number] == 1
    if name in PRIMARY:
        state.powerRatios[number] = 1
    else:
        state.powerValues[number] = 5
    old = value(plugin, state)
    state.event(state, event, "player", state.secret(state, "资源事件参数"))
    assert calls[number] == 1
    assert value(plugin, state) == old
    state.flushTimers(state)
    assert calls[number] == 2
    assert value(plugin, state) == (120.5 if name in PRIMARY else 5)
    state.tick(state, 10)
    assert calls[number] == 2


@pytest.mark.parametrize("name", RESOURCES)
@pytest.mark.parametrize("damage", ["mixed", "colored", "missing"])
def test_invalid_pixels_and_missing_region_fall_back(name: str, damage: str) -> None:
    plugin = create(name)
    decoder = PixelDecoder(np.zeros((20, 128, 3), dtype=np.uint8))
    image = np.full((4, 4, 3), 100, dtype=np.uint8)
    if damage == "mixed":
        image[1, 1] = 0
    elif damage == "colored":
        image[:] = [100, 0, 100]
    cells = [] if damage == "missing" else [Cell(1, 2, image)]
    with pytest.raises((ValueError, IndexError)):
        plugin.decode_value(cells, [], [], decoder=decoder)
    result = plugin.value(cells, [], [], decoder=decoder)
    assert result == 0
    assert type(result) is (float if name in PRIMARY else int)


def test_all_resources_generate_and_render_independent_cells() -> None:
    plugins = [create(name) for name in RESOURCES]
    _, state = harness(plugins)
    for x, (name, plugin) in enumerate(zip(RESOURCES, plugins, strict=True), start=1):
        assert len(plugin.regions) == 1
        assert plugin.output.value_shape == "scalar"
        assert value(plugin, state, x) == (120.5 / 3 if name in PRIMARY else 3)
    assert len(list(state.percentCalls.items())) == 10
    assert len(list(state.powerCalls.items())) == 6
