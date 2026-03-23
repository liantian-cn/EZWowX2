from __future__ import annotations
from typing import Any, Callable
from PySide6.QtCore import QThread, Signal

class InfoDisplayWorker(QThread):
    data_signal = Signal(dict)

    def __init__(self, get_pixel_dump: Callable[[], dict[str, Any]], interval_ms: int=200) -> None:
        super().__init__()
        self._running: bool = False
        self._get_pixel_dump: Callable[[], dict[str, Any]] = get_pixel_dump
        self._interval_ms: int = max(50, interval_ms)

    def run(self) -> None:
        self._running = True
        while self._running:
            try:
                pixel_dump: dict[str, Any] = self._get_pixel_dump()
            except Exception:
                pixel_dump = {}
            self.data_signal.emit(pixel_dump)
            self.msleep(self._interval_ms)

    def stop(self) -> None:
        self._running = False
        self.wait()
