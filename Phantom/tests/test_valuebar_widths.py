from pathlib import Path
from typing import Any

import numpy as np
import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.pixels import PixelDecoder

ROOT = Path(__file__).resolve().parents[1]
PLUGINS: dict[str, tuple[str, str]] = {"aura_player_buff_duration": ("aura_ids", "duration"), "aura_target_debuff_duration": ("aura_ids", "duration"), "spell_charges": ("spell_ids", "max_charges")}
INVALID_INTEGER_VALUES: tuple[object, ...] = (True, False, 0, -1, 1.0, 1.5, "2", None, [], {}, float("inf"), float("nan"))


@pytest.mark.parametrize("name", [name for name in PLUGINS if name.endswith("duration")])
@pytest.mark.parametrize("duration,expected", [(1, 1), (4, 1), (5, 2), (12, 3), (29, 8), (32, 8), (40, 8)])
def test_duration_default_width(name: str, duration: int, expected: int) -> None:
    args: dict[str, object] = {"aura_ids": [100], "duration": duration}
    plugin = Registry().create(f"{name}@dev", args)
    assert plugin.output.widths == (expected,)
    assert "width" not in args
    assert "width" not in plugin.config_defaults


@pytest.mark.parametrize("duration,expected", [(0.1, 1), (1.0, 1), (4.0001, 2), (13.5, 4), (30, 8), (1e308, 8), (5e-324, 1)])
def test_player_duration_accepts_finite_positive_numbers(duration: float, expected: int) -> None:
    plugin = Registry().create("aura_player_buff_duration@dev", {"aura_ids": [100], "duration": duration})
    assert plugin.output.widths == (expected,)
    assert "width" not in plugin.config_defaults


@pytest.mark.parametrize("maximum,expected", [(1, 1), (2, 1), (3, 2), (4, 2), (17, 9), (49, 25)])
def test_charges_default_width_has_no_cap(maximum: int, expected: int) -> None:
    args: dict[str, object] = {"spell_ids": [100], "max_charges": maximum}
    plugin = Registry().create("spell_charges@dev", args)
    assert plugin.output.widths == (expected,)
    assert "width" not in args
    assert "width" not in plugin.config_defaults


@pytest.mark.parametrize("name", PLUGINS)
@pytest.mark.parametrize("width", [1, 3, 12, 25])
@pytest.mark.parametrize("quarter", [0, 1, 2, 3, 4])
def test_explicit_width_preserves_decoding(name: str, width: int, quarter: int) -> None:
    ids, scale = PLUGINS[name]
    plugin = Registry().create(f"{name}@dev", {ids: [100], scale: 12, "width": width})
    assert plugin.output.widths == (width,)
    board_width = allocate([plugin])
    region = plugin.regions[0]
    pixels = np.zeros((20, board_width, 3), dtype=np.uint8)
    start = region.x * 4
    pixels[8:12, start : start + (width + 1) * 4] = [255, 0, 0]
    pixels[8:12, start + 2 : start + 2 + width * 4] = 0
    pixels[8:12, start + 2 : start + 2 + width * quarter] = 255
    decoder = PixelDecoder(pixels)
    result = plugin.value(*plugin.raw_value(decoder), decoder=decoder)
    assert result == quarter * 3
    assert type(result) is (int if name == "spell_charges" else float)
    assert plugin.value([], [], [], decoder=decoder) == plugin.fallback_value()


@pytest.mark.parametrize(
    "name,field,bad", [(name, field, bad) for name in PLUGINS for field in ("width", "scale") for bad in INVALID_INTEGER_VALUES if not (name == "aura_player_buff_duration" and field == "scale" and type(bad) is float and bad in (1.0, 1.5))]
)
def test_width_and_scale_require_positive_integers(name: str, field: str, bad: object) -> None:
    ids, scale = PLUGINS[name]
    args: dict[str, object] = {ids: [100], scale: 12}
    args[scale if field == "scale" else field] = bad
    with pytest.raises(ValueError, match=scale if field == "scale" else "width"):
        Registry().create(f"{name}@dev", args)


@pytest.mark.parametrize("bad", [True, False, 0, -1, "13.5", None, [], {}, float("inf"), float("-inf"), float("nan"), 10**400])
def test_player_duration_rejects_invalid_positive_number(bad: object) -> None:
    with pytest.raises(ValueError, match="duration"):
        Registry().create("aura_player_buff_duration@dev", {"aura_ids": [100], "duration": bad})


