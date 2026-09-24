"""使用真实 Lua 背板、组件与画布验证几何、计数及静态分层契约。"""

from pathlib import Path
from typing import Any

import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.registry import Registry
from tests.test_aura_migration_conditions import harness

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "phantom/lua/runtime"


@pytest.mark.parametrize("cell_size", [4, 8, 2.5])
def test_backplate_geometry_composition_and_single_accounting(cell_size: float) -> None:
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state, addon = lua.execute((ROOT / "tests/lua/player_conditions_harness.lua").read_text(encoding="utf-8"))
    lua.execute(
        """
        local state, addon, cellSize = ...
        max = math.max
        addon.SCALE = 1
        addon.GetUIScaleFactor = function(value) return value * cellSize / 4 end
        CreateColor = function(r, g, b, a)
            return {value = r, GetRGBA = function() return r, g, b, a end}
        end
        local original = CreateFrame
        CreateFrame = function(...)
            local frame = original(...)
            function frame:SetColorFill(...) self.fillColor = {...} end
            function frame:SetReverseFill(value) self.reverse = value end
            local createTexture = frame.CreateTexture
            function frame:CreateTexture(...)
                local texture = createTexture(self, ...)
                function texture:SetSize(w, h) self.width = w; self.height = h end
                function texture:SetPoint(...) self.point = {...} end
                return texture
            end
            return frame
        end
        """,
        state,
        addon,
        cell_size,
    )
    execute: Any = lua.eval("function(source, addon) assert(loadstring(source))('PhantomTest', addon) end")
    for name in ("04_baseline_definition.lua", "05_background.lua"):
        execute((RUNTIME / name).read_text(encoding="utf-8"), addon)
    lua.execute(
        """
        local state, addon = ...
        local resize = addon.BackgroundFrameResize
        state.resizeCalls = 0
        addon.BackgroundFrameResize = function()
            state.resizeCalls = state.resizeCalls + 1
            resize()
        end
        """,
        state,
        addon,
    )
    for name in ("07_cell_backplate.lua", "08_cell.lua", "09_value_bar_backplate.lua", "10_value_bar.lua", "11_icon_tile_backplate.lua", "12_icon_tile.lua", "13_mask.lua"):
        execute((RUNTIME / name).read_text(encoding="utf-8"), addon)
    state.initialize(state)
    lua.execute((ROOT / "tests/lua/backplates_contract.lua").read_text(encoding="utf-8"), state, addon, cell_size)


def test_all_seventeen_borrowers_construct_only_backplates_and_owned_content() -> None:
    arguments: dict[str, dict[str, object]] = {
        "player_damage_absorb": {"threshold": 0},
        "player_heal_absorb": {"threshold": 0},
        "player_has_buff": {"buff_ids": [100]},
        "player_has_big_defensive": {},
        "player_has_dispellable_debuff": {"dispel_types": {}},
        "target_has_buff": {"aura_ids": [100]},
        "target_has_debuff": {"aura_ids": [100]},
        "target_has_dispellable_buff": {"dispel_types": {}},
        "focus_has_buff": {"aura_ids": [100]},
        "focus_has_debuff": {"aura_ids": [100]},
        "focus_has_dispellable_buff": {"dispel_types": {}},
        "aura_player_buff_duration": {"aura_ids": [100], "duration": 12},
        "aura_player_buff_duration_pct": {"aura_ids": [100]},
        "aura_player_buff_stacks": {"aura_ids": [100], "max_value": 5},
        "aura_target_debuff_duration": {"aura_ids": [100], "duration": 12},
        "aura_target_debuff_duration_pct": {"aura_ids": [100]},
        "aura_target_debuff_stacks": {"aura_ids": [100], "max_value": 5},
    }
    plugins = [Registry().create(f"{name}@dev", args) for name, args in arguments.items()]
    lua, state, addon = harness(plugins)
    state.enemy = True
    state.initialize(state)
    assert addon.ConditionCellLength == 11
    assert addon.ValueBarLength == sum(plugin.output.widths[0] + 1 for plugin in plugins if plugin.output.output_type == "value_bar")
    lua.execute(
        """
        local state, addon = ...
        local cells, containers, bars, separators = 0, 0, 0, 0
        for _, frame in ipairs(state.frames) do
            if frame.name and frame.name:match("Cell_%d+_2$") then
                cells = cells + 1
                assert(frame.parent == addon.BackgroundFrame and frame.level == addon.FrameLevel.Backplate)
                assert(#frame.textures == 1 and frame.textures[1].layer == "BACKGROUND" and frame.textures[1].r == 0)
            elseif frame.name and frame.name:match("separatorFrame$") then
                separators = separators + 1
                assert(frame.parent == addon.BackgroundFrame and frame.level == addon.FrameLevel.Separator)
            elseif frame.kind == "AuraContainer" then
                containers = containers + 1
                assert(frame.parent.parent == addon.BackgroundFrame)
                assert(frame.parent.level == addon.FrameLevel.Backplate and frame.level == addon.FrameLevel.AuraContainer)
                assert(#frame.parent.children == 1) -- 没有无用的默认半满条。
                for _, slot in pairs(frame.slots) do
                    assert(slot.button.parent == frame and slot.button.level == addon.FrameLevel.AuraButton)
                end
            elseif frame.kind == "StatusBar" then
                bars = bars + 1
                if frame.parent.kind == "AuraButton" then
                    assert(frame.level == addon.FrameLevel.AuraContent)
                    assert(frame.parent.parent.kind == "AuraContainer")
                    assert(frame.fill == nil) -- 只交给官方 consumer，不设置普通默认值。
                    assert(#frame.textures == 1 and frame.textures[1].layer == "BACKGROUND")
                else
                    assert(frame.level == addon.FrameLevel.Content and frame.parent.level == addon.FrameLevel.Backplate)
                end
            end
        end
        assert(cells == 11 and containers == 15 and bars == 8 and separators == 6)
        """,
        state,
        addon,
    )
