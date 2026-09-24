"""用完整像素区域、真实布局和 Lua 5.1 显示替身验证两个独立光环百分比插件。"""

import tomllib
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.base import Condition
from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.generator import render
from phantom.core.pixels import PixelDecoder, ValueBar
from phantom.core.rotation import RotationError, load_rotation
from tests.test_aura_migration_conditions import harness

BUFF = "aura_player_buff_duration_pct@dev"
DEBUFF = "aura_target_debuff_duration_pct@dev"
PLUGINS = (BUFF, DEBUFF)
HEADER = """# 仅用于临时副本的百分比插件验证
schema_version = 1
uuid = "550e8400-e29b-41d4-a716-446655440000"
macros = []
rotation = []

[profile]
title = "光环百分比验证"
description = ""
unit_class = "DEATHKNIGHT"
unit_spec = 1
"""


def create(name: str, args: dict[str, object] | None = None) -> Condition:
    return Registry().create(name, {"aura_ids": [100, 200]} if args is None else args)


def write_rotation(tmp_path: Path, entries: list[tuple[str, str]]) -> Path:
    path = tmp_path / "duration-pct-copy.toml"
    sections = [f'\n[[conditions]]\ntitle = "光环{index}"\nplugin = "{name}"\nplugin_args = {{ {args} }}\n' for index, (name, args) in enumerate(entries)]
    path.write_text(HEADER + "".join(sections), encoding="utf-8")
    return path


@pytest.mark.parametrize("name", PLUGINS)
def test_aura_ids_are_required(name: str) -> None:
    with pytest.raises(ValueError, match="aura_ids"):
        create(name, {})


@pytest.mark.parametrize("name", PLUGINS)
@pytest.mark.parametrize("bad", [[], [0], [-1], [True], [False], [1.0], [1.5], ["100"], [100, 0], [None], [float("inf")], [float("nan")], None, 100, "100", (100,), {"100": 100}])
def test_aura_ids_require_nonempty_positive_integer_list(name: str, bad: object) -> None:
    with pytest.raises(ValueError, match="aura_ids"):
        create(name, {"aura_ids": bad})


@pytest.mark.parametrize("name", PLUGINS)
@pytest.mark.parametrize("field", ["duration", "width", "unexpected"])
@pytest.mark.parametrize("value", [5, 0, None, True])
def test_reject_extra_parameters_even_valid_former_duration_and_width(name: str, field: str, value: object) -> None:
    with pytest.raises(ValueError, match=field):
        create(name, {"aura_ids": [100], field: value})


@pytest.mark.parametrize("value", [True, False, None, 0, 1, "true", [], {}])
def test_target_rejects_player_only(value: object) -> None:
    with pytest.raises(ValueError, match="player_only"):
        create(DEBUFF, {"aura_ids": [100], "player_only": value})


@pytest.mark.parametrize("value", [None, 0, 1, "true", [], {}])
def test_buff_player_only_is_strict_boolean(value: object) -> None:
    with pytest.raises(ValueError, match="player_only"):
        create(BUFF, {"aura_ids": [100], "player_only": value})


