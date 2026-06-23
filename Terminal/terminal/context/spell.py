from typing import Any

__all__ = [
    "Spell",
]


class Spell:
    def __init__(self, spell: dict[str, Any]) -> None:
        """
        spell的结构如下: 
        spell = {
            "is_charge": True,
            "charges": charge_cell,
            "title": icon_cell.title,
            "cooldown": cooldown_cell.remaining,
            "highlight": highlight_cell.is_not_black,
            "is_usable": usable_cell.is_not_black,
            "is_known": known_cell.is_not_black,
        }
        """
        self.spell = spell

    def __str__(self) -> str:
        return self.spell["title"]

    @property
    def title(self) -> str:
        return self.spell["title"]

    @property
    def cooldown(self) -> float:
        return float(self.spell.get("cooldown", 999.0))

    @property
    def is_usable(self) -> bool:
        return bool(self.spell.get("is_usable", False))

    @property
    def is_known(self) -> bool:
        return bool(self.spell.get("is_known", False))

    @property
    def is_charge(self) -> bool:
        return bool(self.spell.get("is_charge", False))

    @property
    def charges(self) -> int:
        return int(self.spell.get("charges", 0))

    @property
    def highlight(self) -> bool:
        return bool(self.spell.get("highlight", False))
