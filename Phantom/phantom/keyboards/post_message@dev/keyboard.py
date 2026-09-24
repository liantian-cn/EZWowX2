"""
Summary:
    将明确的按键组合发送到标题恰好为魔兽世界的唯一窗口。
Description:
    PostMessageW 普通按键消息携带扫描码、扩展位及按下/释放状态，按住 10 ms。
    目标发现和 Windows 虚拟键映射属于本插件；核心不传入 HWND 或宏文本。
    API 成功表示消息已入队，不保证游戏已经执行。中途失败仍尝试释放已按下的键。
Key Variables:
    VIRTUAL_KEYS: 中立按键标识到 Windows 虚拟键的映射。
    FIXED_SCAN_CODES: 右修饰键、导航区和数字小键盘的明确扫描码，含 E0 扩展前缀。
Change Log:
    2026-09-20: Changed 使用通用修饰 VK 配合右侧扫描码，完整构造消息 lParam。
    2026-09-14: Added 第一个版本化键盘后端，参考 EZWowX2 Terminal/terminal/keyboard.py。
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from time import sleep

from phantom.core.keyboard.contracts import Key, KeyCombination

VIRTUAL_KEYS: dict[Key, int] = {
    Key.RCTRL: 0x11,
    Key.RALT: 0x12,
    Key.RSHIFT: 0x10,
    Key.UP: 0x26,
    Key.DOWN: 0x28,
    Key.LEFT: 0x25,
    Key.RIGHT: 0x27,
    Key.HOME: 0x24,
    Key.END: 0x23,
    Key.PAGEUP: 0x21,
    Key.PAGEDOWN: 0x22,
    Key.INSERT: 0x2D,
    Key.DELETE: 0x2E,
    Key.SPACE: 0x20,
    Key.TAB: 0x09,
    Key.ENTER: 0x0D,
    Key.ESCAPE: 0x1B,
    Key.BACKSPACE: 0x08,
    Key.NUMPADPLUS: 0x6B,
    Key.NUMPADMINUS: 0x6D,
    Key.NUMPADMULTIPLY: 0x6A,
    Key.NUMPADDIVIDE: 0x6F,
    Key.NUMPADDECIMAL: 0x6E,
    Key.COMMA: 0xBC,
    Key.PERIOD: 0xBE,
    Key.SLASH: 0xBF,
    Key.SEMICOLON: 0xBA,
    Key.QUOTE: 0xDE,
    Key.LEFTBRACKET: 0xDB,
    Key.RIGHTBRACKET: 0xDD,
    Key.BACKSLASH: 0xDC,
    Key.EQUALS: 0xBB,
    Key.MINUS: 0xBD,
    Key.GRAVE: 0xC0,
}
VIRTUAL_KEYS.update({Key(character): ord(character) for character in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"})
VIRTUAL_KEYS.update({Key(f"F{number}"): 0x6F + number for number in range(1, 25)})
VIRTUAL_KEYS.update({Key(f"NUMPAD{number}"): 0x60 + number for number in range(10)})

FIXED_SCAN_CODES: dict[Key, int] = {
    Key.RCTRL: 0xE01D,
    Key.RALT: 0xE038,
    Key.RSHIFT: 0x36,
    Key.UP: 0xE048,
    Key.DOWN: 0xE050,
    Key.LEFT: 0xE04B,
    Key.RIGHT: 0xE04D,
    Key.HOME: 0xE047,
    Key.END: 0xE04F,
    Key.PAGEUP: 0xE049,
    Key.PAGEDOWN: 0xE051,
    Key.INSERT: 0xE052,
    Key.DELETE: 0xE053,
    Key.NUMPAD0: 0x52,
    Key.NUMPAD1: 0x4F,
    Key.NUMPAD2: 0x50,
    Key.NUMPAD3: 0x51,
    Key.NUMPAD4: 0x4B,
    Key.NUMPAD5: 0x4C,
    Key.NUMPAD6: 0x4D,
    Key.NUMPAD7: 0x47,
    Key.NUMPAD8: 0x48,
    Key.NUMPAD9: 0x49,
    Key.NUMPADPLUS: 0x4E,
    Key.NUMPADMINUS: 0x4A,
    Key.NUMPADMULTIPLY: 0x37,
    Key.NUMPADDIVIDE: 0xE035,
    Key.NUMPADDECIMAL: 0x53,
}


class WindowsMessages:
    def __init__(self) -> None:
        if sys.platform != "win32":
            raise OSError("PostMessageW 需要 Windows")
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows.argtypes = [self.callback_type, wintypes.LPARAM]
        self.user32.EnumWindows.restype = wintypes.BOOL
        self.user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        self.user32.GetWindowTextLengthW.restype = ctypes.c_int
        self.user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self.user32.GetWindowTextW.restype = ctypes.c_int
        self.user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        self.user32.PostMessageW.restype = wintypes.BOOL
        self.user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
        self.user32.MapVirtualKeyW.restype = wintypes.UINT

    def target(self) -> int:
        matches: list[int] = []

        def visit(hwnd: int, parameter: int) -> bool:
            length = self.user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, buffer, len(buffer))
            if buffer.value == "魔兽世界":
                matches.append(hwnd)
            return True

        if not self.user32.EnumWindows(self.callback_type(visit), 0):
            raise ctypes.WinError(ctypes.get_last_error())
        if len(matches) != 1:
            raise OSError(f"标题为“魔兽世界”的窗口必须唯一，实际找到 {len(matches)} 个")
        return matches[0]

    def down_lparam(self, key: Key) -> int:
        scan_code = FIXED_SCAN_CODES.get(key)
        if scan_code is None:
            # 其余主键按当前键盘布局转换；导航区和小键盘显式区分，避免映射丢失 E0。
            scan_code = int(self.user32.MapVirtualKeyW(VIRTUAL_KEYS[key], 4))
        if not scan_code or scan_code & 0xFF00 not in (0, 0xE000):
            raise OSError(f"无法映射按键扫描码：{key}")
        # 重复计数为 1；普通 KEY 消息的上下文位及首次按下的状态位均为 0。
        return 1 | ((scan_code & 0xFF) << 16) | (int(bool(scan_code & 0xE000)) << 24)

    def post(self, hwnd: int, message: int, key: int, lparam: int) -> None:
        if not self.user32.PostMessageW(hwnd, message, key, lparam):
            raise ctypes.WinError(ctypes.get_last_error())


class Plugin:
    def __init__(self) -> None:
        self._messages: WindowsMessages | None = None

    def send(self, keys: KeyCombination) -> None:
        if self._messages is None:
            self._messages = WindowsMessages()
        target = self._messages.target()
        pressed: list[tuple[int, int]] = []
        failure: Exception | None = None
        try:
            for key in keys.keys:
                virtual_key = VIRTUAL_KEYS[key]
                lparam = self._messages.down_lparam(key)
                self._messages.post(target, 0x0100, virtual_key, lparam)
                pressed.append((virtual_key, lparam))
            sleep(0.01)
        except Exception as error:
            failure = error
        finally:
            for virtual_key, lparam in reversed(pressed):
                try:
                    # 释放沿用按下时的扫描码，并设置 previous-state 与 transition 位。
                    self._messages.post(target, 0x0101, virtual_key, lparam | 0xC0000000)
                except Exception as error:
                    if failure is None:
                        failure = error
                    else:
                        failure.add_note(f"释放键 {virtual_key} 失败：{error}")
        if failure is not None:
            raise failure

    def close(self) -> None:
        # send 始终完成释放尝试；本后端不拥有目标窗口或持续按键状态。
        self._messages = None
