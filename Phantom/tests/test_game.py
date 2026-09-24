from threading import Event

import psutil
import pytest

from phantom.core.game import GameMonitor, GameStatus, detect_game, is_retail_wow


# 路径均为虚构样例，仅验证 Windows/UNC 语法，不读取实际文件系统。
@pytest.mark.parametrize(
    ("name", "path", "expected"),
    [
        ("Wow.exe", r"X:\Synthetic Game\_retail_\Wow.exe", True),
        ("WOW.EXE", r"X:\Synthetic Game\_RETAIL_\WOW.EXE", True),
        ("wow.exe", r"\\synthetic-server\synthetic-games\_retail_\wow.exe", True),
        ("wow.exe", r"X:\Synthetic Game\_classic_\wow.exe", False),
        ("wow.exe", r"X:\Synthetic Game\_retail_\other\wow.exe", False),
        ("wow.exe", r"X:\Synthetic Game\_retail_\wow.exe.bak", False),
        ("wow.exe", r"_retail_\wow.exe", False),
        ("notwow.exe", r"X:\Synthetic Game\_retail_\wow.exe", False),
        ("wow.exe", "", False),
    ],
)
def test_retail_path_matching(name: str, path: str, expected: bool) -> None:
    assert is_retail_wow(name, path) is expected


class Process:
    def __init__(self, name: str, executable: str | Exception) -> None:
        self._name: str = name
        self._executable: str | Exception = executable

    def name(self) -> str:
        return self._name

    def exe(self) -> str:
        if isinstance(self._executable, Exception):
            raise self._executable
        return self._executable


def test_detection_handles_exit_denied_path_and_multiple_games(monkeypatch: pytest.MonkeyPatch) -> None:
    processes = [Process("wow.exe", psutil.NoSuchProcess(123)), Process("wow.exe", psutil.AccessDenied(456)), Process("wow.exe", r"X:\Synthetic Game\_classic_\wow.exe")]
    monkeypatch.setattr(psutil, "process_iter", lambda: iter(processes))
    assert not detect_game().running
    assert "无法核验" in detect_game().description
    processes.append(Process("wow.exe", r"X:\Synthetic Game\_retail_\wow.exe"))
    assert detect_game() == GameStatus(True)
    processes.clear()
    assert detect_game() == GameStatus()


def test_monitor_runs_off_caller_and_stops_without_late_publication() -> None:
    entered = Event()
    release = Event()
    published: list[GameStatus] = []

    def detector() -> GameStatus:
        entered.set()
        assert release.wait(3)
        return GameStatus(True)

    monitor = GameMonitor(published.append, detector)
    monitor.start()
    assert entered.wait(3)
    release.set()
    monitor.stop()
    count = len(published)
    monitor.stop()
    assert len(published) == count
