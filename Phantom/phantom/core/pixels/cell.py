"""
Summary:
    解析通用或条件 Cell 的内部颜色与亮度。
Description:
    保留完整 4×4 快照，仅使用中间 2×2 计算；逻辑坐标只用于生成基板定位信息。
Key Variables:
    x: Lua Cell 列号。
    y: Lua Cell 行号。
    inner: 中间 2×2 RGB 像素。
Change Log:
    2026-09-12: Added Cell 亮度、颜色与严格纯色判断。
"""

import numpy as np

from ._region import PixelRegion, RGBImage


class Cell(PixelRegion):
    def __init__(self, x: int, y: int, pix_array: RGBImage) -> None:
        super().__init__(pix_array, (4, 4))
        self.x: int = x
        self.y: int = y
        self.inner: RGBImage = self.pix_array[1:3, 1:3]

    @property
    def pos(self) -> tuple[int, int]:
        return 4 * self.x, 4 * (self.y - 1)

    @property
    def mean(self) -> float:
        return float(np.mean(self.inner))

    @property
    def ratio(self) -> float:
        return self.mean / 255.0

    @property
    def percent(self) -> float:
        return self.ratio * 100.0

    @property
    def is_pure(self) -> bool:
        return bool(np.all(self.inner == self.inner[0, 0]))

    @property
    def is_not_pure(self) -> bool:
        return not self.is_pure

    @property
    def color_string(self) -> str:
        return ",".join(str(int(component)) for component in self.inner[0, 0])

    @property
    def is_black(self) -> bool:
        return bool(np.all(self.inner == 0))

    @property
    def is_white(self) -> bool:
        return bool(np.all(self.inner == 255))
