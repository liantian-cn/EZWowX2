from __future__ import annotations

import ctypes
from ctypes import wintypes

import numpy as np


__all__ = ["get_monitors", "capture_screen"]

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

SRCCOPY = 0x00CC0020
BI_RGB = 0


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


def build_monitor_dict(left: int, top: int, right: int, bottom: int) -> dict[str, int]:
    return {
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "width": right - left,
        "height": bottom - top,
    }


def _read_required_region_value(region: dict, key: str) -> int:
    if key not in region:
        raise KeyError(f"region 缺少必须字段: {key}")
    return int(region[key])


def enumerate_monitor_dicts() -> list[dict[str, int]]:
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
    return [build_monitor_dict(left=left, top=top, right=right, bottom=bottom) for left, top, right, bottom in sorted_rects]


def get_monitors() -> list:
    monitor_dicts = enumerate_monitor_dicts()
    return [len(monitor_dicts), *monitor_dicts]


def build_capture_rect(monitor_region: dict, region: dict | None = None) -> dict[str, int]:
    monitor_left = _read_required_region_value(monitor_region, "left")
    monitor_top = _read_required_region_value(monitor_region, "top")
    monitor_right = _read_required_region_value(monitor_region, "right")
    monitor_bottom = _read_required_region_value(monitor_region, "bottom")

    if region is None:
        return build_monitor_dict(
            left=monitor_left,
            top=monitor_top,
            right=monitor_right,
            bottom=monitor_bottom,
        )

    relative_left = _read_required_region_value(region, "left")
    relative_top = _read_required_region_value(region, "top")
    relative_right = _read_required_region_value(region, "right")
    relative_bottom = _read_required_region_value(region, "bottom")

    monitor_width = monitor_right - monitor_left
    monitor_height = monitor_bottom - monitor_top

    if relative_left < 0 or relative_top < 0:
        raise ValueError("region 不能是负坐标，它必须是相对于显示器内部的区域")
    if relative_right > monitor_width or relative_bottom > monitor_height:
        raise ValueError("region 超出了这块显示器的范围")
    if relative_right <= relative_left or relative_bottom <= relative_top:
        raise ValueError("region 的 right/bottom 必须大于 left/top")

    absolute_left = monitor_left + relative_left
    absolute_top = monitor_top + relative_top
    absolute_right = monitor_left + relative_right
    absolute_bottom = monitor_top + relative_bottom
    return build_monitor_dict(
        left=absolute_left,
        top=absolute_top,
        right=absolute_right,
        bottom=absolute_bottom,
    )


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


def capture_screen(monitor_region: dict, region: dict | None = None) -> np.ndarray:
    capture_rect = build_capture_rect(monitor_region=monitor_region, region=region)
    width = capture_rect["width"]
    height = capture_rect["height"]

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
        if not gdi32.BitBlt(
            mem_dc,
            0,
            0,
            width,
            height,
            screen_dc,
            capture_rect["left"],
            capture_rect["top"],
            SRCCOPY,
        ):
            raise ctypes.WinError()
        return _bitmap_to_rgb(mem_dc, bitmap, width, height)
    finally:
        gdi32.SelectObject(mem_dc, old_bitmap)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(0, screen_dc)


if __name__ == "__main__":
    # 这段调试说明只在直接运行文件时才有，正常 import 时不会留在模块里。
    print("这个调试入口会做 4 件事: ")
    print("1. 打印当前机器有几块显示器")
    print("2. 打印每块显示器的区域")
    print("3. 为每块显示器保存一张整屏图")
    print("4. 再为每块显示器保存一张右上角小图")
    print("")

    from pathlib import Path
    from PIL import Image

    base_dir = Path(__file__).resolve().parent
    small_region = {
        "left": 3504,
        "top": 0,
        "right": 3840,
        "bottom": 112,
    }

    def save_rgb_image(frame: np.ndarray, output_path: Path) -> None:
        Image.fromarray(frame, mode="RGB").save(output_path)

    def build_output_path(index: int, small: bool) -> Path:
        if small:
            return base_dir / f"monitor_{index}_small.png"
        return base_dir / f"monitor_{index}.png"

    monitors = get_monitors()
    print(f"screen_count: {monitors[0]}")
    for index, monitor in enumerate(monitors[1:]):
        print(
            f"monitor_{index}: "
            f"left={monitor['left']} top={monitor['top']} right={monitor['right']} bottom={monitor['bottom']} "
            f"width={monitor['width']} height={monitor['height']}"
        )

    print("")

    for index, monitor in enumerate(monitors[1:]):
        full_frame = capture_screen(monitor_region=monitor, region=None)
        full_output_path = build_output_path(index=index, small=False)
        save_rgb_image(full_frame, full_output_path)
        print(f"saved full image: {full_output_path}")

        try:
            small_frame = capture_screen(monitor_region=monitor, region=small_region)
        except ValueError as error:
            print(f"skip monitor_{index} small image: {error}")
            continue

        small_output_path = build_output_path(index=index, small=True)
        save_rgb_image(small_frame, small_output_path)
        print(f"saved small image: {small_output_path}")
