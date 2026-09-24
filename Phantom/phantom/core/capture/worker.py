"""
Summary:
    在线程内连续定位和校验基板，向主线程交付最新截图结果。
Description:
    每次运行创建独立后端，从虚拟桌面搜索切换为局部采集；角标丢失时重定位。
    条件变量协调 FPS 更新和停止，独立结果锁保护图像所有权，不积压历史帧。
Key Variables:
    CaptureSession.bounds: 已锁定基板的绝对物理坐标。
    ThreadCaptureWorker._latest: 最后采集结果，停止后仍保留。
    ThreadCaptureWorker._fps: 可在运行期间更新的频率上限。
Change Log:
    2026-09-14: Changed 发布时递增帧序号，快照复制保留同一帧身份。
    2026-09-11: Added 独立截图线程与图像业务流程。
    2026-09-12: Added 只读运行状态，供 TUI 识别截图线程已结束。
"""

import math
from collections.abc import Callable
from threading import Condition, Lock, Thread
from time import monotonic

import numpy as np

from phantom.core.capture.contracts import Bounds, CaptureBackend, CaptureResult, CaptureStatus
from phantom.core.capture.imaging import find_bounds, markers_valid, validate_colors


class CaptureSession:
    def __init__(self, backend: CaptureBackend) -> None:
        self.backend: CaptureBackend = backend
        self.bounds: Bounds | None = None

    def capture_next(self) -> CaptureResult:
        if self.bounds is None:
            desktop = self.backend.desktop_bounds()
            full_image = self.backend.capture(desktop)
            relative, status = find_bounds(full_image)
            if relative is None:
                return CaptureResult(status=status)
            self.bounds = relative.translated(desktop.left, desktop.top)
            image = full_image[relative.top : relative.bottom, relative.left : relative.right]
        else:
            image = self.backend.capture(self.bounds)
            if not markers_valid(image):
                self.bounds = None
                return CaptureResult(image, CaptureStatus(True, "基板尺寸或定位标记失效，重新搜索"))
        return CaptureResult(image, validate_colors(image))


class ThreadCaptureWorker:
    def __init__(self, backend_factory: Callable[[], CaptureBackend], fps: float = 15) -> None:
        self._backend_factory: Callable[[], CaptureBackend] = backend_factory
        self._condition: Condition = Condition()
        self._lifecycle: Lock = Lock()
        self._result_lock: Lock = Lock()
        self._thread: Thread | None = None
        self._stop_requested: bool = True
        self._latest: CaptureResult = CaptureResult()
        self._sequence: int = 0
        self._fps: float = 15
        self.set_fps(fps)

    @property
    def is_running(self) -> bool:
        # 不等待生命周期锁，避免 UI 查询被另一个线程的 stop/join 阻塞。
        thread = self._thread
        return thread is not None and thread.is_alive()

    def set_fps(self, fps: float = 15) -> None:
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("FPS 必须为有限正数")
        with self._condition:
            self._fps = fps
            self._condition.notify_all()

    def start(self) -> None:
        with self._lifecycle:
            if self._thread is not None and self._thread.is_alive():
                return
            with self._result_lock:
                self._latest = CaptureResult()
            with self._condition:
                self._stop_requested = False
            self._thread = Thread(target=self._run, name="phantom-capture", daemon=False)
            self._thread.start()

    def stop(self) -> None:
        with self._lifecycle:
            with self._condition:
                self._stop_requested = True
                self._condition.notify_all()
            if self._thread is not None:
                self._thread.join()

    def get_latest_result(self) -> CaptureResult:
        with self._result_lock:
            result = self._latest
            return CaptureResult(None if result.image is None else result.image.copy(), result.status, result.sequence)

    def _publish(self, result: CaptureResult) -> None:
        image = None if result.image is None else np.array(result.image, copy=True, order="C")
        with self._result_lock:
            self._sequence += 1
            self._latest = CaptureResult(image, result.status, self._sequence)

    def _run(self) -> None:
        backend: CaptureBackend | None = None
        try:
            backend = self._backend_factory()
            session = CaptureSession(backend)
            while True:
                with self._condition:
                    if self._stop_requested:
                        break
                started = monotonic()
                self._publish(session.capture_next())
                with self._condition:
                    while not self._stop_requested:
                        remaining = started + 1 / self._fps - monotonic()
                        if remaining <= 0:
                            break
                        self._condition.wait(remaining)
        except Exception as error:
            self._publish(CaptureResult(status=CaptureStatus(True, f"截图失败：{error}")))
        finally:
            if backend is not None:
                try:
                    backend.close()
                except Exception as error:
                    self._publish(CaptureResult(status=CaptureStatus(True, f"截图资源释放失败：{error}")))
