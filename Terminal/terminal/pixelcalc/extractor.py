import traceback
import numpy as np
from datetime import datetime
from typing import Any


from .matrix import MatrixDecoder
from .color_map import COLOR_MAP
from .title_manager import get_default_title_manager


def get_player_status(matrix: MatrixDecoder) -> dict[str, Any]:
    """
        DejaVu\\05_slots\\31_player_status.lua
        注意事项，变量名采用驼峰法，是为了和lua同步
    """

    status: dict[str, Any] = {}
    status['unitExists'] = True  # 存在
    status['unitIsAlive'] = matrix.getCell(49, 15).is_not_black  # 单位存在状态

    status['unitClass'] = COLOR_MAP["CLASS"].get(matrix.getCell(50, 14).color_string, "UNKNOWN")   # 职业
    status['unitRole'] = COLOR_MAP["ROLE"].get(matrix.getCell(50, 15).color_string, "NONE")   # 职责

    status['unitHealthPercent'] = matrix.getCell(51, 14).percent  # 血量百分比
    status['unitPowerPercent'] = matrix.getCell(51, 15).percent  # 能量百分比

    status['unitIsEnemy'] = False           # 敌人
    status['unitCanAttack'] = False         # 可以被攻击
    status['unitIsInRangedRange'] = True    # 在远程范围
    status['unitIsInMeleeRange'] = True  # 在近战范围

    status['unitIsInCombat'] = matrix.getCell(52, 14).is_not_black  # 在战斗中
    status['unitIsTarget'] = matrix.getCell(52, 15).is_not_black  # 是当前目标

    status['unitHasBigDefense'] = matrix.getCell(53, 14).is_not_black  # 有大防御值
    status['unitHasDispellableDebuff'] = matrix.getCell(53, 15).is_not_black  # 有可驱散的减益效果

    if matrix.getBadgeCell(45, 14).is_black:
        status['unitCastIcon'] = None
        status['unitCastDuration'] = None
    else:
        status['unitCastIcon'] = matrix.getBadgeCell(45, 14).title     # 正在释放的技能
        status['unitCastDuration'] = matrix.getCell(54, 14).percent  # 施法持续时间

    if matrix.getBadgeCell(47, 14).is_black:
        status['unitChannelIcon'] = None
        status['unitChannelDuration'] = None
    else:
        status['unitChannelIcon'] = matrix.getBadgeCell(47, 14).title     # 正在通道法术的技能
        status['unitChannelDuration'] = matrix.getCell(54, 15).percent  # 通道持续时间

    status['unitIsEmpowering'] = matrix.getCell(55, 14).is_not_black     # isEmpowering
    status['unitEmpoweringStage'] = matrix.getCell(55, 15).percent   # 蓄力阶段

    status['unitIsMoving'] = matrix.getCell(56, 14).is_not_black     # isEmpowering
    status['unitIsMounted'] = matrix.getCell(56, 15).is_not_black     # isEmpowering

    status['unitEnemyCount'] = round(matrix.getCell(57, 14).decimal * 51)  # 近战敌人数量
    status['unitIsSpellTargeting'] = matrix.getCell(57, 15).is_not_black     # 正在选择目标

    status['unitIsChatInputActive'] = matrix.getCell(58, 14).is_not_black     # 正在聊天输入
    status['unitIsInGroupOrRaid'] = matrix.getCell(58, 15).is_not_black     # 在队伍/团队中

    status['unitTrinket1CooldownUsable'] = matrix.getCell(59, 14).is_not_black     # 饰品 1可用
    status['unitTrinket2CooldownUsable'] = matrix.getCell(59, 15).is_not_black     # 饰品 2可用

    status['unitHealthstoneCooldownUsable'] = matrix.getCell(60, 14).is_not_black     # 生命石可用
    status['unitHealingPotionCooldownUsable'] = matrix.getCell(60, 15).is_not_black     # 治疗药水可用
    status["isPlayerCastingTarget"] = matrix.getCell(61, 14).is_not_black   # 玩家正在被施法选中

    status['damage_absorbs'] = matrix.readBarValue(43, 16, 20)  # 伤害吸收
    status['heal_absorbs'] = matrix.readBarValue(64, 14, 20)  # 治疗吸收

    return status


