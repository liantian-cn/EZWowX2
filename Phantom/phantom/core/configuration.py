"""
Summary:
    从启动工作目录读取 Phantom 应用配置，首次运行写入默认文件。
Description:
    配置只在启动时加载，与程序和 rotation 文件的位置无关。
    普通字段非法时明确失败；循环选择的局部错误记录警告并允许启动发现候选。
Key Variables:
    AppConfig.path: 启动工作目录中的配置文件绝对路径。
    AppConfig.fps: 截图与界面读取最新快照的频率上限。
Change Log:
    2026-09-19: Changed 使用平铺组合键管理多份 rotation，保留加载源供选择回写并发检查。
    2026-09-14: Changed 增加 keyboard.plugin 精确版本配置及默认值。
    2026-09-13: Changed 新增 capture.plugin，复用基础校验器。
    2026-09-12: Added 第 5、6 步的工作目录 TOML 配置。
    2026-09-12: Changed 支持单份 rotation、WoW 路径和生成包名。
"""

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from phantom.core.rotation import validate_addon_name
from phantom.core.specializations import SPECIALIZATION_BY_KEY
from phantom.core.validation import PositiveInteger, PositiveNumber, String, Table

DEFAULT_CONFIG = """[capture]
plugin = "gdi@dev"
fps = 15

[keyboard]
plugin = "post_message@dev"

[ui]
min_width = 120
min_height = 46
log_max_lines = 1000

[rotations]

[wow]
executable = ""

[addon]
name = "Phantom"
"""


class ConfigurationError(ValueError):
    """应用配置无法读取或不满足字段约束。"""


@dataclass(frozen=True)
class AppConfig:
    path: Path
    fps: float = 15
    capture_plugin: str = "gdi@dev"
    keyboard_plugin: str = "post_message@dev"
    min_width: int = 120
    min_height: int = 46
    log_max_lines: int = 1000
    rotation_paths: Mapping[str, Path] = field(default_factory=dict)
    wow_executable: Path | None = None
    addon_name: str = "Phantom"
    warnings: tuple[str, ...] = ()
    _source: str | None = field(default=None, repr=False, compare=False)


def _table(document: dict[str, object], name: str) -> dict[str, object]:
    return Table().validate(document.get(name, {}), f"[{name}]")


def _rotation_paths(document: dict[str, object], directory: Path, warnings: list[str]) -> dict[str, Path]:
    if "rotation" in document:
        warnings.append("旧 [rotation].path 已忽略，请使用 [rotations] 组合键配置")
    try:
        values = _table(document, "rotations")
    except ValueError as error:
        warnings.append(f"忽略非法 [rotations]：{error}")
        return {}
    result: dict[str, Path] = {}
    for key, value in values.items():
        if key not in SPECIALIZATION_BY_KEY:
            warnings.append(f"忽略非法 rotation 组合键：{key}")
        elif not isinstance(value, str) or not value.strip():
            warnings.append(f"忽略 rotations.{key}：路径必须为非空字符串")
        else:
            try:
                if "\x00" in value:
                    raise ValueError("路径包含空字符")
                result[key] = (directory / value).resolve()
            except (OSError, ValueError) as error:
                warnings.append(f"忽略 rotations.{key}：{error}")
    return result


def load_config(working_directory: Path) -> AppConfig:
    path = working_directory.resolve() / "phantom.toml"
    try:
        # 独占创建防止覆盖已有配置，包括存在检查与写入之间出现的新文件。
        try:
            with path.open("x", encoding="utf-8", newline="\n") as config_file:
                config_file.write(DEFAULT_CONFIG)
        except FileExistsError:
            pass
        source = path.read_bytes().decode("utf-8")
        document = tomllib.loads(source)
        capture = _table(document, "capture")
        keyboard = _table(document, "keyboard")
        ui = _table(document, "ui")
        wow = _table(document, "wow")
        addon = _table(document, "addon")
        wow_value = wow.get("executable", "")
        addon_name = addon.get("name", "Phantom")
        if not all(isinstance(value, str) for value in (wow_value, addon_name)):
            raise ConfigurationError("wow.executable 和 addon.name 必须为字符串")
        assert isinstance(wow_value, str)
        assert isinstance(addon_name, str)
        warnings: list[str] = []
        rotation_paths = _rotation_paths(document, path.parent, warnings)
        validate_addon_name(addon_name)
        fps_number = PositiveNumber().validate(capture.get("fps", 15), "capture.fps")
        capture_plugin = String().validate(capture.get("plugin", "gdi@dev"), "capture.plugin")
        return AppConfig(
            path=path,
            fps=fps_number,
            capture_plugin=capture_plugin,
            keyboard_plugin=String().validate(keyboard.get("plugin", "post_message@dev"), "keyboard.plugin"),
            min_width=PositiveInteger().validate(ui.get("min_width", 120), "ui.min_width"),
            min_height=PositiveInteger().validate(ui.get("min_height", 46), "ui.min_height"),
            log_max_lines=PositiveInteger().validate(ui.get("log_max_lines", 1000), "ui.log_max_lines"),
            rotation_paths=rotation_paths,
            wow_executable=(path.parent / wow_value).resolve() if wow_value else None,
            addon_name=addon_name,
            warnings=tuple(warnings),
            _source=source,
        )
    except (OSError, ValueError, OverflowError) as error:
        raise ConfigurationError(f"配置文件 {path}：{error}") from error
