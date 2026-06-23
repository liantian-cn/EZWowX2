from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import types

from .base import BaseRotation


@dataclass(frozen=True)
class HotReloadEvent:
    status: str
    message: str


class RotationHotReloadTracker:
    def __init__(self, rotation_class: type[BaseRotation] | None = None) -> None:
        self._current_class: type[BaseRotation] | None = None
        self._last_loaded_class: type[BaseRotation] | None = None
        self._module_name = ""
        self._class_name = ""
        self._module_path: Path | None = None
        self._last_loaded_source = ""
        self._last_attempted_source = ""
        if rotation_class is not None:
            self.set_rotation_class(rotation_class)

    def set_rotation_class(self, rotation_class: type[BaseRotation] | None) -> None:
        if rotation_class is None:
            self._clear()
            return

        module_path = self._resolve_module_path(rotation_class)
        current_source = self._read_source(module_path)

        self._current_class = rotation_class
        self._last_loaded_class = rotation_class
        self._module_name = rotation_class.__module__
        self._class_name = rotation_class.__name__
        self._module_path = module_path
        self._last_loaded_source = current_source
        self._last_attempted_source = current_source

    def get_runtime_rotation_class(self) -> tuple[type[BaseRotation] | None, HotReloadEvent | None]:
        if self._last_loaded_class is None or self._module_path is None:
            return None, None

        current_source = self._read_source(self._module_path)
        if current_source == self._last_loaded_source:
            return self._last_loaded_class, None
        if current_source == self._last_attempted_source:
            return self._last_loaded_class, None

        self._last_attempted_source = current_source

        try:
            runtime_class = self._load_rotation_class(current_source)
        except Exception as error:
            return self._last_loaded_class, HotReloadEvent(
                status="failed",
                message=f"rotation 热重载失败: {self._class_name}，继续使用上一版: {error}",
            )

        self._current_class = runtime_class
        self._last_loaded_class = runtime_class
        self._last_loaded_source = current_source
        return runtime_class, HotReloadEvent(
            status="reloaded",
            message=f"rotation 热重载成功: {self._class_name}",
        )

    def _clear(self) -> None:
        self._current_class = None
        self._last_loaded_class = None
        self._module_name = ""
        self._class_name = ""
        self._module_path = None
        self._last_loaded_source = ""
        self._last_attempted_source = ""

    def _resolve_module_path(self, rotation_class: type[BaseRotation]) -> Path:
        module = sys.modules.get(rotation_class.__module__)
        module_file = getattr(module, "__file__", None)
        if not module_file:
            raise FileNotFoundError(f"找不到 rotation 文件: {rotation_class.__module__}")
        return Path(module_file).resolve()

    def _read_source(self, module_path: Path) -> str:
        return module_path.read_text(encoding="utf-8")

    def _load_rotation_class(self, source: str) -> type[BaseRotation]:
        if self._module_path is None:
            raise FileNotFoundError("当前没有可热重载的 rotation 文件")

        code = compile(source, str(self._module_path), "exec")

        previous_module = sys.modules.get(self._module_name)
        fresh_module = types.ModuleType(self._module_name)
        fresh_module.__file__ = str(self._module_path)
        fresh_module.__package__ = self._module_name.rpartition(".")[0]
        fresh_module.__name__ = self._module_name
        fresh_module.__builtins__ = __builtins__

        try:
            sys.modules[self._module_name] = fresh_module
            exec(code, fresh_module.__dict__)
        except Exception:
            if previous_module is not None:
                sys.modules[self._module_name] = previous_module
            else:
                sys.modules.pop(self._module_name, None)
            raise

        runtime_class = getattr(fresh_module, self._class_name, None)
        if not isinstance(runtime_class, type):
            if previous_module is not None:
                sys.modules[self._module_name] = previous_module
            else:
                sys.modules.pop(self._module_name, None)
            raise AttributeError(f"模块中缺少类: {self._class_name}")
        if not issubclass(runtime_class, BaseRotation):
            if previous_module is not None:
                sys.modules[self._module_name] = previous_module
            else:
                sys.modules.pop(self._module_name, None)
            raise TypeError(f"{self._class_name} 不是 BaseRotation 子类")

        return runtime_class