def get_enemy_status(matrix: MatrixDecoder, x: int, y: int) -> dict[str, Any]:
    """
        DejaVu\\05_slots\\41_enemy_status.lua
        注意事项，变量名采用驼峰法，是为了和lua同步
    """
    status: dict[str, Any] = {}

    status['unitExists'] = matrix.getCell(x+0, y+0).is_not_black   # 单位存在状态
    status['unitIsAlive'] = matrix.getCell(x+0, y+1).is_not_black  # 单位是否存活
    status['unitClass'] = COLOR_MAP["CLASS"].get(matrix.getCell(x+1, y+0).color_string, "UNKNOWN")   # 职业
    status['unitRole'] = COLOR_MAP["ROLE"].get(matrix.getCell(x+1, y+1).color_string, "NONE")   # 职责
    status['unitHealthPercent'] = matrix.getCell(x+2, y+0).percent  # 血量百分比
    status['unitPowerPercent'] = matrix.getCell(x+2, y+1).percent  # 能量百分比
    status['unitIsEnemy'] = matrix.getCell(x+3, y+0).is_not_black  # 敌人
    status['unitCanAttack'] = matrix.getCell(x+3, y+1).is_not_black  # 可以被攻击
    status['unitIsInRangedRange'] = matrix.getCell(x+4, y+0).is_not_black  # 在远程范围
    status['unitIsInMeleeRange'] = matrix.getCell(x+4, y+1).is_not_black  # 在近战范围
    status['unitIsInCombat'] = matrix.getCell(x+5, y+0).is_not_black  # 在战斗中
    status['unitIsTarget'] = matrix.getCell(x+5, y+1).is_not_black  # 是当前目标
    if matrix.getBadgeCell(x+6, y+0).is_black:
        status['unitCastIcon'] = None
        status['unitCastDuration'] = None
        status['unitCastIsInterruptible'] = False
    else:
        status['unitCastIcon'] = matrix.getBadgeCell(x+6, y+0).title     # 正在释放的技能
        status['unitCastDuration'] = matrix.getCell(x+10, y+0).percent  # 施法持续时间
        # status['unitCastIsInterruptible'] = matrix.getCell(x+11, y+0).is_not_black  # 施法是否可中断
        status['unitCastIsInterruptible'] = bool(matrix.getCell(x+11, y+0).color_string == '255,255,60')  # 施法是否可中断

    if matrix.getBadgeCell(x+8, y+0).is_black:
        status['unitChannelIcon'] = None
        status['unitChannelDuration'] = None
        status['unitChannelIsInterruptible'] = False
    else:
        status['unitChannelIcon'] = matrix.getBadgeCell(x+8, y+0).title     # 正在通道法术的技能
        status['unitChannelDuration'] = matrix.getCell(x+10, y+1).percent  # 通道持续时间
        # status['unitChannelIsInterruptible'] = matrix.getCell(x+11, y+1).is_not_black  # 通道是否可中断
        status['unitChannelIsInterruptible'] = bool(matrix.getCell(x+11, y+1).color_string == '255,255,60')  # 通道是否可中断

    return status


