"""
Summary:
    按精确版本加载截图插件并检查启动所需接口。
Description:
    插件导出接受 fps 的 Plugin 类，构造时不启动线程或采集资源。
    核心在 UI 创建前核验调用签名和初始状态，失败保留插件标识与原始原因。
Key Variables:
    Registry.root: 截图版本插件根目录，默认指向 phantom/captures。
Change Log:
    2026-09-13: Changed 命名交由作者规则约束，默认加载 liantian_cn.gdi@dev。
    2026-09-13: Added 可配置截图插件加载入口。
"""

import hashlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import cast

from phantom.core.capture.contracts import CaptureResult, CaptureWorker
from phantom.core.validation import PositiveNumber


class CapturePluginError(ValueError):
    """截图插件选择、加载或构造不满足契约。"""


class Registry:
    def __init__(self, root: Path | None = None) -> None:
        self.root: Path = (root if root is not None else Path(__file__).resolve().parents[2] / "captures").resolve()
        self._classes: dict[str, type[object]] = {}

    def create(self, identifier: str = "gdi@dev", *, fps: float = 15) -> CaptureWorker:
        try:
            if not identifier or identifier in {".", ".."} or any(character in identifier for character in "/\\:") or identifier.endswith((".", " ")) or Path(identifier).is_absolute():
                raise ValueError("插件标识必须是单个安全目录名")
            fps = PositiveNumber().validate(fps, "capture.fps")
            directory = self.root / identifier
            source = directory / "capture.py"
            if directory.resolve().parent != self.root or source.resolve().parent != directory.resolve():
                raise ValueError("截图源码必须位于精确版本目录内")
            if not source.is_file():
                raise ValueError("缺少精确版本的 capture.py")
            if identifier not in self._classes:
                # 不同根目录可有同名插件；模块身份包含实际路径，避免互相覆盖。
                digest = hashlib.sha256(str(source.resolve()).encode()).hexdigest()
                module_name = f"phantom_capture_{digest}"
                spec = importlib.util.spec_from_file_location(module_name, source)
                if spec is None or spec.loader is None:
                    raise ValueError("无法创建截图插件模块")
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                try:
                    spec.loader.exec_module(module)
                    candidate = getattr(module, "Plugin", None)
                    if not isinstance(candidate, type):
                        raise ValueError("capture.py 必须导出 Plugin 类")
                    inspect.signature(candidate).bind(fps=fps)
                    self._classes[identifier] = candidate
                except Exception:
                    sys.modules.pop(module_name, None)
                    raise
            instance = self._classes[identifier](fps=fps)  # type: ignore[call-arg]
            for method_name in ("start", "stop", "set_fps", "get_latest_result"):
                method = getattr(instance, method_name, None)
                if not callable(method):
                    raise ValueError(f"缺少可调用接口 {method_name}")
                signature = inspect.signature(method)
                signature.bind()
                if method_name == "set_fps":
                    signature.bind(fps=fps)
            worker = cast(CaptureWorker, instance)
            if type(worker.is_running) is not bool or worker.is_running:
                raise ValueError("Plugin 构造后必须处于未启动状态")
            if not isinstance(worker.get_latest_result(), CaptureResult):
                raise ValueError("get_latest_result 必须返回 CaptureResult")
            return worker
        except Exception as error:
            raise CapturePluginError(f"截图插件 {identifier}：{error}") from error
