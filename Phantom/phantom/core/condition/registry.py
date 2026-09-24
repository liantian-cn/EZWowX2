"""
Summary:
    按精确名称和版本加载条件类与配套 Lua 模板。
Description:
    仅访问插件根目录中的精确版本目录，缓存类但不共享条件实例。
    导入失败及参数错误附带插件标识，不回退版本。
Key Variables:
    Registry._classes: 当前 registry 生命周期内的精确版本类缓存。
Change Log:
    2026-09-14: Changed 允许无 Lua 模板插件，保留存在模板的路径与文件校验。
    2026-09-13: Changed 命名交由作者规则约束，精确加载并检查目录与源码边界。
    2026-09-12: Added 条件插件发现与参数校验入口。
"""

import hashlib
import importlib.util
import sys
from pathlib import Path

from phantom.core.condition.base import Condition


class Registry:
    def __init__(self, root: Path | None = None) -> None:
        self.root: Path = (root if root is not None else Path(__file__).resolve().parents[2] / "conditions").resolve()
        self._classes: dict[str, type[Condition]] = {}

    def create(self, identifier: str, args: dict[str, object]) -> Condition:
        try:
            if not identifier or identifier in {".", ".."} or any(character in identifier for character in "/\\:") or identifier.endswith((".", " ")) or Path(identifier).is_absolute():
                raise ValueError("插件标识必须是单个安全目录名")
            directory = self.root / identifier
            if directory.resolve().parent != self.root:
                raise ValueError("插件目录必须位于条件根目录内")
            template = directory / "template.lua"
            source = directory / "condition.py"
            if any(path.resolve().parent != directory.resolve() for path in (source, template)):
                raise ValueError("条件源码与模板必须位于精确版本目录内")
            if not source.is_file():
                raise ValueError("缺少精确版本的 condition.py")
            if (template.exists() or template.is_symlink()) and not template.is_file():
                raise ValueError("template.lua 必须为可读取的文件")
            if identifier not in self._classes:
                digest = hashlib.sha256(str(source.resolve()).encode()).hexdigest()
                module_name = f"phantom_condition_{digest}"
                spec = importlib.util.spec_from_file_location(module_name, source)
                if spec is None or spec.loader is None:
                    raise ValueError("无法创建插件模块")
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                try:
                    spec.loader.exec_module(module)
                    candidate = getattr(module, "Plugin", None)
                    if not isinstance(candidate, type) or not issubclass(candidate, Condition):
                        raise ValueError("condition.py 必须公开 Condition 子类 Plugin")
                    self._classes[identifier] = candidate
                except Exception:
                    sys.modules.pop(module_name, None)
                    raise
            instance = self._classes[identifier](args)  # type: ignore[arg-type]
            if template.is_file():
                instance.set_template(template)
            return instance
        except Exception as error:
            raise ValueError(f"插件 {identifier}：{error}") from error
