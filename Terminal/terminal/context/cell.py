from typing import Any

from .error import ContextError

__all__ = [
    "Cell",
    "CellDict",
]


class Cell:
    def __init__(self, cell: dict[str, Any]) -> None:
        """
        cell的结构如下: 
        cellData = {
            "pure": True,  # 固定为True
            "mean": cell.mean,
            "percent": cell.percent,
            "decimal": cell.decimal,
            "is_black": cell.is_black,
            "is_white": cell.is_white,
            "color_string": cell.color_string,
                }
        """
        self.cell = cell

    @property
    def pure(self) -> bool:
        return self.cell["pure"]

    @property
    def mean(self) -> float:
        return self.cell["mean"]

    @property
    def percent(self) -> float:
        return self.cell["percent"]

    @property
    def decimal(self) -> float:
        return self.cell["decimal"]

    @property
    def is_black(self) -> bool:
        return self.cell["is_black"]

    @property
    def is_white(self) -> bool:
        return self.cell["is_white"]

    @property
    def color_string(self) -> str:
        return self.cell["color_string"]


class CellDict:
    def __init__(self, cell_dict: dict[str, Any]) -> None:
        self.cell_dict = cell_dict

    def cell(self, index: int) -> Cell | None:
        entry = self.cell_dict.get(f"{index}", None)
        if entry is None:
            return None
        return Cell(entry)
