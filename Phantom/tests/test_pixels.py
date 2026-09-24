from __future__ import annotations

from typing import cast

import numpy as np
import pytest
import xxhash
from numpy.typing import NDArray

from demo.demo01 import describe_result
from phantom.core.capture.contracts import CaptureResult, CaptureStatus
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar


def board_image() -> NDArray[np.uint8]:
    image = np.full((20, 40, 3), (255, 0, 0), dtype=np.uint8)
    for row in range(2):
        for column in range(1, 9):
            image[row * 4 : row * 4 + 4, column * 4 : column * 4 + 4] = row * 10 + column
    # Lua x=1,width=2 的完整红边占位；白色内容占 3/8。
    image[8:12, 6:14] = 0
    image[8:12, 6:9] = 255
    # 第二条从 x=1+2+1=4 开始。
    image[8:12, 18:22] = 255
    image[12:20, 4:12] = 0
    image[12:20, 12:20] = np.arange(8 * 8 * 3, dtype=np.uint8).reshape(8, 8, 3)
    return image


def test_lua_layout_and_adjacent_regions() -> None:
    image = board_image()
    decoder = PixelDecoder(image)
    for y in (1, 2):
        for x in range(1, 9):
            cell = decoder.getCell(x, y)
            assert cell.mean == (y - 1) * 10 + x
            assert cell.pos == (4 * x, 4 * (y - 1))
    assert decoder.getCell(1, 1).region_string == "4,0,8,4"
    assert decoder.getCell(1, 2).pos_string == "4,4"
    bar = decoder.getValueBar(1, 2)
    assert bar.region == (4, 8, 16, 12)
    assert bar.pos_string == "4,8"
    assert bar.pix_array.shape == (4, 12, 3)
    assert bar.inner.shape == (2, 12, 3)
    assert bar.ratio == 3 / 8 and bar.percent == 37.5
    assert decoder.getValueBar(4, 1).ratio == 1.0
    assert decoder.getIconTile(1).hash is None
    tile = decoder.getIconTile(2)
    assert tile.region == (12, 12, 20, 20)
    assert tile.pos_string == "12,12"
    assert tile.region_string == "12,12,20,20"
    expected = xxhash.xxh3_64_hexdigest(image[13:19, 13:19].tobytes(), seed=0)
    assert tile.hash == expected
    assert decoder.getIconTile(4).region == (28, 12, 36, 20)


def test_cell_uses_inner_rgb_and_ignores_border() -> None:
    pixels = np.full((4, 4, 3), 255, dtype=np.uint8)
    pixels[1:3, 1:3] = (12, 24, 36)
    cell = Cell(8, 2, pixels)
    assert cell.mean == 24.0
    assert cell.ratio == pytest.approx(24 / 255)
    assert cell.percent == pytest.approx(24 / 255 * 100)
    assert cell.color_string == "12,24,36"
    assert cell.is_pure and not cell.is_not_pure
    assert not cell.is_black and not cell.is_white
    pixels[2, 2] = (0, 0, 1)
    mixed = Cell(1, 1, pixels)
    assert mixed.is_not_pure and not mixed.is_pure
    assert mixed.mean == pytest.approx((3 * 72 + 1) / 12)
    assert mixed.color_string == "12,24,36"


@pytest.mark.parametrize("gray", [0, 1, 254, 255])
def test_cell_exact_black_white(gray: int) -> None:
    pixels = np.full((4, 4, 3), (255, 0, 0), dtype=np.uint8)
    pixels[1:3, 1:3] = gray
    cell = Cell(1, 1, pixels)
    assert cell.is_black == (gray == 0)
    assert cell.is_white == (gray == 255)


def test_bar_excludes_border_rows_and_non_black_white_pixels() -> None:
    pixels = np.full((4, 12, 3), 255, dtype=np.uint8)
    pixels[1:3] = (255, 0, 0)
    assert ValueBar(1, 2, pixels).ratio == 0.0
    pixels[1, 2] = 255
    pixels[2, 2:5] = 0
    pixels[1, 5] = (255, 255, 254)
    pixels[1, 6] = (0, 0, 1)
    pixels[2, 6] = (0, 255, 0)
    bar = ValueBar(1, 2, pixels)
    assert bar.ratio == 0.25 and bar.percent == 25.0
    pixels[1, 2] = 0
    assert ValueBar(1, 2, pixels).percent == 0.0


