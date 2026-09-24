from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from phantom.core.configuration import load_config
from phantom.core.keyboard.contracts import Key, parse_key
from phantom.core.keyboard.registry import KeyboardPluginError, Registry


def backend_module() -> ModuleType:
    plugin = Registry().create()
    return sys.modules[type(plugin).__module__]


@pytest.mark.parametrize(
    ("source", "keys"),
    [
        ("RCTRL-1", (Key.RCTRL, Key.DIGIT1)),
        ("RALT-F4", (Key.RALT, Key.F4)),
        ("RSHIFT-RCTRL-NUMPAD1", (Key.RSHIFT, Key.RCTRL, Key.NUMPAD1)),
        ("RCTRL--", (Key.RCTRL, Key.MINUS)),
        ("-", (Key.MINUS,)),
        ("F24", (Key.F24,)),
        ("RCTRL-;", (Key.RCTRL, Key.SEMICOLON)),
        ("NUMPADPLUS", (Key.NUMPADPLUS,)),
    ],
)
def test_key_combinations(source: str, keys: tuple[Key, ...]) -> None:
    assert parse_key(source).keys == keys


@pytest.mark.parametrize("source", ["", "rctrl-1", "RCTRL-RCTRL-A", "RCTRL", "RALT", "RSHIFT", "A-B", "F25", "RCTRL+1", "RCTRL-", "RALT--A", " M", "BUTTON1", "CTRL-A", "ALT-A", "SHIFT-A", "LCTRL-A", "LALT-A", "LSHIFT-A", "RCTRL-SHIFT-A"])
def test_invalid_keys(source: str) -> None:
    with pytest.raises(ValueError):
        parse_key(source)


@pytest.mark.parametrize("name", ["CTRL", "ALT", "SHIFT", "LCTRL", "LALT", "LSHIFT"])
def test_removed_modifier_enum_names(name: str) -> None:
    assert name not in Key.__members__
    with pytest.raises(ValueError):
        Key(name)


def test_windows_mapping_covers_every_key() -> None:
    mapping = backend_module().VIRTUAL_KEYS
    assert set(mapping) == set(Key)
    assert [mapping[key] for key in parse_key("RCTRL-RALT-RSHIFT-1").keys] == [0x11, 0x12, 0x10, 0x31]
    assert mapping[Key.F24] == 0x87
    assert mapping[Key.NUMPAD9] == 0x69
    assert mapping[Key.SEMICOLON] == 0xBA


class RecordingMessages:
    def __init__(self, fail_at: int | tuple[int, ...] = 0) -> None:
        self.calls: list[tuple[int, int, int, int]] = []
        self.fail_at: tuple[int, ...] = (fail_at,) if isinstance(fail_at, int) else fail_at
        message_type = backend_module().WindowsMessages
        self.encoder: Any = message_type.__new__(message_type)
        self.encoder.user32 = SimpleNamespace(MapVirtualKeyW=lambda key, mode: {0x73: 0x3E}.get(key, 0))

    def target(self) -> int:
        return 123

    def down_lparam(self, key: Key) -> int:
        return int(self.encoder.down_lparam(key))

    def post(self, hwnd: int, message: int, key: int, lparam: int) -> None:
        self.calls.append((hwnd, message, key, lparam))
        if len(self.calls) in self.fail_at:
            raise OSError("post failed")


@pytest.mark.parametrize("fail_at", [0, 2, 4])
def test_send_order_and_failure_release(monkeypatch: pytest.MonkeyPatch, fail_at: int) -> None:
    plugin = Registry().create()
    module = sys.modules[type(plugin).__module__]
    messages = RecordingMessages(fail_at)
    sleeps: list[float] = []
    monkeypatch.setattr(module, "WindowsMessages", lambda: messages)
    monkeypatch.setattr(module, "sleep", sleeps.append)
    if fail_at:
        with pytest.raises(OSError, match="post failed"):
            plugin.send(parse_key("RCTRL-RALT-F4"))
    else:
        plugin.send(parse_key("RCTRL-RALT-F4"))
    expected = [(123, 0x100, 0x11, 0x011D0001), (123, 0x100, 0x12, 0x01380001)]
    if fail_at == 2:
        expected += [(123, 0x101, 0x11, 0xC11D0001)]
        assert sleeps == []
    else:
        expected += [(123, 0x100, 0x73, 0x003E0001), (123, 0x101, 0x73, 0xC03E0001), (123, 0x101, 0x12, 0xC1380001), (123, 0x101, 0x11, 0xC11D0001)]
        assert sleeps == [0.01]
    assert messages.calls == expected
    plugin.close()


