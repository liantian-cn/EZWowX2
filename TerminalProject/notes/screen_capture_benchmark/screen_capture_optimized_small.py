import ctypes
from ctypes import wintypes

import numpy as np


user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

SRCCOPY = 0x00CC0020
BI_RGB = 0
CAPTURE_WIDTH = 336
CAPTURE_HEIGHT = 112
PRIMARY_SCREEN_WIDTH = user32.GetSystemMetrics(0)


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


class GdiCapture:
    def __init__(self, width: int, height: int, left: int, top: int):
        self.width = width
        self.height = height
        self.left = left
        self.top = top

        self.screen_dc = user32.GetDC(0)
        self.mem_dc = gdi32.CreateCompatibleDC(self.screen_dc)
        self.bitmap = gdi32.CreateCompatibleBitmap(self.screen_dc, width, height)
        gdi32.SelectObject(self.mem_dc, self.bitmap)

        self.pixel_buffer = (ctypes.c_ubyte * (width * height * 4))()
        self.bitmap_info = BITMAPINFOHEADER()
        self.bitmap_info.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        self.bitmap_info.biWidth = width
        self.bitmap_info.biHeight = -height
        self.bitmap_info.biPlanes = 1
        self.bitmap_info.biBitCount = 32
        self.bitmap_info.biCompression = BI_RGB

    def capture_rgb(self) -> np.ndarray:
        gdi32.BitBlt(
            self.mem_dc,
            0,
            0,
            self.width,
            self.height,
            self.screen_dc,
            self.left,
            self.top,
            SRCCOPY,
        )
        gdi32.GetDIBits(
            self.mem_dc,
            self.bitmap,
            0,
            self.height,
            self.pixel_buffer,
            ctypes.byref(self.bitmap_info),
            0,
        )
        pixels = np.frombuffer(self.pixel_buffer, dtype=np.uint8)
        pixels = pixels.reshape((self.height, self.width, 4))
        return pixels[:, :, [2, 1, 0]]

    def __del__(self):
        if hasattr(self, "bitmap"):
            gdi32.DeleteObject(self.bitmap)
        if hasattr(self, "mem_dc"):
            gdi32.DeleteDC(self.mem_dc)
        if hasattr(self, "screen_dc"):
            user32.ReleaseDC(0, self.screen_dc)


_CAPTURE = GdiCapture(
    width=CAPTURE_WIDTH,
    height=CAPTURE_HEIGHT,
    left=PRIMARY_SCREEN_WIDTH - CAPTURE_WIDTH,
    top=0,
)


def capture_rgb() -> np.ndarray:
    return _CAPTURE.capture_rgb()


def validate_capture_not_black(frame: np.ndarray) -> bool:
    return bool(np.any(frame))
