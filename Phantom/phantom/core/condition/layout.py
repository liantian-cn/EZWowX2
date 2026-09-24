"""
Summary:
    按条件声明顺序分配三类独立输出区域。
Description:
    每行紧密排列，ValueBar 包含分隔占位，返回含两侧检测列的画布宽度。
Key Variables:
    next_x: 各类输出的下一可用位置。
Change Log:
    2026-09-13: Changed 按确认计划拆分条件核心职责。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import OutputType, Region


def allocate(conditions: list[Condition]) -> int:
    """按同类出现顺序独立排列，返回包含检测列的基板物理宽度。"""
    next_x: dict[OutputType, int] = {"cell": 1, "value_bar": 1, "icon_tile": 1}
    for condition in conditions:
        kind = condition.output.output_type
        regions: list[Region] = []
        for index in range(condition.output.output_count):
            width = condition.output.widths[index] if kind == "value_bar" else None
            regions.append(Region(next_x[kind], 2 if kind == "cell" else None, width))
            next_x[kind] += width + 1 if width is not None else 1
        condition.freeze(tuple(regions))
    content = max(5, next_x["cell"] - 1, next_x["value_bar"] - 1, 2 * (next_x["icon_tile"] - 1))
    return (content + 2) * 4
