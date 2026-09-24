import numpy as np
import xxhash
import logging

from .color_map import COLOR_MAP
from .title_manager import get_default_title_manager

__all__ = ["Cell", "MegaCell", "BadgeCell", "CharCell"]


class CellRegion(object):
    def __init__(self, pix_array: np.ndarray):
        self.valid_array: np.ndarray = pix_array
        self._hash_cache: str | None = None

    @property
    def mean(self) -> np.floating:
        return np.mean(self.valid_array)

    @property
    def decimal(self) -> np.floating:
        return self.mean / 255.0

    @property
    def percent(self) -> np.floating:
        return self.mean / 255.0 * 100

    @property
    def is_pure(self) -> bool:
        first_pixel: np.ndarray = self.valid_array[0, 0]
        return bool(np.all(self.valid_array == first_pixel))

    @property
    def is_not_pure(self) -> bool:
        return not self.is_pure

    @property
    def color(self) -> tuple[int, int, int]:
        pixel: np.ndarray = self.valid_array[0, 0]
        return (int(pixel[0]), int(pixel[1]), int(pixel[2]))

    @property
    def color_string(self) -> str:
        return f"{self.color[0]},{self.color[1]},{self.color[2]}"

    @property
    def is_black(self) -> bool:
        return self.is_pure and tuple(self.color) == (0, 0, 0)

    @property
    def is_white(self) -> bool:
        return self.is_pure and tuple(self.color) == (255, 255, 255)

    @property
    def is_not_black(self) -> bool:
        return not self.is_black

    @property
    def white_count(self) -> int:
        white_mask = np.all(self.valid_array == (255, 255, 255), axis=2)
        return int(np.count_nonzero(white_mask))

    @property
    def remaining(self) -> float:
        gray: int = int(self.mean)
        if gray <= 0:
            return 0.0
        if gray >= 255:
            return 375.0
        if gray <= 100:
            return 5.0 * gray / 100
        if gray <= 150:
            return 5.0 + 25.0 * (gray - 100) / 50
        if gray <= 200:
            return 30.0 + 125.0 * (gray - 150) / 50
        return 155.0 + 220.0 * (gray - 200) / 55


class Cell(CellRegion):
    def __init__(self, x: int, y: int, pix_array: np.ndarray) -> None:
        self.x: int = x
        self.y: int = y
        self.pix_array: np.ndarray = pix_array
        inner = pix_array[1:3, 1:3]
        super().__init__(inner)

    @property
    def is_black(self) -> bool:
        return self.is_pure and tuple(self.color) == (0, 0, 0)

    @property
    def is_green(self) -> bool:
        return self.is_pure and tuple(self.color) == (0, 255, 0)

    @property
    def is_white(self) -> bool:
        return self.is_pure and tuple(self.color) == (255, 255, 255)

    @property
    def is_not_black(self) -> bool:
        if (not self.is_green) and (not self.is_black):
            logging.warning(f"坐标在 ({self.x}, {self.y}) 的单元格不是二元色, 颜色: {self.color_string}，发生串色，考虑抗锯齿、插帧、缩放异常。")
        return not self.is_black


class MegaCell(CellRegion):
    def __init__(self, x: int, y: int, pix_array: np.ndarray) -> None:
        self.x: int = x
        self.y: int = y
        self.pix_array: np.ndarray = pix_array
        self._hash_cache: str | None = None
        inner = pix_array[1:7, 1:7]
        super().__init__(inner)

    @property
    def cell_type(self) -> str:
        return "NONE"

    @property
    def hash(self) -> str:
        if self._hash_cache is None:
            self._hash_cache = xxhash.xxh3_64_hexdigest(np.ascontiguousarray(self.valid_array), seed=0)
        return self._hash_cache

    @property
    def title(self) -> str:
        manager = get_default_title_manager()
        return manager.get_title(self.valid_array, self.cell_type, self.hash)


class BadgeCell(CellRegion):
    def __init__(self, x: int, y: int, pix_array: np.ndarray) -> None:
        self.x: int = x
        self.y: int = y
        self.pix_array: np.ndarray = pix_array
        self._hash_cache: str | None = None
        inner = pix_array[1:7, 1:7]
        super().__init__(inner)
        self._footnote = CellRegion(self.pix_array[-2:, -2:])
        self._core = CellRegion(pix_array[3:5, 3:5])  # 一个极中间的区域，判断是否为黑色。

    @property
    def is_black(self) -> bool:
        return self._core.is_black

    @property
    def footnote(self) -> CellRegion:
        return self._footnote

    @property
    def footnote_color_string(self) -> str:
        return self._footnote.color_string

    @property
    def cell_type(self) -> str:
        return COLOR_MAP["SPELL_TYPE"].get(self.footnote_color_string, "UNKNOWN")

    @property
    def hash(self) -> str:
        if self._hash_cache is None:
            self._hash_cache = xxhash.xxh3_64_hexdigest(np.ascontiguousarray(self.valid_array), seed=0)
        return self._hash_cache

    @property
    def title(self) -> str:
        manager = get_default_title_manager()
        return manager.get_title(self.valid_array, self.cell_type, self.hash)


class CharCell(CellRegion):
    def __init__(self, x: int, y: int, pix_array: np.ndarray) -> None:
        self.x: int = x
        self.y: int = y
        self.pix_array: np.ndarray = pix_array
        super().__init__(pix_array)

    @property
    def count(self) -> int:
        white_count = self.white_count
        if white_count <= 9:
            return white_count
        if white_count == 10:
            return 0
        if white_count >= 11:
            return 10
        return 0
