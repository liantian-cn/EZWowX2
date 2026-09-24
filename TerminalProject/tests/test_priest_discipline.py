import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from terminal.rotation.PriestDiscipline import PriestDiscipline


def _spell(
    title: str,
    *,
    cooldown: float = 0.0,
    is_charge: bool = False,
    charges: int = 1,
    is_usable: bool = True,
    is_known: bool = True,
) -> dict:
    return {
        "title": title,
        "cooldown": cooldown,
        "is_charge": is_charge,
        "charges": charges,
        "is_usable": is_usable,
        "is_known": is_known,
        "highlight": False,
    }


def _aura(title: str, *, remain: float = 0.0, count: int = 1, aura_type: str = "MAGIC") -> dict:
    return {
        "title": title,
        "remain": remain,
        "count": count,
        "type": aura_type,
        "color_string": "255,255,255",
    }


def _unit(
    token: str,
    *,
    exists: bool = True,
    alive: bool = True,
    role: str = "DAMAGER",
    health: float = 100.0,
    buffs: list[dict] | None = None,
    debuffs: list[dict] | None = None,
    damage_absorbs: float = 0.0,
    heal_absorbs: float = 0.0,
    can_attack: bool = False,
    in_combat: bool = False,
    in_ranged: bool = True,
    in_melee: bool = False,
    is_enemy: bool = False,
    cast_icon: str | None = None,
    cast_duration: float | None = None,
    channel_icon: str | None = None,
    channel_duration: float | None = None,
    is_moving: bool = False,
    is_chat_input_active: bool = False,
    is_mounted: bool = False,
    is_empowering: bool = False,
    is_player_casting_target: bool = False,
) -> dict:
    return {
        "unitToken": token,
        "exists": exists,
        "buff": buffs or [],
        "debuff": debuffs or [],
        "status": {
            "unitIsAlive": alive,
            "unitClass": "PRIEST",
            "unitRole": role,
            "unitHealthPercent": health,
            "unitPowerPercent": 100.0,
            "unitIsEnemy": is_enemy,
            "unitCanAttack": can_attack,
            "unitIsInRangedRange": in_ranged,
            "unitIsInMeleeRange": in_melee,
            "unitIsInCombat": in_combat,
            "unitIsTarget": token == "target",
            "unitHasBigDefense": False,
            "unitHasDispellableDebuff": False,
            "isPlayerCastingTarget": is_player_casting_target,
            "unitCastIcon": cast_icon,
            "unitCastDuration": cast_duration,
            "unitCastIsInterruptible": False,
            "unitChannelIcon": channel_icon,
            "unitChannelDuration": channel_duration,
            "unitChannelIsInterruptible": False,
            "unitIsEmpowering": is_empowering,
            "unitEmpoweringStage": 0.0,
            "unitIsMoving": is_moving,
            "unitIsMounted": is_mounted,
            "unitEnemyCount": 0,
            "unitIsSpellTargeting": False,
            "unitIsChatInputActive": is_chat_input_active,
            "unitIsInGroupOrRaid": True,
            "unitTrinket1CooldownUsable": False,
            "unitTrinket2CooldownUsable": False,
            "unitHealthstoneCooldownUsable": False,
            "unitHealingPotionCooldownUsable": False,
            "damage_absorbs": damage_absorbs,
            "heal_absorbs": heal_absorbs,
        },
    }


def _missing_unit(token: str) -> dict:
    return {"unitToken": token, "exists": False, "buff": [], "debuff": [], "status": {}}


def _cell(mean: float) -> dict:
    return {
        "pure": True,
        "mean": mean,
        "percent": mean,
        "decimal": mean / 100.0,
        "is_black": mean <= 0,
        "is_white": mean >= 255,
        "color_string": f"{int(mean)},{int(mean)},{int(mean)}",
    }


def _decoded_data(
    *,
    player: dict,
    spells: list[dict],
    parties: list[dict] | None = None,
    target: dict | None = None,
    focus: dict | None = None,
    mouseover: dict | None = None,
    enable: bool = True,
    delay: bool = False,
    assisted_combat: str = "",
) -> dict:
    party_units = parties or []
    return {
        "player": player,
        "target": target or _missing_unit("target"),
        "focus": focus or _missing_unit("focus"),
        "mouseover": mouseover or _missing_unit("mouseover"),
        "party": {
            "party1": party_units[0] if len(party_units) > 0 else _missing_unit("party1"),
            "party2": party_units[1] if len(party_units) > 1 else _missing_unit("party2"),
            "party3": party_units[2] if len(party_units) > 2 else _missing_unit("party3"),
            "party4": party_units[3] if len(party_units) > 3 else _missing_unit("party4"),
        },
        "spell": spells,
        "misc": {
            "combat_time": 0.0,
            "use_mouse": False,
        },
        "assisted_combat": assisted_combat,
        "delay": delay,
        "enable": enable,
        "dispel_blacklist": [],
        "interrupt_blacklist": [],
        "spell_stop_list": [],
        "spell_queue_window": 0.3,
        "burst_time": 0.0,
        "latest_succeeded_cast": "",
        "setting": {"0": _cell(0)},
        "spec": {},
    }


