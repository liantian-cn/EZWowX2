import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from terminal.pixelcalc import extractor
from terminal.pixelcalc.title_manager import TitleManager, ndarray_to_hash


class _FakeCell:
    def __init__(
        self,
        *,
        mean: float = 0.0,
        decimal: float = 0.0,
        is_not_black: bool = False,
    ) -> None:
        self.mean = mean
        self.decimal = decimal
        self.is_not_black = is_not_black


class _FakeBadgeCell:
    def __init__(self, *, title: str, cell_type: str, valid_array: np.ndarray) -> None:
        self.title = title
        self.cell_type = cell_type
        self.valid_array = valid_array


class _FakeMatrix:
    def __init__(self, *, utf_hash: str, utf_string: str, utf_badge_cell: _FakeBadgeCell) -> None:
        self._utf_hash = utf_hash
        self._utf_string = utf_string
        self._utf_badge_cell = utf_badge_cell
        self._cell_map: dict[tuple[int, int], _FakeCell] = {
            (56, 9): _FakeCell(mean=12.0),
            (58, 9): _FakeCell(is_not_black=False),
            (54, 9): _FakeCell(mean=255.0),
            (55, 9): _FakeCell(is_not_black=False),
            (57, 9): _FakeCell(mean=30.0),
            (82, 0): _FakeCell(decimal=0.5),
            (83, 0): _FakeCell(is_not_black=True),
            (55, 10): _FakeCell(is_not_black=False),
            (70, 10): _FakeCell(is_not_black=False),
            (70, 12): _FakeCell(is_not_black=False),
        }

    def readSpell(self) -> list[dict]:
        return []

    def readAura(self, x: int, y: int, length: int = 11) -> list[dict]:
        return []

    def readCellList(self, x: int, y: int, length: int) -> dict[str, dict]:
        return {}

    def readBadgeCellList(self, x: int, y: int, length: int) -> list[str]:
        return []

    def readUTFhash(self, x: int, y: int) -> str | None:
        return self._utf_hash

    def readUTFString(self, x: int, y: int, length: int) -> str | None:
        return self._utf_string

    def getBadgeCell(self, x: int, y: int) -> _FakeBadgeCell:
        if (x, y) == (64, 26):
            return self._utf_badge_cell
        return _FakeBadgeCell(title="assist", cell_type="NONE", valid_array=np.zeros((6, 6, 3), dtype=np.uint8))

    def getCell(self, x: int, y: int) -> _FakeCell:
        return self._cell_map.get((x, y), _FakeCell())

    def readCharCell(self, x: int, y: int) -> int:
        return 1


def test_extract_all_data_marks_pending_utf_title_record_when_hash_not_persisted(
    monkeypatch,
    tmp_path: Path,
) -> None:
    valid_array = np.full((6, 6, 3), 7, dtype=np.uint8)
    utf_hash = ndarray_to_hash(valid_array)
    utf_badge = _FakeBadgeCell(title=utf_hash, cell_type="PLAYER_SPELL", valid_array=valid_array)
    matrix = _FakeMatrix(utf_hash=utf_hash, utf_string="测试标题", utf_badge_cell=utf_badge)
    manager = TitleManager(tmp_path / "title-manager.sqlite")

    monkeypatch.setattr(extractor, "get_default_title_manager", lambda: manager)
    monkeypatch.setattr(extractor, "get_player_status", lambda matrix: {})
    monkeypatch.setattr(extractor, "get_party_all", lambda matrix, y=19: {})

    try:
        data = extractor.extract_all_data(matrix)
    finally:
        manager.close()

    assert data["UTF_hash"] == utf_hash
    assert data["UTF_string"] == "测试标题"
    assert data["_pending_utf_title_record"] == {
        "hash": utf_hash,
        "title": "测试标题",
        "title_type": "PLAYER_SPELL",
        "valid_array": valid_array.tolist(),
    }


def test_extract_all_data_skips_pending_utf_title_record_when_hash_already_persisted(
    monkeypatch,
    tmp_path: Path,
) -> None:
    valid_array = np.full((6, 6, 3), 9, dtype=np.uint8)
    utf_hash = ndarray_to_hash(valid_array)
    utf_badge = _FakeBadgeCell(title=utf_hash, cell_type="PLAYER_SPELL", valid_array=valid_array)
    matrix = _FakeMatrix(utf_hash=utf_hash, utf_string="已保存标题", utf_badge_cell=utf_badge)
    manager = TitleManager(tmp_path / "title-manager.sqlite")
    manager.add_record(valid_array=valid_array, title_type="PLAYER_SPELL", title="旧标题", hash=utf_hash)

    monkeypatch.setattr(extractor, "get_default_title_manager", lambda: manager)
    monkeypatch.setattr(extractor, "get_player_status", lambda matrix: {})
    monkeypatch.setattr(extractor, "get_party_all", lambda matrix, y=19: {})

    try:
        data = extractor.extract_all_data(matrix)
    finally:
        manager.close()

    assert data["UTF_hash"] == utf_hash
    assert data["UTF_string"] == "已保存标题"
    assert "_pending_utf_title_record" not in data
