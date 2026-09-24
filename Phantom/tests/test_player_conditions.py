from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Value
from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.generator import render
from phantom.core.pixels import Cell, IconTile, PixelDecoder
from phantom.core.rotation import ConditionEntry, load_rotation

ROOT = Path(__file__).resolve().parents[1]
CASES: dict[str, dict[str, object]] = {
    "player_role": {},
    "player_in_combat": {},
    "player_is_player_target": {},
    "player_is_moving": {},
    "player_in_vehicle": {},
    "player_melee_enemies_count": {"spell_id": 49998},
    "player_is_targeting_spell": {},
    "player_is_chatting": {},
    "player_in_group": {},
    "player_trinket_ready": {"slot_id": 13},
    "player_healthstone_ready": {},
    "player_heal_potion_ready": {},
    "player_cast_progress": {},
    "player_is_empowering": {},
    "player_cast_icon": {},
    "player_cast_target": {},
    "player_has_big_defensive": {},
    "player_has_dispellable_debuff": {"dispel_types": {"Magic": True, "Poison": False}},
    "spell_known": {"spell_ids": [100, 200]},
    "talent_known": {"spell_ids": [100, 200]},
    "player_damage_absorb": {"threshold": 10000},
    "player_heal_absorb": {"threshold": 10000},
    "player_has_buff": {"buff_ids": [188298, 188290]},
}


def create(name: str, args: dict[str, object] | None = None) -> Condition:
    return Registry().create(f"{name}@dev", CASES[name] if args is None else args)


def harness(plugins: list[Condition], *, initialize: bool = True) -> tuple[Any, Any, Any]:
    allocate(plugins)
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state: Any
    addon: Any
    state, addon = lua.execute((ROOT / "tests/lua/player_conditions_harness.lua").read_text(encoding="utf-8"))
    execute: Any = lua.eval("function(source, addon) assert(loadstring(source))('PhantomTest', addon) end")
    # Exercise the actual Cell and IconTile consumers, rather than substituting plugin-specific writers.
    for filename in ("07_cell_backplate.lua", "08_cell.lua", "11_icon_tile_backplate.lua", "12_icon_tile.lua"):
        execute((ROOT / "phantom/lua/runtime" / filename).read_text(encoding="utf-8"), addon)
    for index, plugin in enumerate(plugins):
        execute(plugin.generate_lua(f"test-{index}"), addon)
    if initialize:
        state.initialize(state)
    return lua, state, addon


def decode(plugin: Condition, brightness: float) -> Value:
    decoder = PixelDecoder(np.zeros((20, 128, 3), dtype=np.uint8))
    pixels = np.full((4, 4, 3), int(brightness + 0.5), dtype=np.uint8)
    return plugin.value([Cell(1, 2, pixels)], [], [], decoder=decoder)


def emit(state: Any, event: str, unit: str | None = None, target: Any = None) -> None:
    state.event(state, event, unit, target)


def value(plugin: Condition, state: Any, x: int = 1) -> Value:
    return decode(plugin, state.brightness(state, x))


@pytest.mark.parametrize("name", CASES)
def test_every_plugin_initialization_world_event_and_decode_boundary(name: str) -> None:
    plugin = create(name)
    _, state, _ = harness([plugin], initialize=False)
    # World events may arrive before the shared UI exists.
    emit(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)
    state.flushTimers(state)
    state.initialize(state)
    emit(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)
    state.flushTimers(state)
    frames = [frame for frame in state.frames.values() if frame.events["PLAYER_ENTERING_WORLD"]]
    assert len(frames) == 1
    decoder = PixelDecoder(np.zeros((20, 128, 3), dtype=np.uint8))
    assert plugin.value([], [], [], decoder=decoder) == plugin.fallback_value()
    if plugin.output.output_type == "cell":
        assert type(value(plugin, state)) is plugin.output.value_type
        if plugin.output.value_type is bool:
            assert decode(plugin, 255) is True
            assert decode(plugin, 0) is False
            with pytest.raises(ValueError):
                plugin.decode_value([Cell(1, 2, np.full((4, 4, 3), 127, dtype=np.uint8))], [], [], decoder=decoder)
        for damage in ("mixed", "colored"):
            image = np.full((4, 4, 3), 255, dtype=np.uint8)
            if damage == "mixed":
                image[1, 1] = 0
            else:
                image[:] = [255, 0, 0]
            with pytest.raises(ValueError):
                plugin.decode_value([Cell(1, 2, image)], [], [], decoder=decoder)
            assert plugin.value([Cell(1, 2, image)], [], [], decoder=decoder) == plugin.fallback_value()


