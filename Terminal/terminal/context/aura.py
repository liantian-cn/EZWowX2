from typing import Any

__all__ = [
    "Aura",
]


class Aura:
    def __init__(self, aura: dict[str, Any]) -> None:
        """
        aura的结构如下: 
        auraData = {
            "title": icon_cell.title,
            "remain": remain_cell.remaining,
            "color_string": type_cell.color_string,
            "type": COLOR_MAP["SPELL_TYPE"].get(type_cell.color_string, "UNKNOWN"),
            "count": count_cell,
        }
        """
        self.aura = aura

    def __str__(self) -> str:
        return self.aura["title"]

    @property
    def title(self) -> str:
        return self.aura["title"]

    @property
    def remain(self) -> float:
        return float(self.aura.get("remain", 999.0))

    @property
    def type(self) -> str:
        return self.aura.get("type", "UNKNOWN")

    @property
    def count(self) -> int:
        count = self.aura.get("count", 1)
        if count == 0:
            return 1
        return count

    @property
    def color_string(self) -> str:
        return self.aura.get("color_string", "0,0,0")
