"""
Summary:
    解析带红色分隔的 ValueBar 黑白比例。
Description:
    从完整占位的中间两行统计严格黑白像素，排除分隔和其他颜色，输出比例及百分数。
Key Variables:
    x: Lua 中包含左侧分隔的占位起点。
    width: 黑白内容宽度，以 Cell 为单位。
    inner: 完整占位中间两行的 RGB 像素。
Change Log:
    2026-09-12: Added ValueBar ratio 与 percent 解析。
"""

import numpy as np

from ._region import PixelRegion, RGBImage, positive_integer


class ValueBar(PixelRegion):
    def __init__(self, x: int, width: int, pix_array: RGBImage) -> None:
        positive_integer(width, "width")
        super().__init__(pix_array, (4, 4 * (width + 1)))
        self.x: int = x
        self.width: int = width
        self.inner: RGBImage = self.pix_array[1:3, :]

    @property
    def pos(self) -> tuple[int, int]:
        return 4 * self.x, 8

    @property
    def ratio(self) -> float:
        white_count = int(np.count_nonzero(np.all(self.inner == 255, axis=2)))
        black_count = int(np.count_nonzero(np.all(self.inner == 0, axis=2)))
        total_count = white_count + black_count
        return white_count / total_count if total_count else 0.0

    @property
    def percent(self) -> float:
        return self.ratio * 100.0
