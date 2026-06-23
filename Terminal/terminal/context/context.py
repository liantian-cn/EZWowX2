from typing import Any

from .spell import Spell
from .unit import Unit
from .error import ContextError
from .cell import CellDict


__all__ = [
    "Context",
]


class Context:
    def __init__(self, decoded_data: dict[str, Any]) -> None:
        self._decoded_data: dict[str, Any] = decoded_data

    @property
    def decoded_data(self) -> dict[str, Any]:
        return self._decoded_data

    @property
    def raw_data(self) -> dict[str, Any]:
        return self._decoded_data

    def spell(self, spell_name: str) -> Spell | None:
        if self.decoded_data is None:
            return None
        for spell in self.decoded_data["spell"]:
            if spell["title"] == spell_name:
                return Spell(spell)
        return None

    def gcd_ready(self, queue_window: float = 0.2) -> bool:
        gcd_spell = self.spell("公共冷却时间")
        if gcd_spell is None:
            return True  # 没有公共冷却时间这个技能，说明版本比较老，先默认它永远准备好了。
        if gcd_spell.is_known and gcd_spell.is_usable:
            return gcd_spell.cooldown <= queue_window
        else:
            return True  # 没有公共冷却时间这个技能，说明版本比较老，先默认它永远准备好了。

    def spell_cooldown_ready(self, spell_name: str, queue_window: float = 0.2, ignore_gcd=False, ignore_usable=False) -> bool:
        spell = self.spell(spell_name)
        if spell is None:
            return False
        if not spell.is_known:
            return False
        if not (spell.is_usable or ignore_usable):
            return False
        if spell.cooldown <= queue_window:
            return ignore_gcd or self.gcd_ready(queue_window)
        return False

    def spell_charges_ready(self, spell_name: str, charges: int, queue_window: float = 0.2, ignore_gcd=False, ignore_usable=False) -> bool:
        spell = self.spell(spell_name)
        if spell is None:
            return False
        if not (spell.is_charge):
            return False
        if not spell.is_known:
            return False
        if not (spell.is_usable or ignore_usable):
            return False
        if spell.charges >= charges:
            return ignore_gcd or self.gcd_ready(queue_window)
        return False

    def spell_known(self, spell_name: str) -> bool:
        spell = self.spell(spell_name)
        if spell is None:
            return False
        return spell.is_known

    @property
    def player(self) -> Unit:
        return Unit(self.decoded_data["player"])

    @property
    def target(self) -> Unit:
        return Unit(self.decoded_data["target"])

    @property
    def focus(self) -> Unit:
        return Unit(self.decoded_data["focus"])

    @property
    def mouseover(self) -> Unit:
        return Unit(self.decoded_data["mouseover"])

    @property
    def parties(self) -> list[Unit]:
        units = []
        for i in range(1, 5):
            party_key: str = f'party{i}'
            unit = Unit(self.decoded_data["party"][party_key])
            if unit.exists:
                units.append(unit)
        return units

    def party(self, party_index: int) -> Unit:
        return Unit(self.decoded_data["party"][f'party{party_index}'])

    @property
    def burst_time(self) -> float:
        return self.decoded_data['burst_time']

    @property
    def combat_time(self) -> float:
        return self.decoded_data['misc']['combat_time']

    @property
    def use_mouse(self) -> bool:
        return self.decoded_data['misc']['use_mouse']

    @property
    def assisted_combat(self) -> str:
        return self.decoded_data['assisted_combat']

    @property
    def delay(self) -> bool:
        return self.decoded_data['delay']

    @property
    def enable(self) -> bool:
        return self.decoded_data['enable']

    @property
    def dispel_blacklist(self) -> list[str]:
        return self.decoded_data['dispel_blacklist']

    @property
    def interrupt_blacklist(self) -> list[str]:
        return self.decoded_data['interrupt_blacklist']

    @property
    def spell_stop_list(self) -> list[str]:
        return self.decoded_data['spell_stop_list']

    @property
    def spell_queue_window(self) -> float:
        return self.decoded_data['spell_queue_window']

    @property
    def spec(self) -> CellDict:
        return CellDict(self.decoded_data['spec'])

    @property
    def setting(self) -> CellDict:
        return CellDict(self.decoded_data['setting'])

    @property
    def latest_succeeded_cast(self) -> str:
        return self.decoded_data['latest_succeeded_cast']
