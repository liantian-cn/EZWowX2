"""Pixel grid primitives and decoder."""

from typing import Any

import numpy as np
import xxhash

from .database import IconTitleRepository
from ..utils.image_utils import COLOR_MAP


class PixelRegion:
    """A rectangular RGB pixel region."""

    def __init__(self, pix_array: np.ndarray):
        self.pix_array: np.ndarray = pix_array
        self._hash_cache: str | None = None

    @property
    def array(self) -> np.ndarray:
        return self.pix_array

    @property
    def hash(self) -> str:
        if self._hash_cache is None:
            self._hash_cache = xxhash.xxh3_64_hexdigest(np.ascontiguousarray(self.pix_array), seed=0)
        return self._hash_cache

    @property
    def mean(self) -> np.floating:
        return np.mean(self.pix_array)

    @property
    def decimal(self) -> np.floating:
        return self.mean / 255.0

    @property
    def percent(self) -> np.floating:
        return self.mean / 255.0 * 100

    @property
    def is_pure(self) -> bool:
        first_pixel: np.ndarray = self.pix_array[0, 0]
        return bool(np.all(self.pix_array == first_pixel))

    @property
    def is_not_pure(self) -> bool:
        return not self.is_pure

    @property
    def color(self) -> tuple[int, int, int]:
        pixel: np.ndarray = self.pix_array[0, 0]
        return (int(pixel[0]), int(pixel[1]), int(pixel[2]))

    @property
    def color_string(self) -> str:
        return f'{self.color[0]},{self.color[1]},{self.color[2]}'

    @property
    def is_black(self) -> bool:
        return self.is_pure and tuple(self.color) == (0, 0, 0)

    @property
    def is_white(self) -> bool:
        return self.is_pure and tuple(self.color) == (255, 255, 255)

    @property
    def is_red(self) -> bool:
        return self.is_pure and tuple(self.color) == (255, 0, 0)

    @property
    def is_green(self) -> bool:
        return self.is_pure and tuple(self.color) == (0, 255, 0)

    @property
    def is_blue(self) -> bool:
        return self.is_pure and tuple(self.color) == (0, 0, 255)

    @property
    def white_count(self) -> int:
        return int(np.count_nonzero(np.all(self.pix_array == (255, 255, 255), axis=2)))

    @property
    def remaining(self) -> float:
        y: int = int(self.mean)
        points: list[tuple[float, int]] = [(0.0, 0), (5.0, 100), (30.0, 150), (155.0, 200), (375.0, 255)]
        if y <= points[0][1]:
            return points[0][0]
        if y >= points[-1][1]:
            return points[-1][0]
        for i in range(len(points) - 1):
            x1: float
            y1: int
            x2: float
            y2: int
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            if y1 <= y <= y2:
                return x1 + (x2 - x1) * (y - y1) / (y2 - y1)
        return 0.0


class GridCell:
    """A fixed-size 8x8 cell in the pixel grid."""

    _title_repository: IconTitleRepository | None = None

    def __init__(self, x: int, y: int, img_array: np.ndarray) -> None:
        self.x: int = x
        self.y: int = y
        self.pix_array: np.ndarray = img_array
        self._full: PixelRegion | None = None
        self._middle: PixelRegion | None = None
        self._inner: PixelRegion | None = None
        self._sub: list[PixelRegion] | None = None
        self._footnote: PixelRegion | None = None

    @classmethod
    def set_title_repository(cls, repository: IconTitleRepository) -> None:
        cls._title_repository = repository

    @property
    def full(self) -> PixelRegion:
        if self._full is None:
            self._full = PixelRegion(self.pix_array)
        return self._full

    @property
    def middle(self) -> PixelRegion:
        if self._middle is None:
            self._middle = PixelRegion(self.pix_array[1:7, 1:7])
        return self._middle

    @property
    def inner(self) -> PixelRegion:
        if self._inner is None:
            self._inner = PixelRegion(self.pix_array[2:6, 2:6])
        return self._inner

    @property
    def sub_node(self) -> tuple[PixelRegion, PixelRegion, PixelRegion, PixelRegion]:
        if self._sub is None:
            self._sub = [
                PixelRegion(self.pix_array[1:3, 1:3]),
                PixelRegion(self.pix_array[1:3, 5:7]),
                PixelRegion(self.pix_array[5:7, 1:3]),
                PixelRegion(self.pix_array[5:7, 5:7]),
            ]
        return self._sub[0], self._sub[1], self._sub[2], self._sub[3]

    @property
    def mixed_node(self) -> tuple[PixelRegion, PixelRegion, PixelRegion, PixelRegion]:
        return self.sub_node

    @property
    def footnote(self) -> PixelRegion:
        if self._footnote is None:
            self._footnote = PixelRegion(self.pix_array[-2:, -2:])
        return self._footnote

    @property
    def mean(self) -> np.floating:
        return self.inner.mean

    @property
    def mean_value(self) -> np.floating:
        return self.inner.mean

    @property
    def value_percent(self) -> np.floating:
        return self.inner.percent

    @property
    def percent(self) -> np.floating:
        return self.inner.percent

    @property
    def value_decimal(self) -> np.floating:
        return self.inner.decimal

    @property
    def decimal(self) -> np.floating:
        return self.inner.decimal

    @property
    def is_pure(self) -> bool:
        return self.inner.is_pure

    @property
    def is_not_pure(self) -> bool:
        return self.inner.is_not_pure

    @property
    def is_black(self) -> bool:
        return self.inner.is_black

    @property
    def is_white(self) -> bool:
        return self.inner.is_white

    @property
    def color(self) -> tuple[int, int, int]:
        return self.inner.color

    @property
    def color_string(self) -> str:
        return self.inner.color_string

    @property
    def white_count(self) -> int:
        if self.inner.is_pure:
            return 0
        white_count = self.middle.white_count
        if white_count <= 9:
            return white_count
        if white_count == 10:
            return 0
        if white_count >= 11:
            return 20
        return 0

    @property
    def remaining(self) -> float:
        return self.inner.remaining

    @property
    def hash(self) -> str:
        return self.middle.hash

    @property
    def title(self) -> str:
        if GridCell._title_repository is not None:
            return GridCell._title_repository.get_title(
                middle_hash=self.middle.hash,
                middle_array=self.middle.array,
                full_array=self.full.array
            )
        return self.hash

    @property
    def footnote_title(self) -> str:
        if self.footnote.is_pure:
            return COLOR_MAP['IconType'].get(self.footnote.color_string, 'Unknown')
        return 'Unknown'


