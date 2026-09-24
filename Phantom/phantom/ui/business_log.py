"""
Summary:
    为主动业务日志提供带时间戳、连续去重的独立入口。
Description:
    调用者通过 log(message) 写入业务事件；界面接收端负责有界显示。
    不继承或覆盖 Textual 的诊断 log 属性，也不连接 Python logging。
Key Variables:
    BusinessLog._previous: 上一条被接受的原始正文，去重不比较时间戳。
Change Log:
    2026-09-12: Added 第 5 步业务日志接口。
"""

from collections.abc import Callable
from datetime import datetime
from threading import Lock


class BusinessLog:
    def __init__(self, publish: Callable[[str], None]) -> None:
        self._publish: Callable[[str], None] = publish
        self._previous: str | None = None
        self._lock: Lock = Lock()

    def log(self, message: str) -> None:
        with self._lock:
            if message == self._previous:
                return
            self._previous = message
            timestamp = datetime.now().strftime("%H:%M:%S")
            # 多行正文每行都标注同一写入时间；显示组件按实际行数淘汰旧行。
            lines = message.splitlines() or [""]
            self._publish("\n".join(f"[{timestamp}] {line}" for line in lines))