@pytest.mark.parametrize(
    ("key", "mapped_scan", "expected"),
    [
        (Key.RCTRL, 0, 0x011D0001),
        (Key.RALT, 0, 0x01380001),
        (Key.RSHIFT, 0, 0x00360001),
        (Key.NUMPAD1, 0, 0x004F0001),
        (Key.NUMPAD0, 0, 0x00520001),
        (Key.NUMPADDECIMAL, 0, 0x00530001),
        (Key.NUMPADDIVIDE, 0, 0x01350001),
        (Key.END, 0, 0x014F0001),
        (Key.INSERT, 0, 0x01520001),
        (Key.DELETE, 0, 0x01530001),
        (Key.SLASH, 0x35, 0x00350001),
        (Key.ENTER, 0x1C, 0x001C0001),
        (Key.SEMICOLON, 0x27, 0x00270001),
        (Key.F12, 0x58, 0x00580001),
    ],
)
def test_scan_code_and_extended_bit(key: Key, mapped_scan: int, expected: int) -> None:
    messages = RecordingMessages()
    calls: list[tuple[int, int]] = []

    def map_virtual_key(virtual_key: int, mode: int) -> int:
        calls.append((virtual_key, mode))
        return mapped_scan

    messages.encoder.user32.MapVirtualKeyW = map_virtual_key
    assert messages.down_lparam(key) == expected
    assert calls == ([(backend_module().VIRTUAL_KEYS[key], 4)] if mapped_scan else [])


def test_mapping_failure_releases_pressed_modifier(monkeypatch: pytest.MonkeyPatch) -> None:
    module = backend_module()
    messages = RecordingMessages()
    monkeypatch.setattr(module, "WindowsMessages", lambda: messages)
    sleeps: list[float] = []
    monkeypatch.setattr(module, "sleep", sleeps.append)
    with pytest.raises(OSError, match="无法映射按键扫描码"):
        module.Plugin().send(parse_key("RSHIFT-A"))
    assert messages.calls == [(123, 0x100, 0x10, 0x00360001), (123, 0x101, 0x10, 0xC0360001)]
    assert sleeps == []


def test_multiple_release_failures_keep_original_error(monkeypatch: pytest.MonkeyPatch) -> None:
    module = backend_module()
    messages = RecordingMessages((3, 4, 5))
    monkeypatch.setattr(module, "WindowsMessages", lambda: messages)
    with pytest.raises(OSError, match="post failed") as caught:
        module.Plugin().send(parse_key("RCTRL-RALT-F4"))
    assert messages.calls[-2:] == [(123, 0x101, 0x12, 0xC1380001), (123, 0x101, 0x11, 0xC11D0001)]
    assert caught.value.__notes__ == ["释放键 18 失败：post failed", "释放键 17 失败：post failed"]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows scan code mapping")
def test_windows_scan_mapping_covers_every_key() -> None:
    messages: Any = backend_module().WindowsMessages()
    for key in Key:
        lparam = messages.down_lparam(key)
        assert lparam & 0xFFFF == 1
        assert (lparam >> 16) & 0xFF
        assert lparam & 0xFE000000 == 0
    for navigation, numpad in [
        (Key.END, Key.NUMPAD1),
        (Key.DOWN, Key.NUMPAD2),
        (Key.PAGEDOWN, Key.NUMPAD3),
        (Key.LEFT, Key.NUMPAD4),
        (Key.RIGHT, Key.NUMPAD6),
        (Key.HOME, Key.NUMPAD7),
        (Key.UP, Key.NUMPAD8),
        (Key.PAGEUP, Key.NUMPAD9),
        (Key.INSERT, Key.NUMPAD0),
        (Key.DELETE, Key.NUMPADDECIMAL),
    ]:
        assert messages.down_lparam(navigation) == messages.down_lparam(numpad) | 0x01000000


