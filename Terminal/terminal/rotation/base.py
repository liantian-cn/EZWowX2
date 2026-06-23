from __future__ import annotations

from typing import Any


from terminal.context import Context


class BaseRotation:
    name = "BaseRotation"
    desc = "BaseRotation"

    def __init__(self) -> None:

        self.macroTable = {}

    def idle(self, reason: str = "") -> tuple[str, Any, str]:
        return "idle", 0.0, reason

    def wait(self, seconds: float, reason: str = "") -> tuple[str, float, str]:
        return "wait", seconds, reason

    def cast(self, macro: str) -> tuple[str, Any, str]:
        return "cast", 0.0, macro

    def handle(self, decoded_data: dict[str, Any]) -> tuple[str, Any, str]:
        ctx = Context(decoded_data)
        action, timeout, value = self.main_rotation(ctx)
        if action not in {"idle", "wait", "cast"}:
            raise ValueError(f"Invalid action: {action}")
        return action, timeout, value

    def main_rotation(self, ctx: Context) -> tuple[str, Any, str]:
        raise NotImplementedError("main_rotation not implemented")

    def updateMacro(self, macroTable: dict[str, str]) -> None:
        self.macroTable.update(macroTable)

    def getMacroKey(self, macro) -> str | None:
        return self.macroTable.get(macro, None)
