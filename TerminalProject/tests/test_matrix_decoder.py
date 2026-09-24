import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from terminal.pixelcalc.matrix import MatrixDecoder


def _build_matrix(width_cells: int = 84, height_cells: int = 28) -> np.ndarray:
    return np.zeros((height_cells * 4, width_cells * 4, 3), dtype=np.uint8)


def _set_cell(matrix: np.ndarray, x: int, y: int, color: tuple[int, int, int]) -> None:
    start_x = x * 4
    start_y = y * 4
    matrix[start_y:start_y + 4, start_x:start_x + 4] = color


def _set_utf_cells(matrix: np.ndarray, x: int, y: int, chars: list[str], length: int) -> None:
    for index in range(length):
        if index < len(chars):
            encoded = list(chars[index].encode("utf-8"))
            encoded.extend([0] * (3 - len(encoded)))
            color = (encoded[0], encoded[1], encoded[2])
        else:
            color = (0, 0, 0)
        _set_cell(matrix, x + index, y, color)


def test_read_utf_string_returns_wrapped_title_only() -> None:
    matrix_data = _build_matrix()
    wrapped_chars = list("*#炎爆术*#")
    _set_utf_cells(matrix_data, 66, 26, wrapped_chars, 16)
    decoder = MatrixDecoder(matrix_data)

    result = decoder.readUTFString(66, 26, 16)

    assert result == "炎爆术"


def test_read_utf_string_returns_none_without_wrapped_title() -> None:
    matrix_data = _build_matrix()
    _set_utf_cells(matrix_data, 66, 26, list("abcdefghijklmnop"), 16)
    decoder = MatrixDecoder(matrix_data)

    result = decoder.readUTFString(66, 26, 16)

    assert result is None


def test_read_utf_string_returns_none_for_invalid_utf8_bytes() -> None:
    matrix_data = _build_matrix()
    _set_cell(matrix_data, 66, 26, (255, 255, 255))
    decoder = MatrixDecoder(matrix_data)

    result = decoder.readUTFString(66, 26, 16)

    assert result is None


def test_read_utf_string_returns_none_for_non_pure_cell() -> None:
    matrix_data = _build_matrix()
    matrix_data[26 * 4:(26 * 4) + 4, 66 * 4:(66 * 4) + 4] = 0
    matrix_data[(26 * 4) + 1, (66 * 4) + 1] = (42, 0, 0)
    decoder = MatrixDecoder(matrix_data)

    result = decoder.readUTFString(66, 26, 16)

    assert result is None
