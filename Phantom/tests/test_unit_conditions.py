"""迁移条件的参数、真实 Cell 解码与 Lua API 替身测试；不替代游戏内验收。"""

from typing import Any

import numpy as np
import pytest

from phantom.core.condition.registry import Registry
from phantom.core.pixels import Cell, PixelDecoder
from tests.test_player_conditions import emit, harness, value

HEALTH = ("player_health_pct", "target_health_pct", "focus_health_pct")
RANGE_CASES = (("target_in_range", "target"), ("focus_in_range", "focus"), ("spell_in_range", "target"), ("spell_in_range", "focus"), ("spell_in_range", "mouseover"))


def range_args(name: str, unit: str) -> dict[str, object]:
    args: dict[str, object] = {"spell_id": 100}
    if name == "spell_in_range":
        args["unit_token"] = unit
    return args


@pytest.mark.parametrize("name", HEALTH)
@pytest.mark.parametrize("predicted", [True, False])
def test_health_predicted_events_and_missing_unit(name: str, predicted: bool) -> None:
    unit = name.split("_")[0]
    plugin = Registry().create(f"{name}@dev", {"use_predicted": predicted})
    lua, state, _ = harness([plugin], initialize=False)
    emit(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)
    state.units[unit] = lua.table_from({"health": state.secret(state, 0.2), "predictedHealth": state.secret(state, 0.8)})
    state.initialize(state)
    assert value(plugin, state) == pytest.approx(80.0 if predicted else 20.0)
    assert state.lastHealthPredicted is predicted
    assert state.lastHealthUnit == unit
    frames = [frame for frame in state.frames.values() if frame.events["UNIT_HEALTH"]]
    assert len(frames) == 1
    frame = frames[0]
    assert frame.events["UNIT_HEALTH"] == unit
    assert frame.events["UNIT_MAXHEALTH"] == unit
    assert frame.OnUpdate is None
    for event in ("UNIT_HEAL_PREDICTION", "UNIT_ABSORB_AMOUNT_CHANGED", "UNIT_HEAL_ABSORB_AMOUNT_CHANGED"):
        assert frame.events[event] == (unit if predicted else None)
    state.units[unit].health = 1.0
    state.units[unit].predictedHealth = 1.0
    emit(state, "UNIT_HEALTH", "pet")
    state.flushTimers(state)
    assert value(plugin, state) != 100.0
    emit(state, "UNIT_HEALTH", unit)
    assert value(plugin, state) != 100.0
    state.flushTimers(state)
    assert value(plugin, state) == 100.0
    state.units[unit] = None
    event = {"player": "PLAYER_ENTERING_WORLD", "target": "PLAYER_TARGET_CHANGED", "focus": "PLAYER_FOCUS_CHANGED"}[unit]
    emit(state, event)
    state.flushTimers(state)
    assert value(plugin, state) == 0.0


@pytest.mark.parametrize("name", HEALTH)
@pytest.mark.parametrize("bad", [None, 0, 1, "true", [], {}])
def test_health_rejects_non_boolean(name: str, bad: object) -> None:
    with pytest.raises(ValueError):
        Registry().create(f"{name}@dev", {"use_predicted": bad})


@pytest.mark.parametrize("name", HEALTH)
def test_health_default_and_pixel_damage(name: str) -> None:
    plugin = Registry().create(f"{name}@dev", {})
    assert plugin.template_parameters() == {"use_predicted": "true"}
    decoder = PixelDecoder(np.zeros((20, 128, 3), dtype=np.uint8))
    for brightness in (0, 51, 128, 255):
        image = np.full((4, 4, 3), brightness, dtype=np.uint8)
        assert plugin.decode_value([Cell(1, 2, image)], [], [], decoder=decoder) == pytest.approx(brightness / 255 * 100)
    image[1, 1] = [255, 0, 0]
    with pytest.raises(ValueError):
        plugin.decode_value([Cell(1, 2, image)], [], [], decoder=decoder)
    assert plugin.value([Cell(1, 2, image)], [], [], decoder=decoder) == 0.0


