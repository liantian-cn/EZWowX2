"""
Summary:
    按 Lua 布局将完整像素基板切分为通用解析区域。
Description:
    校验 RGB 基板及内容边界，按相同 Lua 入参切分 Cell、ValueBar、IconTile 并返回实例。
Key Variables:
    pix_array: 包含两侧检测列的完整基板 RGB 数组。
Change Log:
    2026-09-12: Added 与 Lua 坐标一致的 PixelDecoder。
"""

from ._region import RGBImage, positive_integer, validate_image
from .cell import Cell
from .icon_tile import IconTile
from .value_bar import ValueBar


class PixelDecoder:
    def __init__(self, pix_array: RGBImage) -> None:
        validate_image(pix_array)
        height, width = pix_array.shape[:2]
        if height != 20 or width < 8 or width % 4:
            raise ValueError("完整基板高度必须为 20，宽度至少为 8 且为 4 的倍数")
        self.pix_array: RGBImage = pix_array

    def _crop(self, left: int, top: int, width: int, height: int) -> RGBImage:
        if left < 4 or left + width > self.pix_array.shape[1] - 4:
            raise ValueError("请求区域超出基板内容区或进入检测列")
        return self.pix_array[top : top + height, left : left + width]

    def getCell(self, x: int, y: int) -> Cell:
        positive_integer(x, "x")
        positive_integer(y, "y")
        if y not in (1, 2):
            raise ValueError("Cell 的 y 必须为 1 或 2")
        return Cell(x, y, self._crop(4 * x, 4 * (y - 1), 4, 4))

    def getValueBar(self, x: int, width: int) -> ValueBar:
        positive_integer(x, "x")
        positive_integer(width, "width")
        return ValueBar(x, width, self._crop(4 * x, 8, 4 * (width + 1), 4))

    def getIconTile(self, x: int) -> IconTile:
        positive_integer(x, "x")
        return IconTile(x, self._crop(4 + 8 * (x - 1), 12, 8, 8))