def test_icon_entire_inner_and_cached_independent_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    pixels = np.full((8, 8, 3), 255, dtype=np.uint8)
    pixels[1:7, 1:7] = 0
    empty = IconTile(1, pixels)
    assert empty.is_black and empty.is_pure and empty.hash is None
    # 中心仍为黑色，但内部角落非黑，不能按参考项目的中心 2×2 判空。
    pixels[1, 1] = (0, 0, 1)
    tile = IconTile(2, pixels)
    assert not tile.is_black and tile.is_not_pure
    digest = tile.hash
    assert digest is not None and len(digest) == 16 and digest == digest.lower()

    def unexpected_hash(data: bytes, seed: int = 0) -> str:
        raise AssertionError("同一快照不应重复计算 hash")

    monkeypatch.setattr(xxhash, "xxh3_64_hexdigest", unexpected_hash)
    pixels[:] = 0
    assert tile.hash == digest and not tile.is_black
    with pytest.raises(ValueError):
        tile.inner[0, 0] = 255
    with pytest.raises(ValueError):
        tile.pix_array.setflags(write=True)


def test_non_contiguous_input_and_coordinates_do_not_affect_analysis() -> None:
    image = board_image()
    storage = np.zeros((20, 80, 3), dtype=np.uint8)
    storage[:, ::2] = image
    non_contiguous = storage[:, ::2]
    assert not non_contiguous.flags.c_contiguous
    decoder = PixelDecoder(non_contiguous)
    assert decoder.getValueBar(1, 2).ratio == 3 / 8
    tile = decoder.getIconTile(2)
    assert tile.hash == PixelDecoder(image).getIconTile(2).hash
    assert IconTile(99, tile.pix_array).hash == tile.hash
    assert Cell(99, 99, image[:4, 4:8]).mean == 1.0
    assert ValueBar(99, 2, image[8:12, 4:16]).ratio == 3 / 8


@pytest.mark.parametrize("shape", [(19, 40, 3), (20, 7, 3), (20, 41, 3), (20, 40, 4)])
def test_invalid_board_shape(shape: tuple[int, int, int]) -> None:
    with pytest.raises(ValueError):
        PixelDecoder(np.zeros(shape, dtype=np.uint8))


def test_invalid_requests_and_region_shapes() -> None:
    decoder = PixelDecoder(board_image())
    for x in (0, -1, 9, True):
        with pytest.raises(ValueError):
            decoder.getCell(x, 1)
    for y in (0, 3, True):
        with pytest.raises(ValueError):
            decoder.getCell(1, y)
    for width in (0, -1, 8, True):
        with pytest.raises(ValueError):
            decoder.getValueBar(1, width)
    for x in (0, -1, 5, True):
        with pytest.raises(ValueError):
            decoder.getIconTile(x)
    with pytest.raises(ValueError):
        Cell(1, 1, np.zeros((2, 2, 3), dtype=np.uint8))
    with pytest.raises(ValueError):
        IconTile(1, np.zeros((8, 7, 3), dtype=np.uint8))
    with pytest.raises(ValueError):
        ValueBar(1, 2, np.zeros((4, 8, 3), dtype=np.uint8))


def test_invalid_dtype_channels_and_non_integer_arguments() -> None:
    for image in (np.zeros((20, 40, 3), dtype=np.float64), np.zeros((20, 40), dtype=np.uint8)):
        with pytest.raises(ValueError):
            PixelDecoder(cast(NDArray[np.uint8], image))
    decoder = PixelDecoder(board_image())
    with pytest.raises(ValueError):
        decoder.getCell(cast(int, 1.5), 1)
    with pytest.raises(ValueError):
        decoder.getValueBar(1, cast(int, 2.5))
    with pytest.raises(ValueError):
        decoder.getValueBar(0, 2)


def test_demo_reports_same_frame_and_rejects_failed_images() -> None:
    image = board_image()
    lines = describe_result(CaptureResult(image))
    assert len(lines) == 13
    assert "mean=1.000000" in lines[0]
    assert "mean=15.000000" in lines[9]
    assert "ratio=0.375000, percent=37.500000" in lines[10]
    assert "hash=None" in lines[11]
    with pytest.raises(ValueError, match="颜色错误"):
        describe_result(CaptureResult(image, CaptureStatus(True, "颜色错误")))
    with pytest.raises(ValueError, match="没有返回图像"):
        describe_result(CaptureResult())
