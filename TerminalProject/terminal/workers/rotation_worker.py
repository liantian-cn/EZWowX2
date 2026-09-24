from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal

from ..rotation.base import BaseRotation


class RotationWorker(QObject):
    """执行 rotation 并把 macro 名称解析成实际按键。"""

    rotation_ready = Signal(int, str, object, object, float, str)
    rotation_failed = Signal(int, str)

    def evaluate_rotation(
        self,
        decoded_data: dict[str, Any],
        frame_id: int,
        rotation_class: type[BaseRotation],
    ) -> None:
        try:
            rotation = rotation_class()
            action, timeout, value = rotation.handle(decoded_data)
        except Exception as error:
            self.rotation_failed.emit(frame_id, f"第 {frame_id} 帧 rotation 异常: {error}")
            return

        if action == "cast":
            macro_name = str(value)
            macro_key = rotation.getMacroKey(macro_name)
            self.rotation_ready.emit(frame_id, action, macro_name, macro_key, 0.0, macro_name)
            return

        if action == "wait":
            self.rotation_ready.emit(frame_id, action, None, None, float(timeout), str(value))
            return

        self.rotation_ready.emit(frame_id, action, None, None, 0.0, str(value))
