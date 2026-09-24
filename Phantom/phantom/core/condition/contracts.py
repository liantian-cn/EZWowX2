"""
Summary:
    声明不可变条件输出和布局区域。
Description:
    输出业务类型与区域数量独立；冻结区域使用 Lua 构造器的坐标单位。
Key Variables:
    Output: 输出类型、数量、业务类型与形状。
    Region: 分配后的坐标与宽度。
Change Log:
    2026-09-14: Changed 增加不分配像素区域的 none 输出契约。
    2026-09-13: Changed 按确认计划拆分条件核心职责。
"""

from dataclasses import dataclass
from typing import Literal

from phantom.core.pixels import Cell, IconTile, ValueBar

type Scalar = bool | int | float | str
type Value = Scalar | list[Scalar]
type Raw = tuple[list[Cell], list[ValueBar], list[IconTile]]
type OutputType = Literal["cell", "value_bar", "icon_tile", "none"]


@dataclass(frozen=True)
class Output:
    output_type: OutputType
    output_count: int = 1
    value_type: type[bool] | type[int] | type[float] | type[str] = float
    value_shape: Literal["scalar", "list"] = "scalar"
    widths: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.output_type not in ("cell", "value_bar", "icon_tile", "none"):
            raise ValueError("未知输出类型")
        if type(self.output_count) is not int:
            raise ValueError("输出数量必须为整数")
        if self.output_type == "none":
            if self.output_count != 0:
                raise ValueError("none 输出数量必须为 0")
        elif self.output_count < 1:
            raise ValueError("输出数量必须为正整数")
        if self.value_type not in (bool, int, float, str):
            raise ValueError("未知业务值类型")
        if self.value_shape not in ("scalar", "list"):
            raise ValueError("未知业务值形状")
        if self.output_type == "value_bar":
            if len(self.widths) != self.output_count or any(type(width) is not int or width < 1 for width in self.widths):
                raise ValueError("每条 ValueBar 必须声明正整数内容宽度")
        elif self.widths:
            raise ValueError("只有 ValueBar 可以声明宽度")

    def accepts(self, value: Value) -> bool:
        if self.value_shape == "list":
            return isinstance(value, list) and all(type(item) is self.value_type for item in value)
        return type(value) is self.value_type


@dataclass(frozen=True)
class Region:
    x: int
    y: int | None = None
    width: int | None = None

    def metadata(self) -> dict[str, int]:
        result = {"x": self.x}
        if self.y is not None:
            result["y"] = self.y
        if self.width is not None:
            result["width"] = self.width
        return result
