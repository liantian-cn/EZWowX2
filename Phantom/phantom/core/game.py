"""
Summary:
    核验零售版 WoW 进程，并独立发布游戏启动状态。
Description:
    进程名称和可执行文件直接父目录共同确认游戏；不绑定本机安装位置。
    后台监视线程每秒查询一次，停止时等待查询结束，不在 UI 线程调用系统查询。
Key Variables:
    GameStatus.running: 是否确认至少一个 _retail_/wow.exe 正在运行。
    GameMonitor._stop: 唤醒轮询等待并结束游戏检测。
Change Log:
    2026-09-12: Added TUI 的游戏状态检测与后台生命周期。
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PureWindowsPath
from threading import Event, Thread

import psutil


@dataclass(frozen=True)
class GameStatus:
    running: bool = False
    description: str = ""


def is_retail_wow(name: str, executable: str) -> bool:
    path = PureWindowsPath(executable)
    return name.casefold() == "wow.exe" and path.is_absolute() and path.name.casefold() == "wow.exe" and path.parent.name.casefold() == "_retail_"


def detect_game() -> GameStatus:
    inaccessible = False
    try:
        for process in psutil.process_iter():
            try:
                name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if name.casefold() != "wow.exe":
                continue
            try:
                executable = process.exe()
                if is_retail_wow(name, executable):
                    return GameStatus(True)
                if not executable:
                    inaccessible = True
            except psutil.NoSuchProcess:
                continue
            except psutil.AccessDenied:
                inaccessible = True
    except (psutil.Error, OSError) as error:
        return GameStatus(description=f"游戏进程检测失败：{error}")
    if inaccessible:
        return GameStatus(description="无法核验 wow.exe 路径，未确认游戏启动")
    return GameStatus()


class GameMonitor:
    def __init__(self, publish: Callable[[GameStatus], None], detector: Callable[[], GameStatus] = detect_game) -> None:
        self._publish: Callable[[GameStatus], None] = publish
        self._detector: Callable[[], GameStatus] = detector
        self._stop: Event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = Thread(target=self._run, name="phantom-game", daemon=False)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                status = self._detector()
            except Exception as error:
                # 未预期的查询错误是本次检测失败，不允许被当成“游戏已启动”。
                self._publish(GameStatus(description=f"游戏进程检测失败：{error}"))
                return
            if self._stop.is_set():
                return
            self._publish(status)
            self._stop.wait(1)
