from pathlib import Path
from typing import Any

import numpy as np
import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.base import Condition
from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.pixels import Cell, PixelDecoder

ROOT = Path(__file__).resolve().parents[1]

# 库存与冷却专用替身；所有查询参数均校验，禁止调用可用性 API。
EXTENSION = """
local state = ...
state.now = 100
state.itemData = {}
GetTime = function() return state.now end
C_Item.GetItemCount = function(id, bank, uses, reagentBank, accountBank)
    assert(bank == false and uses == false and reagentBank == false and accountBank == false)
    state:query('count')
    if state.failCount then error('库存查询失败') end
    return (state.itemData[id] or {}).count
end
C_Item.GetItemCooldown = function(id)
    state:query('cooldown')
    if state.failCooldown then error('冷却查询失败') end
    local data = state.itemData[id] or {}
    return data.start, data.duration, data.enabled
end
C_Item.IsUsableItem = function() error('本插件不得查询 usable') end
-- 本组仅验证普通 API 返回；普通布尔显示不依赖秘密诊断函数。
C_CurveUtil.EvaluateColorFromBoolean = function(value, yes, no)
    assert(type(value) == 'boolean')
    return value and yes or no
end
issecretvalue = nil
"""


def harness(item_ids: tuple[int, ...] = (241308,), *, initialize: bool = True) -> tuple[list[Condition], Any, Any]:
    plugins = [Registry().create("item_cooldown_ready@dev", {"item_id": item_id}) for item_id in item_ids]
    allocate(plugins)
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state, addon = lua.execute((ROOT / "tests/lua/player_conditions_harness.lua").read_text(encoding="utf-8"))
    lua.execute(EXTENSION, state)
    execute: Any = lua.eval("function(source, addon) assert(loadstring(source))('PhantomTest', addon) end")
    execute((ROOT / "phantom/lua/runtime/07_cell_backplate.lua").read_text(encoding="utf-8"), addon)
    execute((ROOT / "phantom/lua/runtime/08_cell.lua").read_text(encoding="utf-8"), addon)
    for index, plugin in enumerate(plugins):
        execute(plugin.generate_lua(f"item-{index}"), addon)
    if initialize:
        state.initialize(state)
    return plugins, lua, state


def set_item(lua: Any, state: Any, item_id: int = 241308, **overrides: object) -> None:
    data: dict[str, object] = {"count": 1, "start": 0, "duration": 0, "enabled": True}
    data.update(overrides)
    state.itemData[item_id] = lua.table_from(data)


def value(plugin: Condition, state: Any) -> bool:
    region = plugin.regions[0]
    image = np.zeros((20, 256, 3), dtype=np.uint8)
    image[4:8, region.x * 4 : region.x * 4 + 4] = int(state.brightness(state, region.x))
    decoder = PixelDecoder(image)
    result = plugin.value(*plugin.raw_value(decoder), decoder=decoder)
    assert type(result) is bool
    return result


def refresh(state: Any, event: str = "BAG_UPDATE_COOLDOWN") -> None:
    state.event(state, event)
    state.flushTimers(state)


