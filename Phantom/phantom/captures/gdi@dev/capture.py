"""
Summary:
    使用 Windows GDI 截取虚拟桌面或指定物理像素区域。
Description:
    在截图线程内开启物理像素坐标，复用 DC 和同尺寸位图；BitBlt 后取消位图选择，
    再通过 GetDIBits 读取自顶向下 BGRA 并转换为独立连续 RGB。退出时释放所有资源。
    参考 EZWowX2/Terminal/terminal/capture/capture_screen.py，补全句柄类型与资源契约。
Key Variables:
    GDIBackend._bitmap: 与当前截图尺寸对应、读取时未选入 DC 的位图。
    GDIBackend._previous_dpi: 当前线程原 DPI 上下文，关闭后端时恢复。
Change Log:
    2026-09-13: Changed 公开统一 Plugin 入口并迁用截图核心契约。
    2026-09-11: Added gdi@1.0 截图线程后端。
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

import numpy as np

from phantom.core.capture.contracts import Bounds, RGBImage
from phantom.core.capture.worker import ThreadCaptureWorker


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


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 1)]


def windows_error(operation: str) -> OSError:
    if sys.platform == "win32":
        return OSError(f"{operation} 失败：{ctypes.WinError(ctypes.get_last_error())}")
    return OSError("GDI 截图仅支持 Windows")


def checked_handle(value: int | None, operation: str) -> int:
    if not value or (operation == "SelectObject" and value == ctypes.c_void_p(-1).value):
        raise windows_error(operation)
    return value


class GDIBackend:
    """只持有当前采集线程的 Windows 资源，不负责定位或业务校验。"""

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise OSError("GDI 截图仅支持 Windows")
        self._user32: ctypes.CDLL = ctypes.WinDLL("user32", use_last_error=True)
        self._gdi32: ctypes.CDLL = ctypes.WinDLL("gdi32", use_last_error=True)
        self._screen_dc: int | None = None
        self._memory_dc: int | None = None
        self._bitmap: int | None = None
        self._size: tuple[int, int] | None = None
        self._previous_dpi: int | None = None
        self._declare_signatures()
        try:
            # 仅修改截图线程，避免提前决定未来 Textual 主线程的 DPI 策略。
            self._previous_dpi = checked_handle(self._user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4)), "SetThreadDpiAwarenessContext")
            self._screen_dc = checked_handle(self._user32.GetDC(None), "GetDC")
            self._memory_dc = checked_handle(self._gdi32.CreateCompatibleDC(self._screen_dc), "CreateCompatibleDC")
        except Exception:
            self.close()
            raise

    def _declare_signatures(self) -> None:
        """显式声明指针与句柄宽度，避免 64 位环境默认整数返回值截断。"""
        user32, gdi32 = self._user32, self._gdi32
        user32.SetThreadDpiAwarenessContext.argtypes = [wintypes.HANDLE]
        user32.SetThreadDpiAwarenessContext.restype = wintypes.HANDLE
        user32.GetSystemMetrics.argtypes = [ctypes.c_int]
        user32.GetSystemMetrics.restype = ctypes.c_int
        user32.GetDC.argtypes = [wintypes.HWND]
        user32.GetDC.restype = wintypes.HDC
        user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
        user32.ReleaseDC.restype = ctypes.c_int
        gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
        gdi32.CreateCompatibleDC.restype = wintypes.HDC
        gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
        gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
        gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
        gdi32.SelectObject.restype = wintypes.HGDIOBJ
        gdi32.BitBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
        gdi32.BitBlt.restype = wintypes.BOOL
        gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p, ctypes.POINTER(BITMAPINFO), wintypes.UINT]
        gdi32.GetDIBits.restype = ctypes.c_int
        gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
        gdi32.DeleteObject.restype = wintypes.BOOL
        gdi32.DeleteDC.argtypes = [wintypes.HDC]
        gdi32.DeleteDC.restype = wintypes.BOOL

    def desktop_bounds(self) -> Bounds:
        """取整个虚拟桌面的物理像素范围，左侧或上方显示器可产生负坐标。"""
        left = int(self._user32.GetSystemMetrics(76))  # SM_XVIRTUALSCREEN
        top = int(self._user32.GetSystemMetrics(77))  # SM_YVIRTUALSCREEN
        width = int(self._user32.GetSystemMetrics(78))  # SM_CXVIRTUALSCREEN
        height = int(self._user32.GetSystemMetrics(79))  # SM_CYVIRTUALSCREEN
        if width <= 0 or height <= 0:
            raise OSError("无法取得虚拟桌面尺寸")
        return Bounds(left, top, left + width, top + height)

    def capture(self, bounds: Bounds) -> RGBImage:
        """复用同尺寸位图，交付不依赖 Windows 缓冲区的连续 RGB 快照。"""
        if self._screen_dc is None or self._memory_dc is None:
            raise OSError("GDI 后端已经关闭")
        width, height = bounds.width, bounds.height
        if width <= 0 or height <= 0:
            raise ValueError("截图区域宽高必须大于 0")
        # 全屏定位切换到基板局部采集时才重建位图。
        if self._size != (width, height):
            if self._bitmap is not None:
                if not self._gdi32.DeleteObject(self._bitmap):
                    raise windows_error("DeleteObject")
                self._bitmap = None
            self._bitmap = checked_handle(self._gdi32.CreateCompatibleBitmap(self._screen_dc, width, height), "CreateCompatibleBitmap")
            self._size = (width, height)

        previous = checked_handle(self._gdi32.SelectObject(self._memory_dc, self._bitmap), "SelectObject")
        try:
            if not self._gdi32.BitBlt(self._memory_dc, 0, 0, width, height, self._screen_dc, bounds.left, bounds.top, 0x00CC0020):
                raise windows_error("BitBlt")
        finally:
            # GetDIBits 明确要求目标位图不再选入任何 DC。
            checked_handle(self._gdi32.SelectObject(self._memory_dc, previous), "SelectObject")

        bitmap_info = BITMAPINFO()
        bitmap_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bitmap_info.bmiHeader.biWidth = width
        bitmap_info.bmiHeader.biHeight = -height  # 负高度要求自顶向下，保持与屏幕坐标同向。
        bitmap_info.bmiHeader.biPlanes = 1
        bitmap_info.bmiHeader.biBitCount = 32
        bitmap_info.bmiHeader.biCompression = 0  # BI_RGB
        buffer = (ctypes.c_ubyte * (width * height * 4))()
        lines = self._gdi32.GetDIBits(self._screen_dc, self._bitmap, 0, height, buffer, ctypes.byref(bitmap_info), 0)
        if lines != height:
            raise OSError(f"GetDIBits 只读取 {lines}/{height} 行")
        # GDI 输出 BGRA；丢弃 alpha、反转颜色通道，再独立保存 RGB。
        bgra = np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4)
        return np.ascontiguousarray(bgra[:, :, 2::-1])

    def close(self) -> None:
        """尝试释放所有已申请资源并恢复线程 DPI；汇总释放错误。"""
        failures: list[str] = []
        if self._memory_dc is not None:
            if not self._gdi32.DeleteDC(self._memory_dc):
                failures.append("DeleteDC")
            self._memory_dc = None
        if self._bitmap is not None:
            if not self._gdi32.DeleteObject(self._bitmap):
                failures.append("DeleteObject")
            self._bitmap = None
        if self._screen_dc is not None:
            if not self._user32.ReleaseDC(None, self._screen_dc):
                failures.append("ReleaseDC")
            self._screen_dc = None
        if self._previous_dpi is not None:
            if not self._user32.SetThreadDpiAwarenessContext(self._previous_dpi):
                failures.append("SetThreadDpiAwarenessContext")
            self._previous_dpi = None
        if failures:
            raise OSError("GDI 资源释放失败：" + ", ".join(failures))


class GDIWorker(ThreadCaptureWorker):
    """构造仅保存后端工厂；start 后由公共 worker 在线程内申请 GDI 资源。"""

    def __init__(self, fps: float = 15) -> None:
        super().__init__(GDIBackend, fps)


# 版本加载器的统一入口；具体类名仍说明 GDI 的实现责任。
Plugin = GDIWorker