@pytest.mark.parametrize("name", CASES)
def test_parameters_reject_unknown_and_missing_fields(name: str) -> None:
    with pytest.raises(ValueError):
        create(name, {**CASES[name], "unexpected": 1})
    if CASES[name]:
        with pytest.raises(ValueError):
            create(name, {})


@pytest.mark.parametrize("name,field", [("player_melee_enemies_count", "spell_id"), ("player_trinket_ready", "slot_id")])
@pytest.mark.parametrize("bad", [None, False, True, 0, -1, 1.5, "13", [], {}])
def test_invalid_scalar_ids(name: str, field: str, bad: object) -> None:
    with pytest.raises(ValueError):
        create(name, {field: bad})


@pytest.mark.parametrize("slot", [1, 12, 15, 100])
def test_trinket_slot_bounds(slot: int) -> None:
    with pytest.raises(ValueError):
        create("player_trinket_ready", {"slot_id": slot})


@pytest.mark.parametrize("name,field", [("spell_known", "spell_ids"), ("talent_known", "spell_ids"), ("player_has_buff", "buff_ids")])
@pytest.mark.parametrize("bad", [[], [0], [-1], [True], [1.5], ["100"], 100, "100", None])
def test_invalid_id_lists(name: str, field: str, bad: object) -> None:
    with pytest.raises(ValueError):
        create(name, {field: bad})


@pytest.mark.parametrize("player_only", [None, True, False])
def test_player_buff_source_filter_default_and_override(player_only: bool | None) -> None:
    args = CASES["player_has_buff"].copy()
    if player_only is not None:
        args["player_only"] = player_only
    plugin = create("player_has_buff", args)
    _, state, _ = harness([plugin])
    container = next(frame for frame in state.frames.values() if frame.kind == "AuraContainer")
    assert plugin.config_defaults["player_only"] is True
    assert container.slots.aura.filter == ("HELPFUL" if player_only is False else "HELPFUL|PLAYER")
    assert dict(container.slots.aura.options.candidateFilters.includeSpellIDs.items()) == {188298: True, 188290: True}


@pytest.mark.parametrize("bad", [None, 0, 1, "true", [], {}])
def test_player_buff_source_filter_requires_boolean(bad: object) -> None:
    with pytest.raises(ValueError, match="player_only"):
        create("player_has_buff", {**CASES["player_has_buff"], "player_only": bad})


@pytest.mark.parametrize("name", ["player_damage_absorb", "player_heal_absorb"])
@pytest.mark.parametrize("bad", [True, False, -1, 0.5, "0", None, 9007199254740991, 10**100])
def test_invalid_threshold(name: str, bad: object) -> None:
    with pytest.raises(ValueError):
        create(name, {"threshold": bad})


@pytest.mark.parametrize("bad", [None, [], {"magic": True}, {"Bleed": True}, {"Magic": 1}, {"Magic": "true"}, {"Magic": None}])
def test_invalid_dispel_map(bad: object) -> None:
    with pytest.raises(ValueError):
        create("player_has_dispellable_debuff", {"dispel_types": bad})


@pytest.mark.parametrize("role,brightness", [("NONE", 0), ("TANK", 85), ("HEALER", 170), ("DAMAGER", 255)])
def test_roles_roundtrip(role: str, brightness: int) -> None:
    plugin = create("player_role")
    _, state, _ = harness([plugin])
    state.role = role
    emit(state, "PLAYER_ROLES_ASSIGNED")
    state.flushTimers(state)
    assert state.brightness(state, 1) == brightness
    assert value(plugin, state) == role
    state.role = state.secret(state, "TANK")
    emit(state, "ROLE_CHANGED_INFORM")
    state.flushTimers(state)
    assert value(plugin, state) == "NONE"
    assert decode(plugin, 1) == "NONE"


