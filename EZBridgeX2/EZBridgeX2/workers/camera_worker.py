import time
from typing import Any
import numpy as np
from PySide6.QtCore import QThread, Signal

class CameraWorker(QThread):
    data_signal = Signal(np.ndarray, str)
    log_signal = Signal(str)

    def __init__(self, camera: Any, fps: int, region: tuple[int, int, int, int]) -> None:
        super().__init__()
        self._running: bool = False
        self.camera: Any = camera
        self.fps: int = fps
        self.region: tuple[int, int, int, int] = region

    def _start_capture(self) -> bool:
        left, top, right, bottom = self.region
        try:
            self.camera.start(target_fps=self.fps, region=(left, top, right, bottom))
            return True
        except Exception as error:
            self.log_signal.emit(f'CameraWorker 启动 DXCam 失败: {error}')
            return False

    def _restart_capture(self, reason: str) -> bool:
        self.log_signal.emit(f'CameraWorker {reason}，尝试自动重启 DXCam')
        try:
            self.camera.stop()
        except Exception as stop_error:
            self.log_signal.emit(f'CameraWorker 停止 DXCam 失败: {stop_error}')
        if not self._running:
            return False
        time.sleep(0.2)
        if self._start_capture():
            self.log_signal.emit('CameraWorker DXCam 自动重启成功')
            return True
        return False

    def _is_capture_thread_alive(self) -> bool:
        # NOTE: Accesses dxcam private attribute via name-mangling. If dxcam internals
        # change, getattr returns None and this method returns False (triggers restart).
        thread: Any = getattr(self.camera, '_DXCamera__thread', None)
        if thread is None:
            return False
        return bool(thread.is_alive())

    def _get_latest_frame_with_timeout(self, timeout: float) -> np.ndarray | None:
        # NOTE: Accesses dxcam private attribute via name-mangling. If dxcam internals
        # change, getattr returns None and we fall through to get_latest_frame() directly.
        frame_available_event: Any = getattr(self.camera, '_DXCamera__frame_available', None)
        if frame_available_event is not None and (not frame_available_event.wait(timeout)):
            return None
        return self.camera.get_latest_frame()

    def run(self) -> None:
        self._running = True
        if not self._start_capture():
            self._running = False
            return
        stalled_frame_count: int = 0
        while self._running:
            try:
                if not self.camera.is_capturing or not self._is_capture_thread_alive():
                    if not self._restart_capture('检测到 DXCam 捕获线程已停止'):
                        time.sleep(0.5)
                    stalled_frame_count = 0
                    continue
                frame: np.ndarray | None = self._get_latest_frame_with_timeout(timeout=1.0)
                if frame is None:
                    stalled_frame_count += 1
                    if stalled_frame_count >= 3:
                        if not self._restart_capture('连续等待新帧超时'):
                            time.sleep(0.5)
                        stalled_frame_count = 0
                    continue
                stalled_frame_count = 0
                self.data_signal.emit(frame, 'ok')
            except Exception as error:
                if not self._restart_capture(f'截图异常: {error}'):
                    time.sleep(0.5)
                stalled_frame_count = 0

    def stop(self) -> None:
        self._running = False
        if hasattr(self.camera, 'stop'):
            self.camera.stop()
        if hasattr(self.camera, 'release'):
            self.camera.release()
        self.wait()