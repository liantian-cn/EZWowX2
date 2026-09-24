"""单位关系、宠物与可观察减益计数的离线配对验证；不替代游戏验收。"""

from typing import Any

import numpy as np
import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.base import Condition
from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.pixels import Cell, PixelDecoder
from tests.test_player_conditions import ROOT, decode, emit, value

BOOL_NAMES = ("target_is_enemy", "focus_is_enemy", "target_can_assist", "focus_can_assist", "player_has_pet")
COUNT = "player_range_aura_units_count"


def setup(plugin: Condition) -> tuple[Any, Any]:
    """复用真实 Cell 和共享替身，只在本文件补充当前插件需要的 API。"""
    allocate([plugin])
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state, addon = lua.execute((ROOT / "tests/lua/player_conditions_harness.lua").read_text(encoding="utf-8"))
    lua.execute(
        """
        local state = ...
        UnitIsEnemy = function(player, unit)
            assert(player == "player"); state:query("enemy")
            return state.units[unit].enemy
        end
        UnitCanAssist = function(player, unit, ...)
            assert(player == "player" and select("#", ...) == 0)
            state:query("assist"); return state.units[unit].assist
        end
        Enum.SecrecyLevel = {NeverSecret = 0}
        C_Secrets = {GetSpellAuraSecrecy = function(id)
            assert(id == 200); return state.auraSecrecy or 0
        end}
        C_UnitAuras = {GetUnitAuraBySpellID = function(unit, id)
            assert(id == 200); state:query("aura"); return state.auras[unit]
        end}
        """,
        state,
    )
    execute: Any = lua.eval("function(source, addon) assert(loadstring(source))('PhantomTest', addon) end")
    execute((ROOT / "phantom/lua/runtime/07_cell_backplate.lua").read_text(encoding="utf-8"), addon)
    execute((ROOT / "phantom/lua/runtime/08_cell.lua").read_text(encoding="utf-8"), addon)
    execute(plugin.generate_lua("unit-state-test"), addon)
    return lua, state


@pytest.mark.parametrize("name", BOOL_NAMES)
def test_boolean_events_and_missing_units(name: str) -> None:
    plugin = Registry().create(f"{name}@dev", {})
    lua, state = setup(plugin)
    emit(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)
    state.initialize(state)
    assert value(plugin, state) is False
    unit = "pet" if name == "player_has_pet" else name.split("_")[0]
    field = "enemy" if "enemy" in name else "assist"
    state.units[unit] = lua.table_from({field: True})
    event = {"pet": "UNIT_PET", "target": "PLAYER_TARGET_CHANGED", "focus": "PLAYER_FOCUS_CHANGED"}[unit]
    emit(state, event, "player" if unit == "pet" else None)
    assert value(plugin, state) is False
    state.flushTimers(state)
    assert value(plugin, state) is True
    assert all(frame.OnUpdate is None for frame in state.frames.values())
    if unit == "pet":
        state.units.pet.dead = True
        emit(state, "UNIT_HEALTH", "target")
        state.flushTimers(state)
        assert value(plugin, state) is True
        emit(state, "UNIT_HEALTH", "pet")
        state.flushTimers(state)
        assert value(plugin, state) is False
        state.units.pet.dead = False
        emit(state, "UNIT_FLAGS", "pet")
        state.flushTimers(state)
        assert value(plugin, state) is True
    else:
        for result in (False, True):
            state.units[unit][field] = state.secret(state, result)
            emit(state, "UNIT_FACTION", unit)
            state.flushTimers(state)
            assert value(plugin, state) is result
    state.units[unit] = None
    emit(state, event, "player" if unit == "pet" else None)
    state.flushTimers(state)
    assert value(plugin, state) is False


@pytest.mark.parametrize("name", BOOL_NAMES)
def test_boolean_validation_and_pixels(name: str) -> None:
    with pytest.raises(ValueError):
        Registry().create(f"{name}@dev", {"extra": True})
    plugin = Registry().create(f"{name}@dev", {})
    assert decode(plugin, 0) is False
    assert decode(plugin, 255) is True
    assert decode(plugin, 127) is False
    decoder = PixelDecoder(np.zeros((20, 128, 3), dtype=np.uint8))
    pixels = np.full((4, 4, 3), 255, dtype=np.uint8)
    pixels[1, 1] = [255, 0, 0]
    with pytest.raises(ValueError):
        plugin.decode_value([Cell(1, 2, pixels)], [], [], decoder=decoder)
    assert plugin.value([Cell(1, 2, pixels)], [], [], decoder=decoder) is False