@pytest.mark.parametrize(
    "name,field,event",
    [
        ("player_in_combat", "combat", "PLAYER_REGEN_DISABLED"),
        ("player_is_player_target", "selfTarget", "PLAYER_TARGET_CHANGED"),
        ("player_in_vehicle", "mounted", "PLAYER_MOUNT_DISPLAY_CHANGED"),
        ("player_in_vehicle", "vehicle", "UNIT_ENTERED_VEHICLE"),
        ("player_is_targeting_spell", "targeting", "CURRENT_SPELL_CAST_CHANGED"),
        ("player_in_group", "grouped", "GROUP_JOINED"),
        ("player_in_group", "raiding", "GROUP_ROSTER_UPDATE"),
    ],
)
def test_boolean_event_business_paths(name: str, field: str, event: str) -> None:
    plugin = create(name)
    _, state, _ = harness([plugin])
    state[field] = True
    emit(state, event, "player")
    assert value(plugin, state) is False  # Event refresh waits until the next frame.
    state.flushTimers(state)
    assert value(plugin, state) is True
    state[field] = False
    emit(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)
    assert value(plugin, state) is False


def test_secret_boolean_reaches_real_cell_consumer() -> None:
    plugin = create("player_is_player_target")
    _, state, _ = harness([plugin])
    for expected in (True, False):
        state.selfTarget = state.secret(state, expected)
        emit(state, "PLAYER_TARGET_CHANGED")
        state.flushTimers(state)
        assert value(plugin, state) is expected


def test_moving_deferred_next_frame_and_unfiltered_poll() -> None:
    plugin = create("player_is_moving")
    _, state, _ = harness([plugin])
    emit(state, "PLAYER_STARTED_MOVING")
    assert not state.queries.moving
    state.moving = True  # The event arrived before IsPlayerMoving reflected the new state.
    state.flushTimers(state)
    assert value(plugin, state) is True
    emit(state, "PLAYER_STOPPED_MOVING")
    assert value(plugin, state) is True
    state.moving = False
    state.flushTimers(state)
    assert value(plugin, state) is False
    state.moving = True
    state.tick(state, 3)
    assert value(plugin, state) is True


def test_polling_stagger_remainder_and_single_update_per_frame() -> None:
    plugins = [create("player_in_combat"), create("player_in_combat")]
    _, state, _ = harness(plugins)
    assert state.randomCalls == 2
    state.combat = True
    state.tick(state, 1.015)
    assert value(plugins[0], state, 1) is True
    assert value(plugins[1], state, 2) is False
    state.tick(state, 0.01)
    assert value(plugins[1], state, 2) is True
    state.queries.combat = 0
    state.tick(state, 10)
    assert state.queries.combat == 2  # No while-loop catch-up on one frame.
    state.tick(state, 0)
    assert state.queries.combat == 4  # Accumulated remainder was retained.


def test_chat_focus_includes_non_chat_input_and_chat_callbacks() -> None:
    plugin = create("player_is_chatting")
    lua, state, _ = harness([plugin])
    state.focus = lua.table_from({"name": "SearchBox"})
    emit(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)
    assert value(plugin, state) is True
    assert len(list(state.callbacks.keys())) == 4
    state.focus = None
    state.callbacks["ChatFrame.OnEditBoxFocusLost"].callback()
    state.flushTimers(state)
    assert value(plugin, state) is False


def test_melee_all_counts_and_restricted_ranges() -> None:
    plugin = create("player_melee_enemies_count")
    lua, state, _ = harness([plugin])
    for count in range(41):
        if count:
            unit = f"nameplate{count}"
            state.units[unit] = lua.table_from({"attackable": True})
            state.ranges[unit] = True
        emit(state, "NAME_PLATE_UNIT_ADDED")
        state.flushTimers(state)
        assert value(plugin, state) == count
    assert state.lastRangeSpell == 49998
    state.ranges.nameplate1 = state.secret(state, True)
    state.ranges.nameplate2 = None
    state.ranges.nameplate3 = False
    state.units.nameplate4.attackable = False
    state.units.nameplate5 = None
    state.units.nameplate41 = lua.table_from({"attackable": True})
    state.ranges.nameplate41 = True
    emit(state, "NAME_PLATE_UNIT_REMOVED")
    state.flushTimers(state)
    assert value(plugin, state) == 35