def get_party_all(matrix: MatrixDecoder, y: int = 19) -> dict[str, Any]:
    """
        DejaVu\\05_slots\\51_party_aura.lua
        DejaVu\\05_slots\\52_party_bar.lua
        DejaVu\\05_slots\\53_party_status.lua
    """
    result = {
        'party1': {'exists': False, 'unitToken': 'party1', 'buff': [], 'debuff': [],  'status': {}, },
        'party2': {'exists': False, 'unitToken': 'party2', 'buff': [], 'debuff': [],  'status': {}, },
        'party3': {'exists': False, 'unitToken': 'party3', 'buff': [], 'debuff': [],  'status': {}, },
        'party4': {'exists': False, 'unitToken': 'party4', 'buff': [], 'debuff': [],  'status': {}, },
    }
    for i in range(1, 5):
        baseX = 21*i
        statusY = y + 5
        party_key: str = f'party{i}'
        party_exist: bool = matrix.getCell(baseX - 9, statusY).is_not_black
        # print(f"{party_key}/{party_exist}/{matrix.getCell(baseX - 9, statusY).color_string}")
        # print(f"{party_key}/{party_exist}/{matrix.getCell(baseX - 8, statusY).color_string}")
        if party_exist:
            result[party_key]['exists'] = True
            # DejaVu\\05_slots\\53_party_status.lua
            result[party_key]['status']['unitExists'] = True
            result[party_key]['status']['unitIsAlive'] = matrix.getCell(baseX - 9, statusY+1).is_not_black
            # unitClass\unitRole
            result[party_key]['status']['unitClass'] = COLOR_MAP["CLASS"].get(matrix.getCell(baseX - 8, statusY).color_string, "UNKNOWN")  # 职业
            result[party_key]['status']['unitRole'] = COLOR_MAP["ROLE"].get(matrix.getCell(baseX - 8, statusY+1).color_string, "NONE")   # 职责
            # unitHealthPercent\unitPowerPercent
            result[party_key]['status']['unitHealthPercent'] = matrix.getCell(baseX - 7, statusY).percent  # 血量百分比
            result[party_key]['status']['unitPowerPercent'] = matrix.getCell(baseX - 7, statusY+1).percent  # 能量百分比
            # unitIsEnemy /unitCanAttack
            result[party_key]['status']['unitIsEnemy'] = matrix.getCell(baseX - 6, statusY).is_not_black  # 敌人
            result[party_key]['status']['unitCanAttack'] = matrix.getCell(baseX - 6, statusY+1).is_not_black  # 可以被攻击
            # unitIsInRangedRange/unitIsInMeleeRange
            result[party_key]['status']['unitIsInRangedRange'] = matrix.getCell(baseX - 5, statusY).is_not_black  # 在远程范围
            result[party_key]['status']['unitIsInMeleeRange'] = matrix.getCell(baseX - 5, statusY+1).is_not_black  # 在近战范围
            # unitIsInCombat/unitIsTarget
            result[party_key]['status']['unitIsInCombat'] = matrix.getCell(baseX - 4, statusY).is_not_black  # 在战斗中
            result[party_key]['status']['unitIsTarget'] = matrix.getCell(baseX - 4, statusY+1).is_not_black  # 是当前目标
            # unitHasBigDefense/unitHasDispellableDebuff
            result[party_key]['status']['unitHasBigDefense'] = matrix.getCell(baseX - 3, statusY).is_not_black  # 有大防御
            result[party_key]['status']['unitHasDispellableDebuff'] = matrix.getCell(baseX - 3, statusY+1).is_not_black  # 有可移除的法术
            result[party_key]['status']['isPlayerCastingTarget'] = matrix.getCell(baseX - 2, statusY).is_not_black   # 玩家正在被施法选中
            # DejaVu\\05_slots\\52_party_bar.lua
            result[party_key]['status']['damage_absorbs'] = matrix.readBarValue(baseX - 20, statusY, 10) / 2  # 伤害吸收 # 注意，吸收盾的条最大现在是血量的一半，所以这里除以2映射到百分比。
            result[party_key]['status']['heal_absorbs'] = matrix.readBarValue(baseX - 20, statusY + 1, 10) / 2  # 治疗吸收# 注意，吸收盾的条最大现在是血量的一半，所以这里除以2映射到百分比。
            # DejaVu\\05_slots\\51_party_aura.lua
            result[party_key]['buff'] = matrix.readAura(x=baseX - 20, y=y, length=7)  # buff
            result[party_key]['debuff'] = matrix.readAura(x=baseX - 6, y=y, length=3)  # debuff
    return result