@pytest.mark.parametrize("combat_only", [False, True])
def test_count_filter_chain_and_polling(combat_only: bool) -> None:
    plugin = Registry().create(f"{COUNT}@dev", {"spell_id": 100, "aura_id": 200, "combat_only": combat_only})
    lua, state = setup(plugin)
    state.tick(state, 2)
    state.initialize(state)
    assert value(plugin, state) == 0
    for index in range(1, 42):
        unit = f"nameplate{index}"
        state.units[unit] = lua.table_from({"attackable": True, "combat": True})
        state.ranges[unit] = True
        state.auras[unit] = lua.table_from({"isHarmful": True})
    state.units.nameplate1 = None
    state.units.nameplate2.attackable = False
    state.units.nameplate3.dead = True
    state.units.nameplate4.combat = False
    state.ranges.nameplate5 = None
    state.ranges.nameplate6 = False
    state.ranges.nameplate7 = state.secret(state, True)
    state.auras.nameplate8 = None
    state.auras.nameplate9.isHarmful = False
    state.auras.nameplate10 = state.secret(state, True)
    state.auras.nameplate11.isHarmful = state.secret(state, True)
    emit(state, "UNIT_AURA", "nameplate12")
    assert value(plugin, state) == 0
    state.flushTimers(state)
    assert value(plugin, state) == (29 if combat_only else 30)
    previous = state.queries["range"]
    state.invalidSpells[100] = True
    state.tick(state, 1.1)
    assert value(plugin, state) == 0
    assert state.queries["range"] == previous
    state.invalidSpells[100] = None
    state.units = lua.table()
    emit(state, "NAME_PLATE_UNIT_REMOVED", "nameplate12")
    state.flushTimers(state)
    assert value(plugin, state) == 0


def test_count_neversecret_hard_error_and_stagger() -> None:
    plugin = Registry().create(f"{COUNT}@dev", {"spell_id": 100, "aura_id": 200})
    _, state = setup(plugin)
    state.auraSecrecy = 1
    with pytest.raises(Exception, match="aura_id 必须为 NeverSecret"):
        state.initialize(state)
    assert len(state.cells) == 0
    plugin = Registry().create(f"{COUNT}@dev", {"spell_id": 100, "aura_id": 200})
    lua, state = setup(plugin)
    state.initialize(state)
    state.units.nameplate1 = lua.table_from({"attackable": True})
    state.ranges.nameplate1 = True
    state.auras.nameplate1 = lua.table_from({"isHarmful": True})
    state.tick(state, 1)
    assert state.queries["range"] is None
    state.tick(state, 0.02)
    assert state.queries["range"] == 1
    state.tick(state, 10)
    assert state.queries["range"] == 2
    state.tick(state, 0)
    assert state.queries["range"] == 3


@pytest.mark.parametrize("field", ["spell_id", "aura_id"])
@pytest.mark.parametrize("bad", [None, False, True, 0, -1, 1.5, "100", [], {}])
def test_count_rejects_invalid_ids(field: str, bad: object) -> None:
    args: dict[str, object] = {"spell_id": 100, "aura_id": 200, field: bad}
    with pytest.raises(ValueError):
        Registry().create(f"{COUNT}@dev", args)


@pytest.mark.parametrize("bad", [None, 0, 1, "true", [], {}])
def test_count_rejects_invalid_combat_option(bad: object) -> None:
    with pytest.raises(ValueError):
        Registry().create(f"{COUNT}@dev", {"spell_id": 100, "aura_id": 200, "combat_only": bad})


def test_count_parameters_and_complete_pixel_range() -> None:
    invalid_args: tuple[dict[str, object], ...] = ({}, {"spell_id": 100}, {"aura_id": 200}, {"spell_id": 100, "aura_id": 200, "extra": 1})
    for args in invalid_args:
        with pytest.raises(ValueError):
            Registry().create(f"{COUNT}@dev", args)
    plugin = Registry().create(f"{COUNT}@dev", {"spell_id": 100, "aura_id": 200})
    assert plugin.template_parameters() == {"spell_id": "100", "aura_id": "200", "combat_only": "false"}
    for count in range(41):
        assert decode(plugin, count / 40 * 255) == count
    decoder = PixelDecoder(np.zeros((20, 128, 3), dtype=np.uint8))
    pixels = np.full((4, 4, 3), 255, dtype=np.uint8)
    pixels[1, 1] = [255, 0, 0]
    with pytest.raises(ValueError):
        plugin.decode_value([Cell(1, 2, pixels)], [], [], decoder=decoder)
    assert plugin.value([Cell(1, 2, pixels)], [], [], decoder=decoder) == 0