@pytest.mark.parametrize("args", [{}, {"item_id": 241308, "usable": False}, {"item_ids": [241308]}])
def test_item_fields(args: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        Registry().create("item_cooldown_ready@dev", args)


@pytest.mark.parametrize("bad", [True, False, 0, -1, 1.0, 1.5, "241308", None, [], {}, float("inf"), float("nan")])
def test_item_id_requires_positive_integer(bad: object) -> None:
    with pytest.raises(ValueError, match="item_id"):
        Registry().create("item_cooldown_ready@dev", {"item_id": bad})


@pytest.mark.parametrize("item_id", [241308, 241309, 123])
@pytest.mark.parametrize(
    "count,start,duration,enabled,expected", [(1, 0, 0, True, True), (0, 0, 0, True, False), (2, 95, 10, True, False), (1, 95, 5, True, True), (1, 90, 5, True, True), (1, 95, 5.001, True, False), (1, 0, 0, False, False)]
)
def test_inventory_and_remaining_cooldown(item_id: int, count: int, start: float, duration: float, enabled: bool, expected: bool) -> None:
    plugins, lua, state = harness((item_id,))
    set_item(lua, state, item_id, count=count, start=start, duration=duration, enabled=enabled)
    refresh(state)
    assert value(plugins[0], state) is expected


@pytest.mark.parametrize("field", ["count", "start", "duration", "enabled", "now"])
@pytest.mark.parametrize("bad", [None, "0", -1, float("inf"), float("-inf"), float("nan")])
def test_invalid_api_data_clears_previous_ready(field: str, bad: object) -> None:
    plugins, lua, state = harness()
    set_item(lua, state)
    refresh(state)
    assert value(plugins[0], state) is True
    if field == "now":
        state.now = bad
    else:
        state.itemData[241308][field] = bad
    refresh(state)
    assert value(plugins[0], state) is False


@pytest.mark.parametrize("enabled", [0, 1])
def test_enabled_does_not_accept_legacy_numeric_flag(enabled: int) -> None:
    plugins, lua, state = harness()
    set_item(lua, state, enabled=enabled)
    refresh(state)
    assert value(plugins[0], state) is False


@pytest.mark.parametrize("field", ["count", "start", "duration", "now"])
@pytest.mark.parametrize("bad", [True, False])
def test_numeric_api_fields_reject_boolean(field: str, bad: bool) -> None:
    plugins, lua, state = harness()
    set_item(lua, state)
    if field == "now":
        state.now = bad
    else:
        state.itemData[241308][field] = bad
    refresh(state)
    assert value(plugins[0], state) is False


def test_ordinary_api_path_needs_no_secrecy_diagnostics() -> None:
    plugins, lua, state = harness()
    set_item(lua, state)
    assert lua.eval("issecretvalue == nil")
    refresh(state)
    assert value(plugins[0], state) is True


@pytest.mark.parametrize("failure", ["failCount", "failCooldown"])
def test_api_exception_returns_false_and_recovers(failure: str) -> None:
    plugins, lua, state = harness()
    set_item(lua, state)
    refresh(state)
    assert value(plugins[0], state) is True
    state[failure] = True
    refresh(state)
    assert value(plugins[0], state) is False
    state[failure] = False
    refresh(state)
    assert value(plugins[0], state) is True


def test_item_instances_do_not_merge_macro_candidates() -> None:
    plugins, lua, state = harness((241308, 241309))
    set_item(lua, state, 241308, count=0)
    set_item(lua, state, 241309)
    refresh(state)
    assert value(plugins[0], state) is False
    assert value(plugins[1], state) is True


@pytest.mark.parametrize("event", ["PLAYER_ENTERING_WORLD", "BAG_UPDATE", "BAG_UPDATE_COOLDOWN", "SPELL_UPDATE_COOLDOWN"])
def test_events_defer_until_next_frame(event: str) -> None:
    plugins, lua, state = harness(initialize=False)
    state.event(state, event)
    state.flushTimers(state)
    set_item(lua, state)
    state.initialize(state)
    assert value(plugins[0], state) is True
    state.itemData[241308].count = 0
    state.event(state, event)
    assert value(plugins[0], state) is True
    state.flushTimers(state)
    assert value(plugins[0], state) is False


def test_polling_stagger_and_elapsed_cooldown() -> None:
    plugins, lua, state = harness((241308, 241309))
    for item_id in (241308, 241309):
        set_item(lua, state, item_id, start=95, duration=10)
    refresh(state)
    assert all(value(plugin, state) is False for plugin in plugins)
    state.now = 105
    state.tick(state, 1.015)
    assert value(plugins[0], state) is True
    assert value(plugins[1], state) is False
    state.tick(state, 0.01)
    assert value(plugins[1], state) is True
    state.queries.count = 0
    state.tick(state, 10)
    assert state.queries.count == 2


@pytest.mark.parametrize("damage", ["gray", "colored", "mixed", "missing"])
def test_pixel_decode_failure_is_false(damage: str) -> None:
    plugin = Registry().create("item_cooldown_ready@dev", {"item_id": 241308})
    image = np.full((4, 4, 3), 255, dtype=np.uint8)
    if damage == "gray":
        image[:] = 127
    elif damage == "colored":
        image[:] = [255, 0, 0]
    elif damage == "mixed":
        image[1, 1] = 0
    decoder = PixelDecoder(np.zeros((20, 256, 3), dtype=np.uint8))
    cells = [] if damage == "missing" else [Cell(1, 2, image)]
    assert plugin.value(cells, [], [], decoder=decoder) is False
