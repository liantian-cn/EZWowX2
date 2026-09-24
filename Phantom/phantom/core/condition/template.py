"""
Summary:
    用插件参数与冻结布局渲染一个条件实例的 Lua。
Description:
    核心保留 uuid 与区域坐标参数的控制权；未知占位符明确失败。
Key Variables:
    regions: 已冻结的条件区域。
Change Log:
    2026-09-13: Changed 按确认计划拆分条件核心职责。
"""

import re
from pathlib import Path

from phantom.core.condition.contracts import Region


def render_template(path: Path, regions: tuple[Region, ...], parameters: dict[str, str], instance_id: str) -> str:
    values = dict(parameters)
    values["uuid"] = instance_id
    for index, region in enumerate(regions, 1):
        for name, value in region.metadata().items():
            values[f"{name}{index}"] = str(value)
    source = path.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            raise ValueError(f"模板缺少参数：{name}")
        return values[name]

    return re.sub(r"\{\{([a-zA-Z0-9_]+)\}\}", replace, source)