def test_priest_discipline_macro_table_contains_required_keys_and_assignments() -> None:
    rotation = PriestDiscipline()

    expected = {
        "绝望祷言": "SHIFT-F8",
        "福音": "SHIFT-F9",
        "target痛": "SHIFT-,",
        "focus痛": "ALT-,",
        "target灭": "SHIFT-.",
        "focus灭": "ALT-.",
        "target心灵震爆": "SHIFT-/",
        "focus心灵震爆": "ALT-/",
        "target苦修": "SHIFT-;",
        "focus苦修": "ALT-;",
        "target惩击": "SHIFT-'",
        "focus惩击": "ALT-'",
    }

    for macro_name, key in expected.items():
        assert rotation.getMacroKey(macro_name) == key


def test_priest_discipline_cast_gate_allows_queue_window_casts() -> None:
    rotation = PriestDiscipline()
    decoded_data = _decoded_data(
        player=_unit("player", health=40.0, cast_icon="快速治疗", cast_duration=95.0),
        spells=[_spell("绝望祷言")],
    )

    action, _, value = rotation.handle(decoded_data)

    assert action == "cast"
    assert value == "绝望祷言"


def test_priest_discipline_cast_gate_still_blocks_early_casts() -> None:
    rotation = PriestDiscipline()
    decoded_data = _decoded_data(
        player=_unit("player", health=40.0, cast_icon="快速治疗", cast_duration=80.0),
        spells=[_spell("绝望祷言")],
    )

    action, _, value = rotation.handle(decoded_data)

    assert action == "idle"
    assert value == "正在施法"


def test_priest_discipline_channel_gate_allows_queue_window_casts() -> None:
    rotation = PriestDiscipline()
    decoded_data = _decoded_data(
        player=_unit("player", health=40.0, channel_icon="苦修", channel_duration=95.0),
        spells=[_spell("绝望祷言")],
    )

    action, _, value = rotation.handle(decoded_data)

    assert action == "cast"
    assert value == "绝望祷言"


def test_priest_discipline_channel_gate_still_blocks_early_channels() -> None:
    rotation = PriestDiscipline()
    decoded_data = _decoded_data(
        player=_unit("player", health=40.0, channel_icon="苦修", channel_duration=80.0),
        spells=[_spell("绝望祷言")],
    )

    action, _, value = rotation.handle(decoded_data)

    assert action == "idle"
    assert value == "正在引导"


def test_priest_discipline_surge_threshold_uses_real_buff_stack() -> None:
    rotation = PriestDiscipline()
    decoded_data = _decoded_data(
        player=_unit("player", buffs=[_aura("圣光涌动", remain=1.0, count=2)]),
        parties=[_unit("party1", health=85.0, buffs=[_aura("救赎", remain=10.0)])],
        spells=[_spell("快速治疗")],
    )

    action, _, value = rotation.handle(decoded_data)

    assert action == "cast"
    assert value == "party1快速治疗"


def test_priest_discipline_shadow_mend_threshold_uses_real_buff_stack() -> None:
    rotation = PriestDiscipline()
    decoded_data = _decoded_data(
        player=_unit("player", buffs=[_aura("暗影愈合", remain=1.0, count=2)]),
        parties=[_unit("party1", health=90.0, buffs=[_aura("救赎", remain=10.0)])],
        spells=[_spell("暗影愈合")],
    )

    action, _, value = rotation.handle(decoded_data)

    assert action == "cast"
    assert value == "party1快速治疗"


def test_priest_discipline_keeps_radiance_recast_guard_inside_queue_window() -> None:
    rotation = PriestDiscipline()
    decoded_data = _decoded_data(
        player=_unit("player", cast_icon="真言术：耀", cast_duration=95.0),
        parties=[
            _unit("party1", health=85.0),
            _unit("party2", health=86.0),
            _unit("party3", health=87.0),
        ],
        spells=[_spell("真言术：耀", is_charge=True, charges=1)],
    )

    action, _, value = rotation.handle(decoded_data)

    assert action == "idle"
    assert value == "当前没有合适动作"


def test_priest_discipline_skips_double_radiance_branch_without_atonement_targets() -> None:
    rotation = PriestDiscipline()
    decoded_data = _decoded_data(
        player=_unit("player", in_combat=True, buffs=[_aura("福音", count=1)]),
        parties=[
            _unit("party1", health=85.0, in_combat=True, buffs=[_aura("救赎", remain=10.0)]),
            _unit("party2", health=86.0, in_combat=True, buffs=[_aura("救赎", remain=10.0)]),
            _unit("party3", health=87.0, in_combat=True, buffs=[_aura("救赎", remain=10.0)]),
        ],
        spells=[_spell("真言术：耀", is_charge=True, charges=2)],
    )

    try:
        action, _, value = rotation.handle(decoded_data)
    except IndexError as exc:
        pytest.fail(f"rotation should skip radiance recast without valid target: {exc}")

    assert action == "idle"
    assert value == "当前没有合适动作"