@pytest.mark.parametrize("name,item_id", [("player_trinket_ready", 123), ("player_healthstone_ready", 224464), ("player_heal_potion_ready", 258138)])
def test_item_readiness(name: str, item_id: int) -> None:
    plugin = create(name)
    lua, state, _ = harness([plugin])
    state.inventory[13] = item_id
    for duration, enabled, usable, no_mana, expected in [(0, True, True, False, True), (1, True, True, False, False), (0, False, True, False, False), (0, True, False, False, False), (0, True, True, True, False)]:
        state["items"][item_id] = lua.table_from({"duration": duration, "enabled": enabled, "usable": usable, "noMana": no_mana})
        emit(state, "BAG_UPDATE_COOLDOWN")
        state.flushTimers(state)
        assert state.lastItem == item_id
        assert value(plugin, state) is expected
    if name == "player_trinket_ready":
        state.queries.item = 0
        state.event(state, "PLAYER_EQUIPMENT_CHANGED", 14)
        state.flushTimers(state)
        assert state.queries.item == 0
        state.inventory[13] = None
        state.event(state, "PLAYER_EQUIPMENT_CHANGED", 13)
        state.flushTimers(state)
        assert value(plugin, state) is False


def test_trinket_instances_use_distinct_slots() -> None:
    plugins = [create("player_trinket_ready", {"slot_id": slot}) for slot in (13, 14)]
    lua, state, _ = harness(plugins)
    state.inventory[13], state.inventory[14] = 111, 222
    state["items"][111] = lua.table_from({"duration": 0, "enabled": True, "usable": True, "noMana": False})
    state["items"][222] = lua.table_from({"duration": 10, "enabled": True, "usable": True, "noMana": False})
    emit(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)
    assert value(plugins[0], state, 1) is True
    assert value(plugins[1], state, 2) is False


@pytest.mark.parametrize("mode,empowered", [("casting", False), ("channeling", False), ("channeling", True)])
def test_cast_progress_empower_and_icon_transitions(mode: str, empowered: bool) -> None:
    plugins = [create(name) for name in ("player_cast_progress", "player_is_empowering", "player_cast_icon")]
    _, state, _ = harness(plugins)
    state.mode, state.empowered = mode, empowered
    state.castTexture = state.secret(state, 123456)
    state.secretDuration = True
    for progress in (0, 0.25, 0.5, 0.75, 1):
        state.progress = progress
        emit(state, "UNIT_SPELLCAST_START", "target")
        state.flushTimers(state)
        emit(state, "UNIT_SPELLCAST_CHANNEL_UPDATE", "player")
        state.flushTimers(state)
        assert value(plugins[0], state, 1) == pytest.approx(progress * 100, abs=0.2)
        assert value(plugins[1], state, 2) is empowered
        assert state.icons[1].textures[2].texture == 123456
        assert not state.icons[1].textures[2].hidden
    state.noDuration = True
    emit(state, "UNIT_SPELLCAST_DELAYED", "player")
    state.flushTimers(state)
    assert value(plugins[0], state, 1) == 0.0
    state.mode = None
    emit(state, "UNIT_SPELLCAST_STOP", "player")
    state.flushTimers(state)
    assert value(plugins[0], state, 1) == 0.0
    assert value(plugins[1], state, 2) is False
    assert state.icons[1].textures[2].hidden
    assert state.icons[1].textures[3].hidden


def test_progress_poll_updates_and_ignores_other_units() -> None:
    plugin = create("player_cast_progress")
    _, state, _ = harness([plugin])
    state.mode, state.progress = "casting", 0.5
    emit(state, "UNIT_SPELLCAST_START", "target")
    state.flushTimers(state)
    assert value(plugin, state) == 0.0
    state.tick(state, 0.12)
    assert value(plugin, state) == pytest.approx(50, abs=0.2)
    state.progress = 1
    state.tick(state, 0.1)
    assert value(plugin, state) == 100.0


def test_icon_hash_and_empty_string() -> None:
    plugin = create("player_cast_icon")
    allocate([plugin])
    image = np.zeros((20, 28, 3), dtype=np.uint8)
    decoder = PixelDecoder(image)
    assert plugin.value(*plugin.raw_value(decoder), decoder=decoder) == ""
    image[12:20, 4:12] = np.arange(192, dtype=np.uint8).reshape(8, 8, 3)
    decoder = PixelDecoder(image)
    result = plugin.value(*plugin.raw_value(decoder), decoder=decoder)
    assert result == IconTile(1, image[12:20, 4:12]).hash
    assert isinstance(result, str) and len(result) == 16


