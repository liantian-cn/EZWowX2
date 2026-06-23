from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Qt, Signal

from ..capture.capture_screen import build_monitor_dict, capture_screen
from ..capture.find_template_bounds import find_template_bounds


class CaptureWorker(QObject):
    """截图 worker。

    这个类只做截图相关工作，不碰任何 UI 控件。
    整体流程故意按真实执行顺序展开: 

    1. 收到启动参数。
    2. 先对整块显示器截图。
    3. 找标志位。
    4. 找到后只截小区域。
    5. 用 Qt 定时器按 FPS 持续循环。
    """

    log_message = Signal(str)
    capture_ready = Signal(object)
    capture_started = Signal(object)
    capture_failed = Signal(str)
    capture_stopped = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._is_running = False
        self._fps = 15
        self._monitor_region: dict[str, int] | None = None
        self._capture_region: dict[str, int] | None = None

        # 用 QTimer 而不是 while + sleep，
        # 这样 stop / fps 更新都还能继续走 Qt 自己的事件循环。
        self._timer = QTimer(self)
        self._timer.setSingleShot(False)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._capture_current_region)
        self._update_timer_interval()

    def set_fps(self, value: int) -> None:
        """保存新的 FPS，并立刻改掉下一轮定时器间隔。"""

        self._fps = max(1, int(value))
        self._update_timer_interval()

    def start_capture(self, monitor_region: dict[str, int], fps: int) -> None:
        """启动截图。

        启动时先整屏找标志位；只有找到了，后面才进入小区域循环截图。
        """

        if self._is_running:
            self.log_message.emit('截图 worker 已经在运行，这次启动请求会被忽略。')
            return

        self._monitor_region = dict(monitor_region)
        self._capture_region = None
        self._is_running = True
        self.set_fps(fps)

        self.log_message.emit('worker 收到启动参数。')
        self.log_message.emit('开始整屏查找标志位。')

        try:
            full_frame = capture_screen(monitor_region=self._monitor_region, region=None)
        except Exception as error:  # pragma: no cover - 具体系统错误文字依赖 Windows API
            self._fail_and_reset(f'整屏截图失败: {error}')
            return

        bounds = find_template_bounds(full_frame)
        if bounds is None:
            self._fail_and_reset('未找到标志位，已自动停机。')
            return

        left, top, right, bottom = bounds
        self._capture_region = build_monitor_dict(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
        )
        self.log_message.emit(
            '已锁定截图区域: '
            f'left={left} top={top} right={right} bottom={bottom}'
        )
        self.capture_started.emit(self._capture_region)
        self._capture_current_region()

        if self._is_running:
            self._timer.start()

    def stop_capture(self) -> None:
        """停止截图循环。"""

        if not self._is_running and not self._timer.isActive():
            return

        self._timer.stop()
        self._is_running = False
        self._capture_region = None
        self.capture_stopped.emit()

    def _update_timer_interval(self) -> None:
        """把 FPS 换算成毫秒间隔。"""

        interval_ms = max(1, round(1000 / self._fps))
        self._timer.setInterval(interval_ms)

    def _capture_current_region(self) -> None:
        """定时器每次触发时，只截已经锁定的小区域。"""

        if not self._is_running:
            return
        if self._monitor_region is None or self._capture_region is None:
            self._fail_and_reset('截图区域还没准备好。')
            return

        try:
            frame = capture_screen(
                monitor_region=self._monitor_region,
                region=self._capture_region,
            )
        except Exception as error:  # pragma: no cover - 具体系统错误文字依赖 Windows API
            self._fail_and_reset(f'小区域截图失败: {error}')
            return

        self.capture_ready.emit(frame)

    def _fail_and_reset(self, reason: str) -> None:
        """发生异常时统一走这里，避免状态只改一半。"""

        self._timer.stop()
        self._is_running = False
        self._capture_region = None
        self.capture_failed.emit(reason)