@pytest.mark.skipif(sys.platform != "win32", reason="Windows API callback type")
@pytest.mark.parametrize("titles, expected", [(["魔兽世界"], 1), (["魔兽世界测试"], None), (["魔兽世界", "魔兽世界"], None)])
def test_target_requires_unique_exact_title(titles: list[str], expected: int | None) -> None:
    messages: Any = backend_module().WindowsMessages()

    class FakeUser32:
        def EnumWindows(self, callback: Any, parameter: int) -> bool:
            for index in range(len(titles)):
                callback(index + 1, parameter)
            return True

        def GetWindowTextLengthW(self, hwnd: int) -> int:
            return len(titles[hwnd - 1])

        def GetWindowTextW(self, hwnd: int, buffer: Any, length: int) -> int:
            buffer.value = titles[hwnd - 1]
            return len(buffer.value)

    messages.user32 = FakeUser32()
    if expected is None:
        with pytest.raises(OSError, match="必须唯一"):
            messages.target()
    else:
        assert messages.target() == expected


def test_registry_and_configuration(tmp_path: Path) -> None:
    registry = Registry()
    first, second = registry.create(), registry.create()
    assert first is not second and type(first) is type(second)
    for identifier in ("../bad", "x/y", "x\\y", "x:stream", "x.", "x ", "post_message@1", ""):
        with pytest.raises(KeyboardPluginError):
            registry.create(identifier)
    config = load_config(tmp_path)
    assert config.keyboard_plugin == "post_message@dev"
    config.path.write_text('[keyboard]\nplugin="other@dev"', encoding="utf-8")
    assert load_config(tmp_path).keyboard_plugin == "other@dev"
    with pytest.raises(KeyboardPluginError):
        registry.create(load_config(tmp_path).keyboard_plugin)


@pytest.mark.parametrize("source", ["Plugin = 0", "raise RuntimeError('broken')", "class Plugin:\n    pass", "class Plugin:\n    def send(self): pass\n    def close(self): pass"])
def test_invalid_plugin_interface(tmp_path: Path, source: str) -> None:
    directory = tmp_path / "broken@dev"
    directory.mkdir()
    (directory / "keyboard.py").write_text(source, encoding="utf-8")
    with pytest.raises(KeyboardPluginError, match="broken@dev"):
        Registry(tmp_path).create("broken@dev")


@pytest.mark.skipif(sys.platform != "win32", reason="real Windows message queue")
def test_real_post_message_to_owned_hidden_window(monkeypatch: pytest.MonkeyPatch) -> None:
    module = backend_module()
    messages: Any = module.WindowsMessages()
    user32 = messages.user32
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.restype = wintypes.BOOL
    user32.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
    user32.PeekMessageW.restype = wintypes.BOOL
    hwnd = user32.CreateWindowExW(0, "STATIC", "Phantom-test-" + uuid4().hex, 0, 0, 0, 1, 1, None, None, None, None)
    assert hwnd, ctypes.WinError(ctypes.get_last_error())
    try:
        # 仅向测试拥有的 HWND 发送，不枚举游戏窗口。
        monkeypatch.setattr(messages, "target", lambda: hwnd)
        monkeypatch.setattr(module, "WindowsMessages", lambda: messages)
        plugin: Any = module.Plugin()
        plugin.send(parse_key("RCTRL-1"))
        plugin.send(parse_key("RALT-F4"))
        plugin.send(parse_key("RSHIFT-NUMPAD1"))
        plugin.send(parse_key("END"))
        received: list[tuple[int, int, int]] = []
        message = wintypes.MSG()
        while user32.PeekMessageW(ctypes.byref(message), hwnd, 0x100, 0x101, 1):
            received.append((message.message, message.wParam, message.lParam & 0xFFFFFFFF))
        assert received == [
            (0x100, 0x11, 0x011D0001),
            (0x100, 0x31, 0x00020001),
            (0x101, 0x31, 0xC0020001),
            (0x101, 0x11, 0xC11D0001),
            (0x100, 0x12, 0x01380001),
            (0x100, 0x73, 0x003E0001),
            (0x101, 0x73, 0xC03E0001),
            (0x101, 0x12, 0xC1380001),
            (0x100, 0x10, 0x00360001),
            (0x100, 0x61, 0x004F0001),
            (0x101, 0x61, 0xC04F0001),
            (0x101, 0x10, 0xC0360001),
            (0x100, 0x23, 0x014F0001),
            (0x101, 0x23, 0xC14F0001),
        ]
        plugin.close()
    finally:
        assert user32.DestroyWindow(hwnd)