@pytest.mark.parametrize("name,unit", RANGE_CASES)
def test_range_polling_secret_results_and_fallbacks(name: str, unit: str) -> None:
    plugin = Registry().create(f"{name}@dev", range_args(name, unit))
    lua, state, _ = harness([plugin], initialize=False)
    state.tick(state, 0.3)
    state.initialize(state)
    assert value(plugin, state) is False
    state.units[unit] = lua.table_from({"name": unit})
    state.ranges[unit] = True
    state.tick(state, 0.11)
    assert value(plugin, state) is True
    assert state.lastRangeSpell == 100
    for result in (False, True, None, state.secret(state, False), state.secret(state, True)):
        state.ranges[unit] = result
        state.tick(state, 0.11)
        expected = result is True
        if not isinstance(result, (bool, type(None))):
            reveal: Any = lua.eval("function(v) return C_CurveUtil.EvaluateColorFromBoolean(v, CreateColor(1), CreateColor(0)).value == 1 end")
            expected = bool(reveal(result))
        assert value(plugin, state) is expected
    previous = state.queries["range"]
    state.invalidSpells[100] = True
    state.tick(state, 0.11)
    assert value(plugin, state) is False
    assert state.queries["range"] == previous
    state.invalidSpells[100] = None
    state.units[unit] = None
    state.tick(state, 0.11)
    assert value(plugin, state) is False
    assert state.queries["range"] == previous
    assert all(frame.events["PLAYER_TARGET_CHANGED"] is None for frame in state.frames.values())
    assert all(frame.events["PLAYER_FOCUS_CHANGED"] is None for frame in state.frames.values())


@pytest.mark.parametrize("name,unit", RANGE_CASES)
def test_range_stagger_and_once_per_frame(name: str, unit: str) -> None:
    plugin = Registry().create(f"{name}@dev", range_args(name, unit))
    lua, state, _ = harness([plugin])
    state.units[unit] = lua.table_from({"name": unit})
    state.ranges[unit] = True
    state.tick(state, 0.1)
    assert state.queries["range"] is None
    state.tick(state, 0.02)
    assert state.queries["range"] == 1
    state.tick(state, 10)
    assert state.queries["range"] == 2
    state.tick(state, 0)
    assert state.queries["range"] == 3


@pytest.mark.parametrize("name,unit", RANGE_CASES)
@pytest.mark.parametrize("bad", [None, False, True, 0, -1, 1.5, "100", [], {}])
def test_range_invalid_spell_id(name: str, unit: str, bad: object) -> None:
    args = range_args(name, unit)
    args["spell_id"] = bad
    with pytest.raises(ValueError):
        Registry().create(f"{name}@dev", args)


@pytest.mark.parametrize("bad", [None, "player", "pet", "nameplate1", "TARGET", "", "target\";error('injected')", 1, []])
def test_range_unit_whitelist(bad: object) -> None:
    with pytest.raises(ValueError):
        Registry().create("spell_in_range@dev", {"spell_id": 100, "unit_token": bad})


@pytest.mark.parametrize("name,unit", RANGE_CASES)
def test_range_parameter_shape_and_pixel_validation(name: str, unit: str) -> None:
    args = range_args(name, unit)
    for incomplete in ({}, {**args, "extra": True}):
        with pytest.raises(ValueError):
            Registry().create(f"{name}@dev", incomplete)
    plugin = Registry().create(f"{name}@dev", args)
    decoder = PixelDecoder(np.zeros((20, 128, 3), dtype=np.uint8))
    for brightness, expected in ((0, False), (255, True)):
        image = np.full((4, 4, 3), brightness, dtype=np.uint8)
        assert plugin.decode_value([Cell(1, 2, image)], [], [], decoder=decoder) is expected
    for pixel in (127, [255, 0, 0]):
        image[:] = pixel
        with pytest.raises(ValueError):
            plugin.decode_value([Cell(1, 2, image)], [], [], decoder=decoder)
        assert plugin.value([Cell(1, 2, image)], [], [], decoder=decoder) is False


@pytest.mark.parametrize("combat_only", [True, False])
def test_melee_full_filter_chain(combat_only: bool) -> None:
    plugin = Registry().create("player_melee_enemies_count@dev", {"spell_id": 100, "combat_only": combat_only})
    lua, state, _ = harness([plugin])
    for index in range(1, 42):
        state.units[f"nameplate{index}"] = lua.table_from({"attackable": True, "combat": True})
        state.ranges[f"nameplate{index}"] = True
    state.units.nameplate1 = None
    state.units.nameplate2.attackable = False
    state.units.nameplate3.dead = True
    state.units.nameplate4.combat = False
    state.ranges.nameplate5 = False
    state.ranges.nameplate6 = None
    state.ranges.nameplate7 = state.secret(state, True)
    emit(state, "NAME_PLATE_UNIT_ADDED", "nameplate40")
    assert value(plugin, state) == 0
    state.flushTimers(state)
    assert value(plugin, state) == (33 if combat_only else 34)
    previous = state.queries["range"]
    state.invalidSpells[100] = True
    state.tick(state, 1.1)
    assert value(plugin, state) == 0
    assert state.queries["range"] == previous


@pytest.mark.parametrize("bad", [None, 0, 1, "false", [], {}])
def test_melee_combat_only_strict_bool(bad: object) -> None:
    with pytest.raises(ValueError):
        Registry().create("player_melee_enemies_count@dev", {"spell_id": 100, "combat_only": bad})