def test_cast_targets_all_tokens_secret_retention_and_clearing() -> None:
    plugin = create("player_cast_target")
    lua, state, _ = harness([plugin])
    tokens = ["player"] + [f"party{i}" for i in range(1, 5)] + [f"raid{i}" for i in range(1, 41)]
    for index, token in enumerate(tokens, 1):
        state.units[token] = lua.table_from({"name": f"Person{index}"})
        emit(state, "UNIT_SPELLCAST_SENT", "player", f"Person{index}")
        state.flushTimers(state)
        assert value(plugin, state) == token
    emit(state, "UNIT_SPELLCAST_SENT", "player", state.secret(state, "hidden"))
    state.flushTimers(state)
    assert value(plugin, state) == "raid40"
    state.tick(state, 3)
    assert value(plugin, state) == ""
    for event in ("STOP", "INTERRUPTED", "FAILED", "FAILED_QUIET", "SUCCEEDED"):
        emit(state, "UNIT_SPELLCAST_SENT", "player", "Person1")
        state.flushTimers(state)
        assert value(plugin, state) == "player"
        emit(state, f"UNIT_SPELLCAST_{event}", "player")
        state.flushTimers(state)
        assert value(plugin, state) == ""
    for target in (None, "Enemy", ""):
        emit(state, "UNIT_SPELLCAST_SENT", "player", target)
        state.flushTimers(state)
        assert value(plugin, state) == ""
    state.units.player.name = state.secret(state, "Person1")
    emit(state, "UNIT_SPELLCAST_SENT", "player", "Person1")
    state.flushTimers(state)
    assert value(plugin, state) == ""
    assert decode(plugin, 226) == ""
    assert decode(plugin, 255) == ""


@pytest.mark.parametrize("name", ["spell_known", "talent_known"])
def test_spell_candidates_and_next_frame_refresh(name: str) -> None:
    plugin = create(name)
    _, state, _ = harness([plugin])
    state.known[200] = True
    emit(state, "SPELLS_CHANGED")
    emit(state, "SPELLS_CHANGED")
    assert len(state.timers) == 3
    assert all(timer.delay == 0 for timer in state.timers.values())
    assert not state.queries.known
    state.flushTimers(state)
    assert state.queries.known == 6
    assert value(plugin, state) is True
    state.known[200] = False
    state.spellbook[100] = True
    emit(state, "SPELLS_CHANGED")
    state.flushTimers(state)
    assert value(plugin, state) is True
    state.spellbook[100] = False
    emit(state, "SPELLS_CHANGED")
    state.flushTimers(state)
    assert value(plugin, state) is False


@pytest.mark.parametrize("name,field,event", [("player_damage_absorb", "absorbs", "UNIT_ABSORB_AMOUNT_CHANGED"), ("player_heal_absorb", "healAbsorbs", "UNIT_HEAL_ABSORB_AMOUNT_CHANGED")])
@pytest.mark.parametrize("threshold", [0, 10000, 9007199254740990])
def test_absorb_opaque_values_boundaries_and_units(name: str, field: str, event: str, threshold: int) -> None:
    plugin = create(name, {"threshold": threshold})
    lua, state, _ = harness([plugin])
    bar = state.cells[1].children[1]
    assert bar.low == threshold and bar.high == threshold + 1
    for amount in (max(0, threshold - 1), threshold, threshold + 1):
        state[field] = state.secret(state, amount)
        emit(state, event, "player")
        state.flushTimers(state)
        same: Any = lua.eval("function(a,b) return rawequal(a,b) end")
        assert same(bar.rawValue, state[field])
        assert value(plugin, state) is (amount > threshold)
    state[field] = state.secret(state, 0)
    emit(state, event, "target")
    state.flushTimers(state)
    assert value(plugin, state) is True
    emit(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)
    assert value(plugin, state) is False


