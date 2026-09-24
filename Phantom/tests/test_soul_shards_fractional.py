"""灵魂碎片小数模式的真实 ValueBar、合成像素、表达式及秘密值边界离线验证。"""

from pathlib import Path
from typing import Any
from unittest.mock import PropertyMock, patch

import numpy as np
import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Value
from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.expression import evaluate, parse_expression
from phantom.core.pixels import PixelDecoder, ValueBar
from phantom.core.rotation import load_rotation

ROOT = Path(__file__).resolve().parents[1]

# 扩展已有显示替身，使用真实 ValueBar；只有既有 StatusBar 消费者可以解释秘密值。
EXTENSION = """
local state, addon = ...
Enum.PowerType = {SoulShards = 7}
addon.ValueBarLength = 0
addon.COLOR.RED = {GetRGBA = function() return 1, 0, 0, 1 end}
state.power = 0
state.powerCalls = 0
state.bars = {}
UnitPower = function(unit, powerType, unmodified)
    assert(unit == "player" and powerType == 7)
    assert(unmodified == state.fractional)
    state.powerCalls = state.powerCalls + 1
    return state.power
end
UnitPowerDisplayMod = function() error("不得在 Lua 换算片段") end
UnitPowerMax = function() error("固定量程不读取动态最大值") end
local original = CreateFrame
CreateFrame = function(kind, name, parent, template)
    local frame = original(kind, name, parent, template)
    function frame:SetColorFill(r, g, b, a)
        assert(r == 1 and g == 1 and b == 1)
        self.fillColor = {r, g, b, a}
    end
    if kind == "StatusBar" then table.insert(state.bars, frame) end
    return frame
end
"""


def create(args: dict[str, object] | None = None) -> Condition:
    return Registry().create("spec_power_soul_shards@dev", {"fractional": True} if args is None else args)


def harness(plugin: Condition, *, prefix: list[Condition] | None = None) -> tuple[Any, Any, Any]:
    allocate([*(prefix or []), plugin])
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state, addon = lua.execute((ROOT / "tests/lua/player_conditions_harness.lua").read_text(encoding="utf-8"))
    lua.execute(EXTENSION, state, addon)
    state.fractional = plugin.output.value_type is float
    if state.fractional:
        # 小数路径不应检查 secret；身份传递由测试端 rawequal 验证。
        lua.execute('issecretvalue = function() error("小数路径不得检查秘密值") end')
    execute: Any = lua.eval("function(source, addon) assert(loadstring(source))('PhantomTest', addon) end")
    for filename in ("07_cell_backplate.lua", "08_cell.lua", "09_value_bar_backplate.lua", "10_value_bar.lua"):
        execute((ROOT / "phantom/lua/runtime" / filename).read_text(encoding="utf-8"), addon)
    execute(plugin.generate_lua("soul-shards-test"), addon)
    return lua, state, addon


def pixels(plugin: Condition, fill: float) -> PixelDecoder:
    region = plugin.regions[0]
    assert region.width is not None
    width = region.width
    image = np.zeros((20, (region.x + width + 2) * 4, 3), dtype=np.uint8)
    start = region.x * 4
    image[8:12, start : start + 2] = [255, 0, 0]
    image[8:12, start + 2 + width * 4 : start + (width + 1) * 4] = [255, 0, 0]
    white_columns = int(fill * width * 4 + 0.5)
    image[8:12, start + 2 : start + 2 + white_columns] = 255
    return PixelDecoder(image)


def decode(plugin: Condition, decoder: PixelDecoder) -> Value:
    cells, bars, icons = plugin.raw_value(decoder)
    return plugin.value(cells, bars, icons, decoder=decoder)


@pytest.mark.parametrize("width", [25, 50])
@pytest.mark.parametrize("secret", [False, True])
@pytest.mark.parametrize("fragments", range(51))
def test_all_fragments_real_valuebar_pixels_and_expressions(width: int, secret: bool, fragments: int) -> None:
    plugin = create({"fractional": True, "width": width})
    lua, state, addon = harness(plugin)
    power = state.secret(state, fragments) if secret else fragments
    state.power = power
    state.initialize(state)
    bar = state.bars[1]
    assert len(state.bars) == 1
    assert (bar.low, bar.high) == (0, 50)
    assert lua.eval("rawequal")(bar.rawValue, power)
    assert bar.parent.width == width * 4
    assert bar.parent.point[4] == 6
    assert addon.ValueBarLength == width + 1
    assert addon.ConditionCellLength == 0
    assert state.powerCalls == 1
    result = decode(plugin, pixels(plugin, bar.fill))
    assert type(result) is float
    assert result == fragments / 10
    outputs = {"灵魂碎片": plugin.output}
    assert evaluate(parse_expression("灵魂碎片 >= 1.5", outputs), {"灵魂碎片": result}) is (fragments >= 15)
    assert evaluate(parse_expression("灵魂碎片 <= 4", outputs), {"灵魂碎片": result}) is (fragments <= 40)