def extract_all_data(matrix: MatrixDecoder) -> dict[str, Any]:
    data: dict[str, Any] = {
        'timestamp': datetime.now(),
        'spell': matrix.readSpell(),
        # Keep unitToken camelCase for game protocol compatibility.
        'player': {'unitToken': 'player',
                   'exists': True,
                   'buff': matrix.readAura(x=1, y=4, length=30),
                   'debuff': matrix.readAura(x=1, y=9, length=10),
                   'status': get_player_status(matrix),
                   },
        'target': {'unitToken': 'target',
                   'exists': False,
                   'debuff': [],
                   'status': {}
                   },
        'focus': {'unitToken': 'focus',
                  'exists': False,
                  'debuff': [],
                  'status': {}
                  },
        'mouseover': {'unitToken': 'mouseover',
                      'exists': False,
                      'debuff': [],
                      'status': {}
                      },
        'misc': {
            'combat_time': matrix.getCell(56, 9).mean,
            'use_mouse': matrix.getCell(58, 9).is_not_black,
        },
        'spec': matrix.readCellList(55, 13, 14),
        'setting': matrix.readCellList(55, 12, 14),
        'party': get_party_all(matrix),
        # DejaVu\05_slots\92_assisted_combat.lua
        'assisted_combat': matrix.getBadgeCell(43, 14).title,   # 一键辅助技能
        # DejaVu\05_slots\91_global.lua
        'flash': matrix.getCell(54, 9),             # 一个闪烁的cell
        'delay': matrix.getCell(55, 9).is_not_black,    # 延迟
        'testCell': matrix.readCharCell(0, 2),
        'enable': matrix.getCell(83, 0).is_not_black,
        'dispel_blacklist': matrix.readBadgeCellList(64, 15, 10),  # 可移除的法术
        'interrupt_blacklist': matrix.readBadgeCellList(43, 17, 19),  # 可中断的法术
        'spell_stop_list': matrix.readBadgeCellList(43, 26, 10),  # 可中断的法术
        'spell_queue_window': matrix.getCell(57, 9).mean / 100,  # 映射到秒，游戏内的毫秒/10。
        'burst_time': matrix.getCell(82, 0).decimal * 60,
        'latest_succeeded_cast': matrix.getBadgeCell(82, 17).title     # 最后的施法技能
    }

    target_exists = matrix.getCell(55, 10).is_not_black
    focus_exists = matrix.getCell(70, 10).is_not_black
    mouseover_exists = matrix.getCell(70, 12).is_not_black
    if target_exists:
        data["target"]["exists"] = True
        data["target"]["debuff"] = matrix.readAura(x=22, y=9, length=16)
        data["target"]["status"] = get_enemy_status(matrix, 55, 10)

    if focus_exists:
        data["focus"]["exists"] = True
        data["focus"]["debuff"] = matrix.readAura(x=1, y=14, length=10)
        data["focus"]["status"] = get_enemy_status(matrix, 70, 10)

    if mouseover_exists:
        data["mouseover"]["exists"] = True
        data["mouseover"]["debuff"] = matrix.readAura(x=22, y=14, length=10)
        data["mouseover"]["status"] = get_enemy_status(matrix, 70, 12)

    UTF_hash = matrix.readUTFhash(64, 26)  # 用于测试的UTF8编码的hash值
    UTF_string = matrix.readUTFString(66, 26, 16)  # 用于测试的UTF8编码的字符串

    if (UTF_hash is not None) and (UTF_string is not None):
        title_manager = get_default_title_manager()
        if not title_manager.has_persistent_record(UTF_hash):
            utf_badge_cell = matrix.getBadgeCell(64, 26)
            data["_pending_utf_title_record"] = {
                "hash": UTF_hash,
                "title": UTF_string,
                "title_type": utf_badge_cell.cell_type,
                "valid_array": utf_badge_cell.valid_array.tolist(),
            }
    data["UTF_hash"] = UTF_hash
    data["UTF_string"] = UTF_string

    return data


if __name__ == "__main__":
    from pathlib import Path
    from PIL import Image
    from pprint import pprint

    screenshot_array = np.array(Image.open(r"terminal/pixelcalc/monitor_1_small.png").convert("RGB"))
    matrix: MatrixDecoder = MatrixDecoder(screenshot_array)

    data = extract_all_data(matrix)
    pprint(data)