@pytest.mark.parametrize("name,filter_string", [("player_has_big_defensive", "HELPFUL|BIG_DEFENSIVE"), ("player_has_dispellable_debuff", "HARMFUL|RAID_PLAYER_DISPELLABLE"), ("player_has_buff", "HELPFUL|PLAYER")])
def test_managed_aura_slot_contract_and_world_refresh(name: str, filter_string: str) -> None:
    plugin = create(name)
    _, state, addon = harness([plugin])
    container = state.cells[1].children[1]
    slot = container.slots.aura
    assert container.unit == "player" and slot.filter == filter_string
    assert container.level == addon.FrameLevel.AuraContainer
    assert slot.button.level == addon.FrameLevel.AuraButton
    overlay = slot.button.ActiveOverlay
    assert (overlay.r, overlay.g, overlay.b, overlay.a) == (1, 1, 1, 1)
    assert slot.button.width == slot.button.height == 4
    assert not slot.button.OnShow and not slot.button.OnHide and not slot.button.OnUpdate
    assert not container.OnUpdate
    if name == "player_has_big_defensive":
        assert slot.options.sortMethod == 1 and slot.options.sortDirection == 0
    elif name == "player_has_buff":
        assert dict(slot.options.candidateFilters.includeSpellIDs.items()) == {188298: True, 188290: True}
    else:
        assert dict(slot.options.candidateFilters.includeDispelTypes.items()) == {"Magic": True, "Poison": False, "Disease": False, "Curse": False, "Stealth": False, "Special": False, "Enrage": False}
    emit(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)
    assert container.refreshes == 1


@pytest.mark.parametrize("types", [{}, {"Magic": False}, {key: True for key in ("Magic", "Poison", "Disease", "Curse", "Stealth", "Special", "Enrage")}])
def test_dispel_maps_fill_missing_types_and_preserve_explicit_values(types: dict[str, bool]) -> None:
    plugin = create("player_has_dispellable_debuff", {"dispel_types": types})
    _, state, _ = harness([plugin])
    candidates = state.cells[1].children[1].slots.aura.options.candidateFilters
    assert candidates.includeDispelTypes is not None
    # 缺失类型显式补 false，空表仍不匹配，已有 true/false 不被默认值覆盖。
    expected = dict.fromkeys(("Magic", "Poison", "Disease", "Curse", "Stealth", "Special", "Enrage"), False) | types
    assert dict(candidates.includeDispelTypes.items()) == expected


def test_all_plugins_generate_together_with_independent_layouts(tmp_path: Path) -> None:
    entries = tuple(ConditionEntry(name, f"{name}@dev", create(name)) for name in CASES)
    width = allocate([entry.instance for entry in entries])
    # 加载器可能补写默认参数，只在测试副本上生成，避免改写夹具。
    rotation_path = tmp_path / "engine.toml"
    rotation_path.write_bytes((ROOT / "tests/fixtures/engine-rotation.toml").read_bytes())
    rotation = replace(load_rotation(rotation_path), conditions=entries, macros=(), board_width=width)
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    compile_lua: Any = lua.eval("function(source) assert(loadstring(source)); return true end")
    sources = render(rotation, "PhantomTest")
    for filename, source in sources.items():
        if filename.endswith(".lua"):
            assert compile_lua(source), filename
            assert "{{" not in source
    assert width == (22 + 2) * 4
    assert [entry.instance.regions[0].x for entry in entries if entry.instance.output.output_type == "cell"] == list(range(1, 23))
    decoder = PixelDecoder(np.zeros((20, width, 3), dtype=np.uint8))
    for entry in entries:
        assert entry.instance.output.accepts(entry.instance.value(*entry.instance.raw_value(decoder), decoder=decoder))


def test_cast_target_deferred_events_preserve_payload_order() -> None:
    plugin = create("player_cast_target")
    lua, state, _ = harness([plugin])
    state.units.party1 = lua.table_from({"name": "First"})
    state.units.party2 = lua.table_from({"name": "Second"})
    emit(state, "UNIT_SPELLCAST_SENT", "player", "First")
    emit(state, "UNIT_SPELLCAST_STOP", "player")
    emit(state, "UNIT_SPELLCAST_SENT", "player", "Second")
    assert value(plugin, state) == ""
    state.flushTimers(state)
    assert value(plugin, state) == "party2"
    state.tick(state, 1.02)
    assert value(plugin, state) == ""