@pytest.mark.parametrize("fragments", [14, 15, 16, 39, 40, 41])
def test_default_width_fragment_thresholds(fragments: int) -> None:
    plugin = create()
    allocate([plugin])
    assert plugin.output.widths == (25,)
    assert decode(plugin, pixels(plugin, fragments / 50)) == fragments / 10


def test_fractional_frozen_position_after_other_output_regions() -> None:
    # 混合区域按行独立分配，前面的Cell不应改变Bar列，前面的Bar应保留分隔占位。
    prefix = [create({}), Registry().create("spell_charges@dev", {"spell_ids": [1], "max_charges": 2, "width": 3})]
    plugin = create()
    _, state, _ = harness(plugin, prefix=prefix)
    state.power = state.secret(state, 41)
    state.initialize(state)
    assert plugin.regions[0].metadata() == {"x": 5, "width": 25}
    assert state.bars[1].parent.point[4] == 22
    assert decode(plugin, pixels(plugin, state.bars[1].fill)) == 4.1


@pytest.mark.parametrize("args", [{}, {"fractional": False}])
def test_legacy_cell_contract_and_unmodified_false(args: dict[str, object]) -> None:
    plugin = create(args)
    _, state, addon = harness(plugin)
    assert plugin.output.output_type == "cell"
    assert plugin.output.value_type is int
    assert plugin.output.widths == ()
    assert plugin.regions[0].metadata() == {"x": 1, "y": 2}
    state.power = 5
    state.initialize(state)
    assert len(state.bars) == 0
    assert addon.ValueBarLength == 0
    assert state.brightness(state, 1) == 5
    image = np.zeros((20, 16, 3), dtype=np.uint8)
    image[4:8, 4:8] = 5
    result = decode(plugin, PixelDecoder(image))
    assert type(result) is int
    assert result == 5
    assert type(plugin.fallback_value()) is int
    assert plugin.fallback_value() == 0


@pytest.mark.parametrize("width", [1, 7, 25, 37, 50])
def test_explicit_width_preserves_range_and_frozen_layout(width: int) -> None:
    plugin = create({"fractional": True, "width": width})
    _, state, _ = harness(plugin)
    state.power = 50
    state.initialize(state)
    assert plugin.regions[0].metadata() == {"x": 1, "width": width}
    assert state.bars[1].parent.width == width * 4
    assert decode(plugin, pixels(plugin, state.bars[1].fill)) == 5.0
    assert plugin.output.value_type is float
    with pytest.raises(ValueError, match="已冻结"):
        allocate([plugin])


def test_narrow_width_does_not_promise_single_fragment_resolution() -> None:
    plugin = create({"fractional": True, "width": 1})
    allocate([plugin])
    assert decode(plugin, pixels(plugin, 14 / 50)) == decode(plugin, pixels(plugin, 15 / 50)) == 1.3


@pytest.mark.parametrize("bad", [None, 0, 1, 0.0, 1.0, "true", "false", [], {}])
def test_fractional_requires_strict_boolean(bad: object) -> None:
    with pytest.raises(ValueError, match="fractional"):
        create({"fractional": bad})


@pytest.mark.parametrize("bad", [None, True, False, 0, -1, 1.5, 25.0, float("inf"), float("nan"), "25", [], {}])
def test_fractional_width_requires_strict_positive_integer(bad: object) -> None:
    with pytest.raises(ValueError, match="width"):
        create({"fractional": True, "width": bad})


