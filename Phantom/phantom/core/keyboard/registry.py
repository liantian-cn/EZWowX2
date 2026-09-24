"""
Summary:
    按精确目录加载独立键盘插件。
Description:
    核心只检查公开发送及关闭接口；构造插件不寻找窗口或发送按键。
Key Variables:
    Registry.root: 键盘插件的唯一源码根目录。
Change Log:
    2026-09-14: Added keyboards 精确版本加载，无隐式回退。
"""

import hashlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import cast

from phantom.core.keyboard.contracts import Key, Keyboard, KeyCombination


class KeyboardPluginError(ValueError):
    """键盘插件不能加载或不满足公开契约。"""


class Registry:
    def __init__(self, root: Path | None = None) -> None:
        self.root: Path = (root if root is not None else Path(__file__).resolve().parents[2] / "keyboards").resolve()
        self._classes: dict[str, type[object]] = {}

    def create(self, identifier: str = "post_message@dev") -> Keyboard:
        try:
            if not identifier or identifier in {".", ".."} or any(character in identifier for character in "/\\:") or identifier.endswith((".", " ")) or Path(identifier).is_absolute():
                raise ValueError("插件标识必须是单个安全目录名")
            directory = self.root / identifier
            source = directory / "keyboard.py"
            if directory.resolve().parent != self.root or source.resolve().parent != directory.resolve():
                raise ValueError("键盘源码必须位于精确版本目录内")
            if not source.is_file():
                raise ValueError("缺少精确版本的 keyboard.py")
            if identifier not in self._classes:
                digest = hashlib.sha256(str(source.resolve()).encode()).hexdigest()
                name = f"phantom_keyboard_{digest}"
                spec = importlib.util.spec_from_file_location(name, source)
                if spec is None or spec.loader is None:
                    raise ValueError("无法加载键盘模块")
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                try:
                    spec.loader.exec_module(module)
                    candidate = getattr(module, "Plugin", None)
                    if not isinstance(candidate, type):
                        raise ValueError("keyboard.py 必须导出 Plugin 类")
                    inspect.signature(candidate).bind()
                    self._classes[identifier] = candidate
                except Exception:
                    sys.modules.pop(name, None)
                    raise
            instance = self._classes[identifier]()
            for method_name, arguments in (("send", (KeyCombination((Key.A,)),)), ("close", ())):
                method = getattr(instance, method_name, None)
                if not callable(method):
                    raise ValueError(f"缺少接口 {method_name}")
                inspect.signature(method).bind(*arguments)
            return cast(Keyboard, instance)
        except Exception as error:
            raise KeyboardPluginError(f"键盘插件 {identifier}：{error}") from error