class GridDecoder:
    """Decoder that reads grid cells and high-level sequences."""

    def __init__(self, img_array: np.ndarray) -> None:
        self.pix_array: np.ndarray = img_array

    def cell(self, x: int, y: int) -> GridCell:
        start_x: int = x * 8
        start_y: int = y * 8
        end_x: int = start_x + 8
        end_y: int = start_y + 8
        max_x: int = self.pix_array.shape[1] // 8
        max_y: int = self.pix_array.shape[0] // 8
        if x >= max_x or y >= max_y:
            raise ValueError(f'节点坐标 ({x},{y}) 超出范围 (最大 {max_x},{max_y})')
        array: np.ndarray = self.pix_array[start_y:end_y, start_x:end_x]
        return GridCell(x, y, array)

    def read_health_bar(self, left: int, top: int, length: int) -> float:
        nodes_middle_pix: list[np.ndarray] = [self.cell(x, top).full.array[3:5, :] for x in range(left, left + length)]
        white_count = sum(np.count_nonzero(np.all(node == (255, 255, 255), axis=2)) for node in nodes_middle_pix)
        total_count: int = sum(node.shape[0] * node.shape[1] for node in nodes_middle_pix)
        return white_count / total_count if total_count > 0 else 0.0

    def read_spell_sequence(self, left: int, top: int, length: int) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        result_sequence: list[dict[str, Any]] = []
        result_dict: dict[str, dict[str, Any]] = {}
        for x in range(left, left + length):
            icon_node: GridCell = self.cell(x, top)
            if icon_node.is_pure and icon_node.is_black:
                continue
            mix_node: GridCell = self.cell(x, top + 1)
            charge_node: GridCell = self.cell(x, top + 2)
            cooldown_block, usable_block, height_block, known_block = mix_node.mixed_node
            spell = {
                'title': icon_node.title,
                'remaining': cooldown_block.remaining,
                'height': height_block.is_white,
                'charge': int(charge_node.white_count) if not (charge_node.is_pure and charge_node.is_black) else 0,
                'known': known_block.is_white,
                'usable': usable_block.is_white
            }
            result_sequence.append(spell)
            result_dict[icon_node.title] = spell
        return result_sequence, result_dict

    def read_aura_sequence(self, left: int, top: int, length: int) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        result_sequence: list[dict[str, Any]] = []
        result_dict: dict[str, dict[str, Any]] = {}
        for x in range(left, left + length):
            icon_node: GridCell = self.cell(x, top)
            if icon_node.is_pure and icon_node.is_black:
                continue
            mix_node: GridCell = self.cell(x, top + 1)
            count_node: GridCell = self.cell(x, top + 2)
            remain_block, type_block, forever_block, _empty = mix_node.mixed_node
            aura = {
                'title': icon_node.title,
                'remaining': 0.0 if remain_block.is_black else remain_block.remaining,
                'type': COLOR_MAP['IconType'].get(type_block.color_string, 'Unknown'),
                'count': count_node.white_count,
                'forever': forever_block.is_white
            }
            result_sequence.append(aura)
            result_dict[icon_node.title] = aura
        return result_sequence, result_dict
