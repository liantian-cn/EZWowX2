"""
Summary:
    管理像素区域的独立快照与基板定位信息。
Description:
    构造时校验 RGB 图像并创建只读快照；统一输出半开矩形及坐标字符串。
Key Variables:
    pix_array: 已切分的完整区域快照。
Change Log:
    2026-09-12: Added NumPy 像素解析所需的区域快照与定位边界。
"""

import numpy as np
from numpy.typing import NDArray

type RGBImage = NDArray[np.uint8]


def positive_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} 必须为正整数")


def validate_image(image: RGBImage) -> None:
    if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("图像必须是 RGB uint8 三通道数组")


class PixelRegion:
    def __init__(self, pix_array: RGBImage, shape: tuple[int, int]) -> None:
        validate_image(pix_array)
        if pix_array.shape[:2] != shape:
            raise ValueError(f"区域尺寸必须为 {shape}，实际为 {pix_array.shape[:2]}")
        # bytes 提供不可写的独立底层存储，输入后续变化不会使缓存失效。
        self.pix_array: RGBImage = np.frombuffer(pix_array.tobytes(), dtype=np.uint8).reshape(*shape, 3)

    @property
    def pos(self) -> tuple[int, int]:
        raise NotImplementedError

    @property
    def region(self) -> tuple[int, int, int, int]:
        left, top = self.pos
        height, width = self.pix_array.shape[:2]
        return left, top, left + width, top + height

    @property
    def pos_string(self) -> str:
        return ",".join(map(str, self.pos))

    @property
    def region_string(self) -> str:
        return ",".join(map(str, self.region))
