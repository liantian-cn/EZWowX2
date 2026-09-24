"""
Summary:
    解析 IconTile 内部纯色、空槽及图像 hash。
Description:
    仅分析内部 6×6 RGB 像素，全黑返回 None；其他图像按连续字节计算并缓存 xxh3 hash。
Key Variables:
    x: 从 1 开始的 Lua 图标槽位编号。
    inner: 内部 6×6 RGB 像素。
    _hash_cache: 当前独立快照的 hash 缓存。
Change Log:
    2026-09-12: Added IconTile 空槽检测与缓存 hash。
"""

import numpy as np
import xxhash

from ._region import PixelRegion, RGBImage


class IconTile(PixelRegion):
    def __init__(self, x: int, pix_array: RGBImage) -> None:
        super().__init__(pix_array, (8, 8))
        self.x: int = x
        self.inner: RGBImage = self.pix_array[1:7, 1:7]
        self._hash_cache: str | None = None

    @property
    def pos(self) -> tuple[int, int]:
        return 4 + 8 * (self.x - 1), 12

    @property
    def is_black(self) -> bool:
        return bool(np.all(self.inner == 0))

    @property
    def is_pure(self) -> bool:
        return bool(np.all(self.inner == self.inner[0, 0]))

    @property
    def is_not_pure(self) -> bool:
        return not self.is_pure

    @property
    def hash(self) -> str | None:
        if self.is_black:
            return None
        if self._hash_cache is None:
            self._hash_cache = xxhash.xxh3_64_hexdigest(np.ascontiguousarray(self.inner).tobytes(), seed=0)
        return self._hash_cache
