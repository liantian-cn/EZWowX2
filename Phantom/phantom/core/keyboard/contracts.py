"""
Summary:
    定义与发送方式无关的键盘按键组合。
Description:
    内核解析配置后传递明确的按键标识；后端负责设备编码、目标选择和完整按下释放。
Key Variables:
    KeyCombination.keys: 按下顺序，修饰键在前，主键在后。
Change Log:
    2026-09-20: Changed 修饰键契约仅支持 RCTRL、RALT、RSHIFT。
    2026-09-14: Added 第 14–17 步键盘插件公共契约。
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class Key(StrEnum):
    RCTRL = "RCTRL"
    RALT = "RALT"
    RSHIFT = "RSHIFT"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    LETTER_I = "I"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    LETTER_O = "O"
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"
    DIGIT0 = "0"
    DIGIT1 = "1"
    DIGIT2 = "2"
    DIGIT3 = "3"
    DIGIT4 = "4"
    DIGIT5 = "5"
    DIGIT6 = "6"
    DIGIT7 = "7"
    DIGIT8 = "8"
    DIGIT9 = "9"
    F1 = "F1"
    F2 = "F2"
    F3 = "F3"
    F4 = "F4"
    F5 = "F5"
    F6 = "F6"
    F7 = "F7"
    F8 = "F8"
    F9 = "F9"
    F10 = "F10"
    F11 = "F11"
    F12 = "F12"
    F13 = "F13"
    F14 = "F14"
    F15 = "F15"
    F16 = "F16"
    F17 = "F17"
    F18 = "F18"
    F19 = "F19"
    F20 = "F20"
    F21 = "F21"
    F22 = "F22"
    F23 = "F23"
    F24 = "F24"
    NUMPAD0 = "NUMPAD0"
    NUMPAD1 = "NUMPAD1"
    NUMPAD2 = "NUMPAD2"
    NUMPAD3 = "NUMPAD3"
    NUMPAD4 = "NUMPAD4"
    NUMPAD5 = "NUMPAD5"
    NUMPAD6 = "NUMPAD6"
    NUMPAD7 = "NUMPAD7"
    NUMPAD8 = "NUMPAD8"
    NUMPAD9 = "NUMPAD9"
    NUMPADPLUS = "NUMPADPLUS"
    NUMPADMINUS = "NUMPADMINUS"
    NUMPADMULTIPLY = "NUMPADMULTIPLY"
    NUMPADDIVIDE = "NUMPADDIVIDE"
    NUMPADDECIMAL = "NUMPADDECIMAL"
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    HOME = "HOME"
    END = "END"
    PAGEUP = "PAGEUP"
    PAGEDOWN = "PAGEDOWN"
    INSERT = "INSERT"
    DELETE = "DELETE"
    SPACE = "SPACE"
    TAB = "TAB"
    ENTER = "ENTER"
    ESCAPE = "ESCAPE"
    BACKSPACE = "BACKSPACE"
    COMMA = ","
    PERIOD = "."
    SLASH = "/"
    SEMICOLON = ";"
    QUOTE = "'"
    LEFTBRACKET = "["
    RIGHTBRACKET = "]"
    BACKSLASH = "\\"
    EQUALS = "="
    MINUS = "-"
    GRAVE = "`"


MODIFIERS: frozenset[Key] = frozenset((Key.RCTRL, Key.RALT, Key.RSHIFT))


@dataclass(frozen=True)
class KeyCombination:
    keys: tuple[Key, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.keys, tuple)
            or not self.keys
            or any(not isinstance(key, Key) for key in self.keys)
            or self.keys[-1] in MODIFIERS
            or any(key not in MODIFIERS for key in self.keys[:-1])
            or len(set(self.keys)) != len(self.keys)
        ):
            raise ValueError("组合键需要唯一修饰键及一个主键")


def parse_key(source: str) -> KeyCombination:
    remaining = source
    keys: list[Key] = []
    # 只剥离修饰键前缀，保留主键 '-' 本身，例如 RCTRL--。
    while True:
        prefix, separator, tail = remaining.partition("-")
        if separator and prefix in MODIFIERS:
            keys.append(Key(prefix))
            remaining = tail
        else:
            break
    try:
        keys.append(Key(remaining))
        return KeyCombination(tuple(keys))
    except ValueError as error:
        raise ValueError(f"非法或不支持的 WoW 键位：{source}") from error


class Keyboard(Protocol):
    def send(self, keys: KeyCombination) -> None: ...

    def close(self) -> None: ...
