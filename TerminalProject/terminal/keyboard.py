import ctypes
import time
from typing import Any, TypedDict

from win32gui import EnumWindows, GetWindowText


WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101


class WindowRecord(TypedDict):
    hwnd: int
    title: str


VK_DICT = {
    "SHIFT": 0x10, "CTRL": 0x11, "ALT": 0x12,
    "NUMPAD0": 0x60, "NUMPAD1": 0x61, "NUMPAD2": 0x62,    "NUMPAD3": 0x63, "NUMPAD4": 0x64,
    "NUMPAD5": 0x65,    "NUMPAD6": 0x66, "NUMPAD7": 0x67, "NUMPAD8": 0x68,    "NUMPAD9": 0x69,
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
    "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    ",": 0xBC, ".": 0xBE, "/": 0xBF, ";": 0xBA, "'": 0xDE,
    "[": 0xDB, "]": 0xDD, "=": 0xBB, "-": 0xBD, "`": 0xC0,
}

MOD_MAP = {
    "CTRL": 0x0002, "CONTROL": 0x0002,
    "SHIFT": 0x0004, "ALT": 0x0001,
}


def press_key_hwnd(hwnd: int, skey: str) -> None:
    key = VK_DICT.get(skey)
    if key is None:
        raise KeyError(f"Virtual key '{skey}' not found")
    ctypes.windll.user32.PostMessageW(hwnd, WM_KEYDOWN, key, 0)


def release_key_hwnd(hwnd: int, skey: str) -> None:
    key = VK_DICT.get(skey)
    if key is None:
        raise KeyError(f"Virtual key '{skey}' not found")
    ctypes.windll.user32.PostMessageW(hwnd, WM_KEYUP, key, 0)


def send_hot_key(hwnd: int, hot_key: str) -> None:
    key_list = hot_key.split("-")
    for skey in key_list:
        press_key_hwnd(hwnd, skey)
    time.sleep(0.01)
    for skey in reversed(key_list):
        release_key_hwnd(hwnd, skey)


def get_windows_by_title() -> list[WindowRecord]:
    windows: list[WindowRecord] = []

    def enum_callback(hwnd: int, _: Any) -> None:
        title = GetWindowText(hwnd)
        if not title:
            return
        if "魔兽世界".lower() not in title.lower():
            return
        windows.append({"hwnd": hwnd, "title": title})

    EnumWindows(enum_callback, None)
    return windows