@pytest.mark.parametrize("aura_id,duration,width", [(195181, 30, 8), (132403, 13.5, 4), (188370, 4, 2)])
def test_player_duration_configurations_decode_full_valuebar(aura_id: int, duration: float, width: int) -> None:
    plugin = Registry().create("aura_player_buff_duration@dev", {"aura_ids": [aura_id], "duration": duration, "width": width})
    board_width = allocate([plugin])
    start = plugin.regions[0].x * 4
    # 合成全部条宽的离散位置；奉献 width=2 时逐一覆盖 k=0..8，对应每格0.5秒。
    for columns in range(width * 4 + 1):
        pixels = np.zeros((20, board_width, 3), dtype=np.uint8)
        pixels[8:12, start : start + (width + 1) * 4] = [255, 0, 0]
        pixels[8:12, start + 2 : start + 2 + width * 4] = 0
        pixels[8:12, start + 2 : start + 2 + columns] = 255
        decoder = PixelDecoder(pixels)
        result = plugin.value(*plugin.raw_value(decoder), decoder=decoder)
        assert type(result) is float
        assert result == pytest.approx(columns * duration / (width * 4))
        if aura_id == 188370:
            assert result == columns * 0.5


# 复用显示替身和真实 ValueBar；秘密充能值只允许由替身显示消费者读取。
CHARGES_EXTENSION = """
local state, addon = ...
addon.ValueBarLength = 0
addon.COLOR.RED = {GetRGBA = function() return 1, 0, 0, 1 end}
local original = CreateFrame
CreateFrame = function(...)
    local frame = original(...)
    function frame:SetColorFill(...) self.fillColor = {...} end
    return frame
end
C_Spell.GetSpellCharges = function(id)
    assert(id == 200)
    return state.charges
end
state.spellbook[200] = true
"""


@pytest.mark.parametrize("maximum,width,expected_width", [(2, None, 1), (3, None, 2), (3, 1, 1), (3, 25, 25)])
def test_charges_lua_keeps_business_range_independent(maximum: int, width: int | None, expected_width: int) -> None:
    args: dict[str, object] = {"spell_ids": [100, 200], "max_charges": maximum}
    if width is not None:
        args["width"] = width
    plugin = Registry().create("spell_charges@dev", args)
    allocate([plugin])
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state, addon = lua.execute((ROOT / "tests/lua/player_conditions_harness.lua").read_text(encoding="utf-8"))
    lua.execute(CHARGES_EXTENSION, state, addon)
    execute: Any = lua.eval("function(source, addon) assert(loadstring(source))('PhantomTest', addon) end")
    execute((ROOT / "phantom/lua/runtime/09_value_bar_backplate.lua").read_text(encoding="utf-8"), addon)
    execute((ROOT / "phantom/lua/runtime/10_value_bar.lua").read_text(encoding="utf-8"), addon)
    execute(plugin.generate_lua("charges-width"), addon)
    state.event(state, "SPELL_UPDATE_CHARGES")
    state.flushTimers(state)
    state.initialize(state)
    bar = next(frame for frame in state.frames.values() if frame.kind == "StatusBar")
    assert bar.parent.width == expected_width * 4
    assert addon.ValueBarLength == expected_width + 1
    assert (bar.low, bar.high, bar.fill) == (0, maximum, 0)
    for charges in range(maximum + 1):
        # API 实际上限故意不同，确保插件继续使用配置的业务量程。
        state.charges = lua.table_from({"currentCharges": state.secret(state, charges), "maxCharges": maximum + 7})
        state.event(state, "SPELL_UPDATE_CHARGES")
        state.flushTimers(state)
        assert bar.fill == pytest.approx(charges / maximum)
        assert lua.eval("function(a, b) return rawequal(a, b) end")(bar.rawValue, state.charges.currentCharges)
    state.charges = None
    state.event(state, "SPELL_UPDATE_USES")
    state.flushTimers(state)
    assert bar.fill == 0
    state.spellbook[200] = False
    state.event(state, "SPELLS_CHANGED")
    state.flushTimers(state)
    assert bar.fill == 0
