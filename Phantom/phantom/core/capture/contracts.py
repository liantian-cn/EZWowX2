"""
Summary:
    定义截图后端、worker 和最新结果的共同契约。
Description:
    后端只负责物理坐标截图；worker 负责定位、校验及状态交付。
    图像使用 RGB uint8，矩形采用左上包含、右下不包含的物理像素坐标。
Key Variables:
    CaptureResult.image: 当前区域图像；尚无区域时为 None。
    CaptureStatus.has_error: 本次采集是否没有可用结果。
Change Log:
    2026-09-14: Changed 增加可选帧序号以识别持续执行的新截图。
    2026-09-11: Added 截图基础公共契约。
    2026-09-12: Added 截图 worker 契约的只读运行状态。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

type RGBImage = NDArray[np.uint8]


@dataclass(frozen=True)
class Bounds:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def translated(self, x: int, y: int) -> Bounds:
        return Bounds(self.left + x, self.top + y, self.right + x, self.bottom + y)


@dataclass(frozen=True)
class CaptureStatus:
    has_error: bool = False
    description: str = ""


@dataclass(frozen=True)
class CaptureResult:
    image: RGBImage | None = None
    status: CaptureStatus = CaptureStatus()
    sequence: int | None = None


class CaptureBackend(Protocol):
    def desktop_bounds(self) -> Bounds: ...

    def capture(self, bounds: Bounds) -> RGBImage: ...

    def close(self) -> None: ...


class CaptureWorker(Protocol):
    @property
    def is_running(self) -> bool: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def set_fps(self, fps: float = 15) -> None: ...

    def get_latest_result(self) -> CaptureResult: ...
