from __future__ import annotations

import ctypes
from ctypes import wintypes
from pathlib import Path

import numpy as np
from PIL import Image


user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

SRCCOPY = 0x00CC0020
BI_RGB = 0
BASE_DIR = Path(__file__).resolve().parent


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


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


def build_monitor_info(index: int, left: int, top: int, right: int, bottom: int) -> dict[str, int]:
    return {
        "index": index,
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "width": right - left,
        "height": bottom - top,
    }


def build_virtual_desktop_info(monitors: list[dict[str, int]]) -> dict[str, int]:
    if not monitors:
        raise ValueError("monitors is empty")

    left = min(monitor["left"] for monitor in monitors)
    top = min(monitor["top"] for monitor in monitors)
    right = max(monitor["right"] for monitor in monitors)
    bottom = max(monitor["bottom"] for monitor in monitors)
    return {
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "width": right - left,
        "height": bottom - top,
    }


def build_output_path(kind: str, base_dir: Path = BASE_DIR, index: int | None = None) -> Path:
    if kind == "monitor":
        if index is None:
            raise ValueError("index is required for monitor output")
        return base_dir / f"monitor_{index}.png"
    if kind == "virtual_desktop":
        return base_dir / "virtual_desktop.png"
    raise ValueError(f"unsupported output kind: {kind}")


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


def capture_rect_rgb(left: int, top: int, width: int, height: int) -> np.ndarray:
    screen_dc = user32.GetDC(0)
    if not screen_dc:
        raise ctypes.WinError()

    mem_dc = gdi32.CreateCompatibleDC(screen_dc)
    if not mem_dc:
        user32.ReleaseDC(0, screen_dc)
        raise ctypes.WinError()

    bitmap = gdi32.CreateCompatibleBitmap(screen_dc, width, height)
    if not bitmap:
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(0, screen_dc)
        raise ctypes.WinError()

    old_bitmap = gdi32.SelectObject(mem_dc, bitmap)

    try:
        if not gdi32.BitBlt(mem_dc, 0, 0, width, height, screen_dc, left, top, SRCCOPY):
            raise ctypes.WinError()
        return _bitmap_to_rgb(mem_dc, bitmap, width, height)
    finally:
        gdi32.SelectObject(mem_dc, old_bitmap)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(0, screen_dc)


def save_rgb_image(frame: np.ndarray, output_path: Path) -> None:
    Image.fromarray(frame, mode="RGB").save(output_path)


def enumerate_monitors() -> list[dict[str, int]]:
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HANDLE,
        wintypes.HDC,
        ctypes.POINTER(RECT),
        wintypes.LPARAM,
    )
    raw_rects: list[tuple[int, int, int, int]] = []

    def callback(_monitor_handle, _monitor_dc, monitor_rect_ptr, _lparam):
        rect = monitor_rect_ptr.contents
        raw_rects.append((int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)))
        return True

    if not user32.EnumDisplayMonitors(0, 0, callback_type(callback), 0):
        raise ctypes.WinError()

    sorted_rects = sorted(raw_rects, key=lambda item: (item[0], item[1], item[2], item[3]))
    return [
        build_monitor_info(index=index, left=left, top=top, right=right, bottom=bottom)
        for index, (left, top, right, bottom) in enumerate(sorted_rects)
    ]


def print_monitor_summary(monitors: list[dict[str, int]], virtual_desktop: dict[str, int]) -> None:
    print("Monitors:")
    for monitor in monitors:
        print(
            f"monitor_{monitor['index']}: "
            f"left={monitor['left']} top={monitor['top']} right={monitor['right']} bottom={monitor['bottom']} "
            f"width={monitor['width']} height={monitor['height']}"
        )
    print("")
    print(
        "virtual_desktop: "
        f"left={virtual_desktop['left']} top={virtual_desktop['top']} right={virtual_desktop['right']} bottom={virtual_desktop['bottom']} "
        f"width={virtual_desktop['width']} height={virtual_desktop['height']}"
    )


def main() -> None:
    monitors = enumerate_monitors()
    virtual_desktop = build_virtual_desktop_info(monitors)
    print_monitor_summary(monitors, virtual_desktop)

    for monitor in monitors:
        output_path = build_output_path(kind="monitor", base_dir=BASE_DIR, index=monitor["index"])
        frame = capture_rect_rgb(
            left=monitor["left"],
            top=monitor["top"],
            width=monitor["width"],
            height=monitor["height"],
        )
        save_rgb_image(frame, output_path)
        print(f"saved: {output_path}")

    virtual_output_path = build_output_path(kind="virtual_desktop", base_dir=BASE_DIR)
    virtual_frame = capture_rect_rgb(
        left=virtual_desktop["left"],
        top=virtual_desktop["top"],
        width=virtual_desktop["width"],
        height=virtual_desktop["height"],
    )
    save_rgb_image(virtual_frame, virtual_output_path)
    print(f"saved: {virtual_output_path}")


if __name__ == "__main__":
    main()