@pytest.mark.parametrize("args", [{"width": 25}, {"fractional": False, "width": 25}, {"fractional": True, "max_power": 50}, {"fractional": True, "power_type": 7}])
def test_inapplicable_and_unknown_parameters_rejected(args: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        create(args)


@pytest.mark.parametrize("event", ["PLAYER_ENTERING_WORLD", "UNIT_POWER_UPDATE", "UNIT_POWER_FREQUENT", "UNIT_MAXPOWER", "UNIT_DISPLAYPOWER"])
def test_fragment_events_defer_filter_and_keep_layout(event: str) -> None:
    plugin = create()
    lua, state, _ = harness(plugin)
    state.event(state, event, "player", state.secret(state, "事件参数"))
    state.flushTimers(state)
    assert state.powerCalls == 0
    state.power = state.secret(state, 14)
    state.initialize(state)
    bar = state.bars[1]
    regions = plugin.regions
    frame_count = len(state.frames)
    assert decode(plugin, pixels(plugin, bar.fill)) == 1.4
    if event.startswith("UNIT_"):
        state.event(state, event, "target", state.secret(state, "其他单位"))
        state.flushTimers(state)
        assert state.powerCalls == 1
    # 14→15 没有整碎片变化，仍必须在下一帧刷新。
    state.power = state.secret(state, 15)
    state.event(state, event, "player", state.secret(state, "不得读取资源类型"))
    assert state.powerCalls == 1
    assert decode(plugin, pixels(plugin, bar.fill)) == 1.4
    state.flushTimers(state)
    assert state.powerCalls == 2
    assert lua.eval("rawequal")(bar.rawValue, state.power)
    assert decode(plugin, pixels(plugin, bar.fill)) == 1.5
    assert plugin.regions == regions
    assert len(state.frames) == frame_count
    state.tick(state, 10)
    assert state.powerCalls == 2


def test_fractional_fallbacks_are_float_and_can_match_upper_bound() -> None:
    plugin = create()
    allocate([plugin])
    decoder = pixels(plugin, 0.3)
    _, bars, _ = plugin.raw_value(decoder)
    assert type(plugin.fallback_value()) is float
    results = [plugin.value([], [], [], decoder=decoder), plugin.value([], bars * 2, [], decoder=decoder)]
    with patch.object(ValueBar, "ratio", new_callable=PropertyMock, side_effect=ValueError("畸形输入")):
        results.append(plugin.value([], bars, [], decoder=decoder))
    for result in results:
        assert type(result) is float
        assert result == 0.0
        expression = parse_expression("灵魂碎片 <= 4", {"灵魂碎片": plugin.output})
        assert evaluate(expression, {"灵魂碎片": result}) is True


@pytest.mark.parametrize("damage,expected", [("all_gray", 0.0), ("all_red", 0.0), ("missing_separator", 1.4), ("outer_rows", 1.5), ("colored_content", 1.6)])
def test_malformed_pixels_follow_existing_valuebar_counting(damage: str, expected: float) -> None:
    plugin = create()
    allocate([plugin])
    image = np.zeros((4, 104, 3), dtype=np.uint8)
    image[:, :2] = [255, 0, 0]
    image[:, -2:] = [255, 0, 0]
    image[:, 2:32] = 255
    if damage == "all_gray":
        image[:] = 127
    elif damage == "all_red":
        image[:] = [255, 0, 0]
    elif damage == "missing_separator":
        image[:, :2] = 0
        image[:, -2:] = 0
    elif damage == "outer_rows":
        image[0] = 127
        image[-1] = 127
    else:
        image[:, 32:36] = [0, 255, 0]
    decoder = pixels(plugin, 0)
    result = plugin.value([], [ValueBar(1, 25, image)], [], decoder=decoder)
    assert type(result) is float
    assert result == expected


@pytest.mark.parametrize("fractional", [False, True])
def test_rotation_default_writeback_keeps_width_derived(tmp_path: Path, fractional: bool) -> None:
    path = tmp_path / "soul-shards.toml"
    source = (ROOT / "tests/fixtures/rotation-validation.toml").read_text(encoding="utf-8")
    # 仅替换临时配置的条件，保留现有 fixture 的公共 schema 和宏配置。
    prefix = source.split("[[conditions]]", 1)[0]
    suffix = "[[macros]]" + source.split("[[macros]]", 1)[1]
    suffix = suffix.replace("符文数量>=1", "灵魂碎片>=1.5").replace("符文能量>=40", "灵魂碎片<=4")
    argument = "\n[conditions.plugin_args]\nfractional = true\n" if fractional else "\n"
    path.write_text(prefix + '[[conditions]]\ntitle = "灵魂碎片"\nplugin = "spec_power_soul_shards@dev"\n' + argument + suffix, encoding="utf-8")
    rotation = load_rotation(path)
    text = path.read_text(encoding="utf-8")
    assert "width" not in text
    assert f"fractional = {str(fractional).lower()}" in text
    assert dict(create().config_defaults) == {"fractional": False}
    assert rotation.conditions[0].instance.output.widths == ((25,) if fractional else ())
