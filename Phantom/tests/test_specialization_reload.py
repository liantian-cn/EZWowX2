from pathlib import Path
from typing import Any

import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

SOURCE = Path(__file__).resolve().parents[1] / "phantom/lua/runtime/14_specialization_reload.lua"


def reload_harness(initial_spec: int | None) -> tuple[Any, Any]:
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state: Any = lua.execute("""
        local state = {frames={}, shown={}, reloads=0}
        C_SpecializationInfo = {GetSpecialization=function() return state.spec end}
        StaticPopupDialogs = {}
        StaticPopup_Show = function(name)
            table.insert(state.shown, name)
            state.visible = name
        end
        ReloadUI = function() state.reloads = state.reloads + 1 end
        CreateFrame = function(kind)
            assert(kind == "Frame")
            local frame = {events={}, scripts={}}
            function frame:RegisterEvent(event) self.events[event] = true end
            function frame:SetScript(name, callback) self.scripts[name] = callback end
            table.insert(state.frames, frame)
            return frame
        end
        function state:event(event)
            for _, frame in ipairs(self.frames) do
                if frame.events[event] then frame.scripts.OnEvent(frame, event) end
            end
        end
        function state:accept()
            StaticPopupDialogs[self.visible].OnAccept()
        end
        state.dialogs = StaticPopupDialogs
        return state
    """)
    state.spec = initial_spec
    execute: Any = lua.eval("function(source) assert(loadstring(source))('TestPhantom', {}) end")
    execute(SOURCE.read_text(encoding="utf-8"))
    return lua, state


@pytest.mark.parametrize("initial_spec", [1, 2, 3, 4])
def test_login_and_reload_same_specialization_do_not_prompt(initial_spec: int) -> None:
    _, state = reload_harness(initial_spec)
    for event in ("PLAYER_ENTERING_WORLD", "ACTIVE_PLAYER_SPECIALIZATION_CHANGED", "ACTIVE_PLAYER_SPECIALIZATION_CHANGED"):
        state.event(state, event)
    assert len(state.shown) == state.reloads == 0


def test_nil_initialization_waits_for_first_valid_specialization() -> None:
    _, state = reload_harness(None)
    state.event(state, "ACTIVE_PLAYER_SPECIALIZATION_CHANGED")
    state.spec = 2
    state.event(state, "ACTIVE_PLAYER_SPECIALIZATION_CHANGED")
    state.spec = None
    state.event(state, "ACTIVE_PLAYER_SPECIALIZATION_CHANGED")
    state.spec = 2
    state.event(state, "ACTIVE_PLAYER_SPECIALIZATION_CHANGED")
    assert len(state.shown) == state.reloads == 0
    state.spec = 3
    state.event(state, "ACTIVE_PLAYER_SPECIALIZATION_CHANGED")
    assert len(state.shown) == 1


def test_first_event_real_change_prompts_once_without_automatic_reload() -> None:
    _, state = reload_harness(1)
    state.spec = 2
    state.event(state, "PLAYER_ENTERING_WORLD")
    state.event(state, "ACTIVE_PLAYER_SPECIALIZATION_CHANGED")
    assert len(state.shown) == 1
    state.visible = None
    for spec in (2, None, 1, 3, 2):
        state.spec = spec
        state.event(state, "ACTIVE_PLAYER_SPECIALIZATION_CHANGED")
    assert len(state.shown) == 1
    assert state.reloads == 0
    assert len(state.frames) == 1
    assert state.frames[1].scripts.OnUpdate is None


def test_popup_has_only_reload_confirmation_and_accept_calls_reload() -> None:
    _, state = reload_harness(1)
    state.spec = 2
    state.event(state, "ACTIVE_PLAYER_SPECIALIZATION_CHANGED")
    dialog = state.dialogs[state.visible]
    assert dialog.button1 == "重载界面"
    assert dialog.button2 is None and dialog.button3 is None
    assert dialog.OnCancel is None
    assert dialog.hideOnEscape is False
    assert dialog.closeButton is False
    assert dialog.timeout == 0
    assert dialog.whileDead is True
    assert state.reloads == 0
    state.accept(state)
    assert state.reloads == 1
    _, after_reload = reload_harness(2)
    after_reload.event(after_reload, "ACTIVE_PLAYER_SPECIALIZATION_CHANGED")
    assert len(after_reload.shown) == after_reload.reloads == 0