def test_default_declaration_is_constructor_source(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = Registry()
    plugin = registry.create(BUFF, {"aura_ids": [100, 200]})
    assert dict(plugin.config_defaults) == {"player_only": True}
    assert plugin.template_parameters() == {"aura_ids": "100, 200", "aura_filter": '"HELPFUL|PLAYER"'}
    # 修改类声明的替身，验证构造缺省值没有另存一份常量；测试后自动恢复。
    monkeypatch.setattr(type(plugin), "config_defaults", {"player_only": False})
    assert registry.create(BUFF, {"aura_ids": [100]}).template_parameters()["aura_filter"] == '"HELPFUL"'
    assert registry.create(BUFF, {"aura_ids": [100], "player_only": True}).template_parameters()["aura_filter"] == '"HELPFUL|PLAYER"'
    assert create(DEBUFF).template_parameters() == {"aura_ids": "100, 200"}
    assert dict(create(DEBUFF).config_defaults) == {}


@pytest.mark.parametrize("name", PLUGINS)
@pytest.mark.parametrize("white_columns", range(21))
def test_full_region_white_columns_return_unrounded_float(name: str, white_columns: int) -> None:
    plugin = create(name)
    board_width = allocate([plugin])
    assert plugin.output.output_type == "value_bar"
    assert plugin.output.output_count == 1
    assert plugin.output.value_type is float
    assert plugin.output.value_shape == "scalar"
    assert plugin.output.widths == (5,)
    assert plugin.regions[0].width == 5
    pixels = np.zeros((20, board_width, 3), dtype=np.uint8)
    pixels[8:12, 4:28] = [255, 0, 0]
    pixels[8:12, 6:26] = 0
    pixels[8:12, 6 : 6 + white_columns] = 255
    decoder = PixelDecoder(pixels)
    raw = plugin.raw_value(decoder)
    assert raw[0] == []
    assert raw[2] == []
    assert raw[1][0].region == (4, 8, 28, 12)
    assert raw[1][0].pix_array.shape == (4, 24, 3)
    result = plugin.value(*raw, decoder=decoder)
    assert type(result) is float
    assert 0.0 <= result <= 100.0
    # 直接比较 ratio 运算结果，保留诸如 55.00000000000001 的浮点结果。
    assert result == white_columns / 20 * 100.0
    assert result == pytest.approx(white_columns * 5.0)


@pytest.mark.parametrize("name", PLUGINS)
@pytest.mark.parametrize("white,black", [(0, 0), (2, 36), (2, 0), (1, 39), (13, 26), (0, 38)])
def test_gray_exclusion_and_unequal_rows_follow_existing_ratio(name: str, white: int, black: int) -> None:
    plugin = create(name)
    board_width = allocate([plugin])
    pixels = np.zeros((20, board_width, 3), dtype=np.uint8)
    pixels[8:12, 4:28] = [255, 0, 0]
    pixels[8:12, 6:26] = 127
    # 污染外侧两行不影响结果；中间两行逐像素构造，明确允许不一致。
    pixels[8, 6:26] = 255
    pixels[11, 6:26] = [0, 255, 0]
    for index in range(white + black):
        row, column = divmod(index, 20)
        pixels[9 + row, 6 + column] = 255 if index < white else 0
    decoder = PixelDecoder(pixels)
    result = plugin.value(*plugin.raw_value(decoder), decoder=decoder)
    expected = white / (white + black) * 100.0 if white + black else 0.0
    assert type(result) is float
    assert result == expected
    assert 0.0 <= result <= 100.0
    if (white, black) in {(2, 36), (1, 39), (13, 26)}:
        assert result % 5 != 0  # 不将灰色污染或两行不一致隐藏成名义 5% 步长。


@pytest.mark.parametrize("name", PLUGINS)
def test_decode_exceptions_and_invalid_counts_fall_back_to_float_zero(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    plugin = create(name)
    board_width = allocate([plugin])
    decoder = PixelDecoder(np.zeros((20, board_width, 3), dtype=np.uint8))
    raw = plugin.raw_value(decoder)
    assert plugin.value(*raw, decoder=decoder) == 0.0
    assert type(plugin.fallback_value()) is float
    for bars in ([], raw[1] * 2):
        result = plugin.value([], bars, [], decoder=decoder)
        assert result == 0.0
        assert type(result) is float

    def broken_ratio(self: ValueBar) -> float:
        raise RuntimeError("模拟像素解码失败")

    monkeypatch.setattr(ValueBar, "ratio", property(broken_ratio))
    with pytest.raises(RuntimeError, match="模拟像素解码失败"):
        plugin.decode_value(*raw, decoder=decoder)
    result = plugin.value(*raw, decoder=decoder)
    assert result == 0.0
    assert type(result) is float


def test_two_instances_use_six_cells_each_and_decode_independently() -> None:
    first, second = create(BUFF), create(DEBUFF)
    assert allocate([first, second]) == 56
    assert [plugin.regions[0].x for plugin in (first, second)] == [1, 7]
    assert first.output is not second.output
    pixels = np.zeros((20, 56, 3), dtype=np.uint8)
    for start, white_columns in ((4, 3), (28, 17)):
        pixels[8:12, start : start + 24] = [255, 0, 0]
        pixels[8:12, start + 2 : start + 22] = 0
        pixels[8:12, start + 2 : start + 2 + white_columns] = 255
    decoder = PixelDecoder(pixels)
    assert first.raw_value(decoder)[1][0].region == (4, 8, 28, 12)
    assert second.raw_value(decoder)[1][0].region == (28, 8, 52, 12)
    assert first.value(*first.raw_value(decoder), decoder=decoder) == 15.0
    assert second.value(*second.raw_value(decoder), decoder=decoder) == 85.0
    with pytest.raises(ValueError, match="冻结"):
        allocate([first])


@pytest.mark.parametrize("name,player_only,expected_filter", [(BUFF, None, "HELPFUL|PLAYER"), (BUFF, True, "HELPFUL|PLAYER"), (BUFF, False, "HELPFUL"), (DEBUFF, None, "PLAYER|HARMFUL")])
def test_lua_official_duration_binding_and_fixed_geometry(name: str, player_only: bool | None, expected_filter: str) -> None:
    args: dict[str, object] = {"aura_ids": [100, 200]}
    if player_only is not None:
        args["player_only"] = player_only
    lua, state, addon = harness([create(name, args)])
    state.event(state, "PLAYER_ENTERING_WORLD")
    state.flushTimers(state)  # 初始化前事件安全返回。
    assert not any(frame.kind == "AuraContainer" for frame in state.frames.values())
    state.initialize(state)
    container = next(frame for frame in state.frames.values() if frame.kind == "AuraContainer")
    assert container.unit == ("player" if name == BUFF else "target")
    assert container.refreshes == 1
    assert list(container.slots.keys()) == ["aura"]
    slot = container.slots.aura
    assert slot.filter == expected_filter
    assert dict(slot.options.candidateFilters.includeSpellIDs.items()) == {100: True, 200: True}
    assert (slot.button.width, slot.button.height) == (20, 4)
    assert dict(slot.button.durationOptions.items()) == {"interpolation": 0, "direction": 1}
    bar = slot.button.durationBar
    assert lua.eval("function(a, b) return rawequal(a, b) end")(bar.parent, slot.button)
    assert bar.orientation == "HORIZONTAL"
    assert bar.barTexture == "Interface\\Buttons\\WHITE8X8"
    assert list(bar.barColor.values()) == [1, 1, 1, 1]
    assert (bar.textures[1].r, bar.textures[1].g, bar.textures[1].b) == (0, 0, 0)
    assert not any(frame.kind == "StatusBar" for frame in container.parent.children.values())
    assert container.parent.level == addon.FrameLevel.Backplate
    assert container.level == addon.FrameLevel.AuraContainer
    assert slot.button.level == addon.FrameLevel.AuraButton
    assert bar.level == addon.FrameLevel.AuraContent
    assert bar.fill is None  # 只绑定官方 consumer，插件不自行写入永久满条或绝对时长。
    assert addon.ValueBarLength == 6
    separator = next(frame for frame in state.frames.values() if frame.name and frame.name.endswith("separatorFrame"))
    assert (separator.width, separator.height) == (24, 4)
    assert list(separator.point.values())[3:] == [4, -8]
    assert list(container.parent.point.values())[3:] == [6, -8]


def test_target_gate_and_unit_events_are_deferred_without_can_attack() -> None:
    lua, state, _ = harness([create(DEBUFF)])
    lua.execute('UnitCanAttack = function() error("不应增加可攻击性门控") end')
    state.initialize(state)
    container = next(frame for frame in state.frames.values() if frame.kind == "AuraContainer")
    assert container.hidden is True
    for event, unit in (("PLAYER_TARGET_CHANGED", None), ("UNIT_FACTION", "target"), ("UNIT_FACTION", "player"), ("UNIT_FLAGS", "target"), ("PLAYER_ENTERING_WORLD", None)):
        before = container.refreshes
        state.assist = not state.assist
        old_hidden = container.hidden
        state.event(state, event, unit)
        assert container.hidden is old_hidden
        assert container.refreshes == before
        state.flushTimers(state)
        assert container.hidden is state.assist
        assert container.refreshes == before + 1
        state.flushTimers(state)
        assert container.refreshes == before + 1
    for event, unit in (("UNIT_FACTION", "focus"), ("UNIT_FLAGS", "player"), ("UNIT_FLAGS", "focus")):
        before = container.refreshes
        state.event(state, event, unit)
        state.flushTimers(state)
        assert container.refreshes == before
    calls = len(state.assistCalls)
    state.exists = False
    state.event(state, "PLAYER_TARGET_CHANGED")
    state.flushTimers(state)
    assert container.hidden is True
    assert len(state.assistCalls) == calls
    state.exists = True
    state.assist = False
    state.event(state, "PLAYER_TARGET_CHANGED")
    state.flushTimers(state)
    assert container.hidden is False


def test_lua_multiple_instances_have_independent_state_and_no_added_polling() -> None:
    ids = [100]
    first = create(BUFF, {"aura_ids": ids})
    ids.append(999)  # 输入列表后续变更不会污染本实例参数。
    second = create(BUFF, {"aura_ids": [200], "player_only": False})
    third = create(DEBUFF, {"aura_ids": [300]})
    lua, state, addon = harness([first, second, third])
    state.initialize(state)
    containers = [frame for frame in state.frames.values() if frame.kind == "AuraContainer"]
    assert len(containers) == 3
    assert addon.ValueBarLength == 18
    assert [plugin.regions[0].x for plugin in (first, second, third)] == [1, 7, 13]
    assert [dict(container.slots.aura.options.candidateFilters.includeSpellIDs.items()) for container in containers] == [{100: True}, {200: True}, {300: True}]
    assert [container.slots.aura.filter for container in containers] == ["HELPFUL|PLAYER", "HELPFUL", "PLAYER|HARMFUL"]
    equal: Any = lua.eval("function(a, b) return rawequal(a, b) end")
    for left, right in ((containers[0], containers[1]), (containers[1], containers[2])):
        assert not equal(left, right)
        assert not equal(left.slots.aura.button, right.slots.aura.button)
        assert not equal(left.slots.aura.button.durationBar, right.slots.aura.button.durationBar)
    state.event(state, "PLAYER_TARGET_CHANGED")
    assert [container.refreshes for container in containers] == [1, 1, 1]
    state.flushTimers(state)
    assert [container.refreshes for container in containers] == [1, 1, 2]
    state.event(state, "PLAYER_ENTERING_WORLD")
    assert [container.refreshes for container in containers] == [1, 1, 2]
    state.flushTimers(state)
    assert [container.refreshes for container in containers] == [2, 2, 3]
    # 原 duration 模板无 OnUpdate；保留事件生命周期，不为了测试加入随机轮询。
    assert not any(frame.OnUpdate for frame in state.frames.values())
    assert state.randomCalls == 0
    state.tick(state, 100)
    state.flushTimers(state)
    assert [container.refreshes for container in containers] == [2, 2, 3]


@pytest.mark.parametrize("name", PLUGINS)
def test_event_bursts_preserve_existing_per_event_deferred_callbacks(name: str) -> None:
    _, state, _ = harness([create(name)])
    state.initialize(state)
    container = next(frame for frame in state.frames.values() if frame.kind == "AuraContainer")
    state.event(state, "PLAYER_ENTERING_WORLD")
    state.event(state, "PLAYER_ENTERING_WORLD")
    assert container.refreshes == 1
    # 原模板逐事件排队，不承诺同帧合并；明确记录此边界，避免把轮询节流规则套到事件上。
    assert len(state.timers) == 2
    state.flushTimers(state)
    assert container.refreshes == 3
    state.flushTimers(state)
    assert container.refreshes == 3


def test_temporary_rotation_defaults_layout_and_actual_generated_lua51(tmp_path: Path) -> None:
    path = write_rotation(tmp_path, [(BUFF, "aura_ids = [100]"), (BUFF, "aura_ids = [200], player_only = false"), (DEBUFF, "aura_ids = [300]")])
    rotation = load_rotation(path)
    assert rotation.board_width == 80
    assert [entry.instance.regions[0].x for entry in rotation.conditions] == [1, 7, 13]
    saved = tomllib.loads(path.read_text(encoding="utf-8"))
    assert [entry["plugin_args"] for entry in saved["conditions"]] == [{"aura_ids": [100], "player_only": True}, {"aura_ids": [200], "player_only": False}, {"aura_ids": [300]}]
    before = path.read_bytes()
    load_rotation(path)
    assert path.read_bytes() == before
    generated = render(rotation, "PhantomTest")
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    compile_lua: Any = lua.eval("function(source) assert(loadstring(source)); return true end")
    assert lua.eval("_VERSION") == "Lua 5.1"
    instance_sources: list[str] = []
    for filename, source in generated.items():
        if filename.endswith(".lua"):
            assert compile_lua(source), filename
            assert "{{" not in source
            if "local AURA_IDS" in source:
                instance_sources.append(source)
    assert len(instance_sources) == 3
    assert len(set(instance_sources)) == 3


@pytest.mark.parametrize("name,extra", [(BUFF, "duration = 12"), (BUFF, "width = 5"), (DEBUFF, "duration = 12"), (DEBUFF, "width = 5"), (DEBUFF, "player_only = true")])
def test_invalid_temporary_rotation_does_not_write_defaults(tmp_path: Path, name: str, extra: str) -> None:
    path = write_rotation(tmp_path, [(BUFF, "aura_ids = [100]"), (name, f"aura_ids = [200], {extra}")])
    before = path.read_bytes()
    with pytest.raises(RotationError):
        load_rotation(path)
    assert path.read_bytes() == before
