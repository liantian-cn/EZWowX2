from __future__ import annotations

from typing import Any

from .aura import Aura
from .error import ContextError

__all__ = [
    "Unit",
]


class Unit:
    def __init__(self, unit: dict[str, Any]) -> None:
        self.unit = unit

    @property
    def unitToken(self) -> str:
        return self.unit["unitToken"]

    @property
    def unitType(self) -> str:
        if self.unitToken == "player":
            return "player"
        elif self.unitToken.startswith("party"):
            return "party"
        else:
            return "enemy"

    @property
    def exists(self) -> bool:
        return bool(self.unit["exists"])

    @property
    def status(self) -> dict[str, Any]:
        return self.unit["status"]

    @property
    def buff(self) -> list[Aura]:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType in ["player", "party"]:
            return [Aura(aura) for aura in self.unit["buff"]]
        raise ContextError("enemy unit has no buff")

    def hasBuff(self, buff_name: str) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType in ["enemy", ]:
            raise ContextError("enemy unit has no buff")
        for aura in self.buff:
            if aura.title == buff_name:
                return True
        return False

    def buffByName(self, name: str) -> Aura | None:
        if self.hasBuff(name):
            for aura in self.buff:
                if aura.title == name:
                    return aura
        return None

    def buffRemain(self, name: str) -> float:
        buff = self.buffByName(name)
        if not buff:
            return 0.0  # 这会让用法非常方便，如果buff不存在，0就是了
        return buff.remain

    def buffStack(self, name: str) -> int:
        buff = self.buffByName(name)
        if not buff:
            return 0  # 这会让用法非常方便，如果buff不存在，0就是了
        return buff.count

    @property
    def debuff(self) -> list[Aura]:
        if not self.exists:
            raise ContextError("unit does not exist")
        return [Aura(aura) for aura in self.unit["debuff"]]

    def hasDebuff(self, debuff_name: str) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        for aura in self.debuff:
            if aura.title == debuff_name:
                return True
        return False

    def debuffByName(self, name: str) -> Aura | None:
        if self.hasDebuff(name):
            for aura in self.debuff:
                if aura.title == name:
                    return aura
        return None

    def debuffRemain(self, name: str) -> float:
        debuff = self.debuffByName(name)
        if not debuff:
            return 0.0  # 这会让用法非常方便，如果debuff不存在，0就是了
        return debuff.remain

    def debuffStack(self, name: str) -> int:
        debuff = self.debuffByName(name)
        if not debuff:
            return 0  # 这会让用法非常方便，如果debuff不存在，0就是了
        return debuff.count

    @property
    def alive(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        return bool(self.status["unitIsAlive"])

    @property
    def unitClass(self) -> str:
        if not self.exists:
            raise ContextError("unit does not exist")
        return str(self.status["unitClass"])

    @property
    def unitRole(self) -> str:
        if not self.exists:
            raise ContextError("unit does not exist")
        return str(self.status["unitRole"])

    @property
    def healthPercent(self) -> float:
        if not self.exists:
            raise ContextError("unit does not exist")
        return float(self.status["unitHealthPercent"])

    @property
    def powerPercent(self) -> float:
        if not self.exists:
            raise ContextError("unit does not exist")
        return float(self.status["unitPowerPercent"])

    @property
    def isEnemy(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        return bool(self.status["unitIsEnemy"])

    @property
    def canAttack(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        return bool(self.status["unitCanAttack"])

    @property
    def isInRangedRange(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        return bool(self.status["unitIsInRangedRange"])

    @property
    def isInMeleeRange(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        return bool(self.status["unitIsInMeleeRange"])

    @property
    def isInCombat(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        return bool(self.status["unitIsInCombat"])

    @property
    def isTarget(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        return bool(self.status["unitIsTarget"])

    @property
    def hasBigDefense(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType in ["player", "party"]:
            return bool(self.status["unitHasBigDefense"])
        raise ContextError("field is not available for this unit type")

    @property
    def hasDispellableDebuff(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType in ["player", "party"]:
            return bool(self.status["unitHasDispellableDebuff"])
        raise ContextError("field is not available for this unit type")

    @property
    def isPlayerCastingTarget(self) -> bool:
        if not self.exists:
            return False
        if self.unitType in ["player", "party"]:
            return bool(self.status["isPlayerCastingTarget"])
        raise ContextError("field is not available for this unit type")

    @property
    def castIcon(self) -> str | None:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType in ["player", "enemy"]:
            return self.status["unitCastIcon"]
        raise ContextError("field is not available for this unit type")

    @property
    def castDuration(self) -> float | None:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType in ["player", "enemy"]:
            duration = self.status["unitCastDuration"]
            if duration is None:
                return None
            return float(duration)
        raise ContextError("field is not available for this unit type")

    @property
    def castIsInterruptible(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "enemy":
            return bool(self.status["unitCastIsInterruptible"])
        raise ContextError("field is not available for this unit type")

    @property
    def channelIcon(self) -> str | None:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType in ["player", "enemy"]:
            return self.status["unitChannelIcon"]
        raise ContextError("field is not available for this unit type")

    @property
    def channelDuration(self) -> float | None:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType in ["player", "enemy"]:
            duration = self.status["unitChannelDuration"]
            if duration is None:
                return None
            return float(duration)
        raise ContextError("field is not available for this unit type")

    @property
    def channelIsInterruptible(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "enemy":
            return bool(self.status["unitChannelIsInterruptible"])
        raise ContextError("field is not available for this unit type")

    @property
    def anyCastIcon(self) -> str | None:
        if self.castIcon is not None:
            return self.castIcon
        if self.channelIcon is not None:
            return self.channelIcon
        return None

    @property
    def anyCastDuration(self) -> float | None:
        if self.castDuration is not None:
            return self.castDuration
        if self.channelDuration is not None:
            return self.channelDuration
        return None

    @property
    def anyCastIsInterruptible(self) -> bool:
        if self.castIcon is not None:
            return self.castIsInterruptible
        if self.channelIcon is not None:
            return self.channelIsInterruptible
        return False

    @property
    def isEmpowering(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return bool(self.status["unitIsEmpowering"])
        raise ContextError("field is not available for this unit type")

    @property
    def empoweringStage(self) -> float:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return float(self.status["unitEmpoweringStage"])
        raise ContextError("field is not available for this unit type")

    @property
    def isMoving(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return bool(self.status["unitIsMoving"])
        raise ContextError("field is not available for this unit type")

    @property
    def isMounted(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return bool(self.status["unitIsMounted"])
        raise ContextError("field is not available for this unit type")

    @property
    def enemyCount(self) -> int:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return int(self.status["unitEnemyCount"])
        raise ContextError("field is not available for this unit type")

    @property
    def isSpellTargeting(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return bool(self.status["unitIsSpellTargeting"])
        raise ContextError("field is not available for this unit type")

    @property
    def isChatInputActive(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return bool(self.status["unitIsChatInputActive"])
        raise ContextError("field is not available for this unit type")

    @property
    def isInGroupOrRaid(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return bool(self.status["unitIsInGroupOrRaid"])
        raise ContextError("field is not available for this unit type")

    @property
    def trinket1CooldownUsable(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return bool(self.status["unitTrinket1CooldownUsable"])
        raise ContextError("field is not available for this unit type")

    @property
    def trinket2CooldownUsable(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return bool(self.status["unitTrinket2CooldownUsable"])
        raise ContextError("field is not available for this unit type")

    @property
    def healthstoneCooldownUsable(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return bool(self.status["unitHealthstoneCooldownUsable"])
        raise ContextError("field is not available for this unit type")

    @property
    def healingPotionCooldownUsable(self) -> bool:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType == "player":
            return bool(self.status["unitHealingPotionCooldownUsable"])
        raise ContextError("field is not available for this unit type")

    @property
    def damageAbsorbs(self) -> float:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType in ["player", "party"]:
            return float(self.status["damage_absorbs"])
        raise ContextError("field is not available for this unit type")

    @property
    def healAbsorbs(self) -> float:
        if not self.exists:
            raise ContextError("unit does not exist")
        if self.unitType in ["player", "party"]:
            return float(self.status["heal_absorbs"])
        raise ContextError("field is not available for this unit type")
