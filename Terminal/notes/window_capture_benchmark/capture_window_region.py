from __future__ import annotations

import ctypes
from ctypes import wintypes

import numpy as np


user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

BI_RGB = 0
PW_RENDERFULLCONTENT = 0x00000002
CAPTURE_WIDTH = 336
CAPTURE_HEIGHT = 112
WINDOW_TITLE = "魔兽世界"


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
user32.PrintWindow.restype = wintypes.BOOL


def validate_capture_not_black(frame: np.ndarray) -> bool:
    return bool(np.any(frame))


def build_capture_box(left: int, top: int, width: int, height: int) -> tuple[int, int, int, int]:
    if width < CAPTURE_WIDTH or height < CAPTURE_HEIGHT:
        raise ValueError(f"target area is smaller than {CAPTURE_WIDTH}x{CAPTURE_HEIGHT}")
    return (left, top, left + CAPTURE_WIDTH, top + CAPTURE_HEIGHT)


def _enum_windows_titles_contains(title_part: str) -> int | None:
    found_hwnd = ctypes.c_void_p()
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd: int, _lparam: int) -> bool:
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True

        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, len(buffer))
        if title_part in buffer.value:
            found_hwnd.value = hwnd
            return False
        return True

    user32.EnumWindows(callback_type(callback), 0)
    return int(found_hwnd.value) if found_hwnd.value else None


def find_window_by_title(title: str = WINDOW_TITLE) -> int | None:
    hwnd = user32.FindWindowW(None, title)
    if hwnd:
        return int(hwnd)
    return _enum_windows_titles_contains(title)


def get_window_rect(hwnd: int) -> tuple[int, int, int, int]:
    window_rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(window_rect)):
        raise ctypes.WinError()

    width = int(window_rect.right - window_rect.left)
    height = int(window_rect.bottom - window_rect.top)
    return (int(window_rect.left), int(window_rect.top), width, height)


def get_client_rect_in_screen(hwnd: int) -> tuple[int, int, int, int]:
    client_rect = RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(client_rect)):
        raise ctypes.WinError()

    top_left = POINT(0, 0)
    if not user32.ClientToScreen(hwnd, ctypes.byref(top_left)):
        raise ctypes.WinError()

    width = int(client_rect.right - client_rect.left)
    height = int(client_rect.bottom - client_rect.top)
    return (int(top_left.x), int(top_left.y), width, height)


def _bitmap_to_rgb(mem_dc: int, bitmap: int, width: int, height: int) -> np.ndarray:
    pixel_buffer = (ctypes.c_ubyte * (width * height * 4))()
    bitmap_info = BITMAPINFOHEADER()
    bitmap_info.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bitmap_info.biWidth = width
    bitmap_info.biHeight = -height
    bitmap_info.biPlanes = 1
    bitmap_info.biBitCount = 32
    bitmap_info.biCompression = BI_RGB

    scan_lines = gdi32.GetDIBits(
        mem_dc,
        bitmap,
        0,
        height,
        pixel_buffer,
        ctypes.byref(bitmap_info),
        0,
    )
    if scan_lines != height:
        raise ctypes.WinError()

    pixels = np.frombuffer(pixel_buffer, dtype=np.uint8)
    pixels = pixels.reshape((height, width, 4))
    return pixels[:, :, [2, 1, 0]]


def _capture_window_rgb(hwnd: int, width: int, height: int) -> np.ndarray:
    window_dc = user32.GetWindowDC(hwnd)
    if not window_dc:
        raise ctypes.WinError()

    mem_dc = gdi32.CreateCompatibleDC(window_dc)
    if not mem_dc:
        user32.ReleaseDC(hwnd, window_dc)
        raise ctypes.WinError()

    bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
    if not bitmap:
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(hwnd, window_dc)
        raise ctypes.WinError()

    old_bitmap = gdi32.SelectObject(mem_dc, bitmap)

    try:
        success = user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT)
        if not success:
            success = user32.PrintWindow(hwnd, mem_dc, 0)
        if not success:
            raise RuntimeError("PrintWindow failed")
        return _bitmap_to_rgb(mem_dc, bitmap, width, height)
    finally:
        gdi32.SelectObject(mem_dc, old_bitmap)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(hwnd, window_dc)


def capture_rgb() -> np.ndarray:
    hwnd = find_window_by_title(WINDOW_TITLE)
    if not hwnd:
        raise RuntimeError(f"window not found: {WINDOW_TITLE}")

    window_left, window_top, window_width, window_height = get_window_rect(hwnd)
    client_left, client_top, client_width, client_height = get_client_rect_in_screen(hwnd)
    capture_left, capture_top, capture_right, capture_bottom = build_capture_box(
        client_left,
        client_top,
        client_width,
        client_height,
    )

    image = _capture_window_rgb(hwnd, window_width, window_height)
    crop_left = capture_left - window_left
    crop_top = capture_top - window_top
    crop_right = crop_left + CAPTURE_WIDTH
    crop_bottom = crop_top + CAPTURE_HEIGHT

    if crop_left < 0 or crop_top < 0 or crop_right > window_width or crop_bottom > window_height:
        raise RuntimeError("capture box is outside of the captured window image")

    return image[crop_top:crop_bottom, crop_left:crop_right]
