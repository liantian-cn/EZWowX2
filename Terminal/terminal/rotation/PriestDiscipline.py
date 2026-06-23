from __future__ import annotations
from typing import cast
from .base import BaseRotation
from terminal.context import Context, Unit
from datetime import datetime


__all__ = ["PriestDiscipline",]

# 技能       | 英文                 | 定义
# --------------------------------------------------------------
# 快速治疗   |  Flash Heal          |
# 真言术：盾 |  Power Word: Shield  | 又叫盾
# 暗影愈合   |  Shadow Mend         | 施法技能是 快速治疗 的热键，实际施放的可能是暗影愈合
# 虚空之盾   |  Void Shield         | 又叫黑盾，和真言术：盾是同一个技能，在存在 buff 虚空之盾 时，技能变为 虚空之盾
# 救赎       |  Atonement
# 纯净术     |  Purify
# 灌注       |  Infusion
# 耀         |  Radiance
# 恳求       |  Plea
# 绝望祷言   |  Desperate Prayer
# 终极苦修   |  Ultimate Penitence
# 福音       |  Evangelism
# 惩击       |  Smite
# 苦修       |  Penance
# 心灵震爆   |  Mind Blast
# 暗言术：痛 |  Shadow Word: Pain
# 暗言术：灭 |  Shadow Word: Death
# 圣光涌动   |  Surge of Light

# changelog
# 2026-04-29 目标是友方，不浪费防御苦修。

MINOR_DEBUFF = ["嗜血", "英勇", "赛季词缀", "良性Debuff", "中度醉拳", "轻度醉拳", "重度醉拳", "低温", "暗影愈合", "沙漏尽枯"]


class DisciplinePartyMember(Unit):
    # 只在当前 rotation 内补充类型信息，不改 Unit 本体。
    atonement_remaining: float
    has_shadow_shield: bool
    has_shield: bool
    shield_remaining: float
    health_score: float
    health_deficit: float
    health_base: float
    rejuvenation_count: int
    hot_count: int
    dispel_list: list[str]
    debuff_list: list[str]
    buff_list: list[str]
    can_dispel: bool


class PriestDiscipline(BaseRotation):
    name = "戒律"
    desc = "戒律牧师的循环逻辑。\n仅限神谕者"

    def __init__(self) -> None:
        super().__init__()

        self.dispel_types = ["MAGIC", ]  # 可驱散的 debuff 类型  本赛季好像没有疾病
        self.dispel_blacklist: list[str] = []

        self.macroTable = {
            "player苦修": "ALT-NUMPAD1",
            "party1苦修": "ALT-NUMPAD2",
            "party2苦修": "ALT-NUMPAD3",
            "party3苦修": "ALT-NUMPAD4",
            "party4苦修": "ALT-NUMPAD5",
            #
            "player快速治疗": "ALT-NUMPAD6",
            "party1快速治疗": "ALT-NUMPAD7",
            "party2快速治疗": "ALT-NUMPAD8",
            "party3快速治疗": "ALT-NUMPAD9",
            "party4快速治疗": "ALT-NUMPAD0",
            #
            "player真言术盾": "ALT-F2",
            "party1真言术盾": "ALT-F3",
            "party2真言术盾": "ALT-F5",
            "party3真言术盾": "ALT-F6",
            "party4真言术盾": "ALT-F7",
            #
            "player纯净术": "ALT-F8",
            "party1纯净术": "ALT-F9",
            "party2纯净术": "ALT-F10",
            "party3纯净术": "ALT-F11",
            "party4纯净术": "ALT-F12",
            #
            "player耀": "SHIFT-NUMPAD1",
            "party1耀": "SHIFT-NUMPAD2",
            "party2耀": "SHIFT-NUMPAD3",
            "party3耀": "SHIFT-NUMPAD4",
            "party4耀": "SHIFT-NUMPAD5",
            #
            "player灌注": "SHIFT-NUMPAD6",
            "party1灌注": "SHIFT-NUMPAD7",
            "party2灌注": "SHIFT-NUMPAD8",
            "party3灌注": "SHIFT-NUMPAD9",
            "party4灌注": "SHIFT-NUMPAD0",
            #
            "player恳求": "SHIFT-F2",
            "party1恳求": "SHIFT-F3",
            "party2恳求": "SHIFT-F5",
            "party3恳求": "SHIFT-F6",
            "party4恳求": "SHIFT-F7",
            #
            "绝望祷言": "SHIFT-F8",
            "福音": "SHIFT-F9",
            # 暗言术：痛
            "target痛": "SHIFT-,",
            "focus痛": "ALT-,",
            # 暗言术：灭
            "target灭": "SHIFT-.",
            "focus灭": "ALT-.",
            # 心灵震爆
            "target心灵震爆": "SHIFT-/",
            "focus心灵震爆": "ALT-/",
            # 苦修
            "target苦修": "SHIFT-;",
            "focus苦修": "ALT-;",
            # 惩击
            "target惩击": "SHIFT-'",
            "focus惩击": "ALT-'",

        }

    def calculate_party_health_score(self, ctx: Context) -> list[DisciplinePartyMember]:
        party_members: list[DisciplinePartyMember] = []
        for unit in ctx.parties:
            if unit.exists and unit.isInRangedRange and unit.alive:
                # if unit.exists and unit.alive:
                party_members.append(cast(DisciplinePartyMember, unit))
        party_members.append(cast(DisciplinePartyMember, ctx.player))
        # print(f"{ctx.player.castIcon=}")

        for member in party_members:
            unit_role = member.unitRole
            unit_class = member.unitClass
            health_percent = member.healthPercent
            damage_absorbs = member.damageAbsorbs
            heal_absorbs = member.healAbsorbs
            atonement_remaining = member.buffRemain("救赎")
            has_shadow_shield = member.hasBuff("虚空之盾")
            has_shield = has_shadow_shield or member.hasBuff("真言术：盾")
            if member.hasBuff("虚空之盾"):
                shield_remaining = member.buffRemain("虚空之盾")
            else:
                shield_remaining = member.buffRemain("真言术：盾")

            health_offset = 0    # 血量偏移，数值越高说明实际血量比显示的血量更安全，越低说明更危险。比如正在被治疗但治疗还没生效，或者正在被伤害但伤害还没生效。
            # debuff修正，每个debuff，积分-15分
            debuff_list = [debuff for debuff in member.debuff if (debuff.title not in MINOR_DEBUFF)]
            debuff_count = sum([debuff.count for debuff in debuff_list])
            debuff_count = min(debuff_count, 5)  # 最多算5层debuff，超过5层的debuff不再增加危险度了。
            # 记录完整 buff 列表，方便调试和后续扩展判断。
            buff_list = [buff.title for buff in member.buff]
            health_offset += -10 * debuff_count

            # 血量基线使用“当前血量 - 治疗吸收”，数值越低说明越危险。
            health_base = health_percent - heal_absorbs + health_offset

            if member.isPlayerCastingTarget:
                if ctx.player.castIcon == "快速治疗":
                    health_base = health_base + 10
                elif ctx.player.castIcon == "暗影愈合":
                    health_base = health_base + 30
            # DKT特殊点。DKT80%血就当满血。

            if unit_role == "TANK" and unit_class == "DEATHKNIGHT":
                health_base = health_base + 20

            # 先找出单位身上可驱散的 debuff，再按黑名单过滤。
            dispel_list = [debuff.title for debuff in member.debuff if (debuff.type in self.dispel_types)]
            can_dispel = len(dispel_list) > 0
            for dispel in dispel_list:
                if dispel in self.dispel_blacklist:
                    can_dispel = False
                    break

            # 血量缺口表示补满到 100% 还需要多少治疗量。
            health_deficit = 100 - health_base
            # 积分计算过程
            # 积分是基于血量基线的，血量基线越低说明越危险，优先级越高。
            # 积分是后续所有判断的标准。
            health_score = health_base + damage_absorbs  # 基础健康分数，伤害吸收护盾越多越安全

            # 角色修正
            # 这样盾总会优先给自己。
            if unit_role == "TANK":
                health_score += 10
            elif unit_role == "HEALER":
                health_score -= 3

            # 积分最大100分
            health_score = min(health_score, 100)

            member.atonement_remaining = atonement_remaining  # 救赎剩余时间
            member.has_shadow_shield = has_shadow_shield  # 有没有黑盾，又叫虚空盾
            member.has_shield = has_shield  # 有没有护盾：包含黑盾
            member.shield_remaining = shield_remaining  # 盾剩余时间
            member.health_score = health_score  # 综合健康分数，数值越低越优先处理
            member.health_deficit = health_deficit  # 血量缺口，数值越高说明越缺治疗
            member.health_base = health_base  # 当前血量减治疗吸收后的基线，数值越低越危险
            member.dispel_list = dispel_list  # 可驱散debuff列表
            # member.debuff_list = debuff_list  # debuff列表
            member.buff_list = buff_list  # buff列表
            member.can_dispel = can_dispel  # 是否有可驱散的debuff
        #     print(f"{member.unitToken}的状态: 血量基线={health_base:.2f}%", end="; ")
        # print(f"{datetime.now().strftime('%H:%M:%S')}")

        party_members.sort(key=lambda m: m.health_score)  # 按健康分数排序，数值越低优先级越高
        return party_members

    def read_config(self, ctx: Context):
        self.dispel_blacklist = ctx.dispel_blacklist

        use_mana_balance = ctx.setting.cell(0)
        if use_mana_balance is None:
            use_mana_balance = "no"
        else:
            use_mana_balance = "yes" if use_mana_balance.mean >= 200 else "no"

        self.use_mana_balance = use_mana_balance

        can_dispel_disease_cell = ctx.setting.cell(0)
        if can_dispel_disease_cell is not None and can_dispel_disease_cell.mean >= 200:
            self.dispel_types = ["MAGIC", "DISEASE"]

    # 阈值计算器
    def threshold_calculator(self, use_calc, min_value, max_value, mana_percent) -> float:
        if not use_calc:
            return max_value
        # 线性插值计算当前阈值
        threshold = max_value - (max_value - min_value) * (mana_percent / 100)
        return threshold

    def main_rotation(self, ctx: Context) -> tuple[str, float, str]:
        self.read_config(ctx)
        party_members = self.calculate_party_health_score(ctx)
        spell_queue_window = float(ctx.spell_queue_window or 0.3)

        if not ctx.enable:
            return self.idle("总开关未开启")

        if ctx.delay:
            return self.idle("延迟开关开启")

        player = [member for member in party_members if member.unitToken == "player"][0]
        target = ctx.target
        focus = ctx.focus
        mouseover = ctx.mouseover

        # 当前法力值百分比
        powerpercent = player.powerPercent
        use_cale = self.use_mana_balance == "yes"
        # 绝望祷言血量阈值
        desperate_prayer_hp_threshold = 50
        # 无救赎受伤血量阈值
        injured_hp_threshold = self.threshold_calculator(use_cale, 80, 90, powerpercent)
        # 暗言术：灭血量阈值
        shadow_word_death_hp_threshold = 20
        # 圣光涌动阈值基线
        surge_baseline_threshold = self.threshold_calculator(use_cale, 70, 80, powerpercent)
        # 暗影愈合阈值基线
        shadow_mend_baseline_threshold = self.threshold_calculator(use_cale, 60, 70, powerpercent)
        # 苦修补血阈值
        penance_heal_hp_threshold = self.threshold_calculator(use_cale, 75, 85, powerpercent)
        # 快速治疗干拉阈值
        flash_heal_hp_threshold = self.threshold_calculator(use_cale, 40, 50, powerpercent)
        # 施法保护阈值，剩余施法时间低于此值时不打断当前施法，单位百分比。设为 90 意味着始终等待施法完成（任何技能施法时间都远小于此值）
        cast_queue_window_threshold = 90
        # 引导保护阈值，剩余引导时间低于此值时不打断当前引导，单位是百分比。设为 90 意味着始终等待引导完成
        channel_queue_window_threshold = 90

        if not player.alive:
            return self.idle("玩家已死亡")

        if player.isChatInputActive:
            return self.idle("正在聊天输入")

        if player.isMounted:
            return self.idle("骑乘中")

        if player.castIcon is not None:
            if player.castDuration is None or player.castDuration < cast_queue_window_threshold:
                return self.idle("正在施法")

        if player.channelIcon is not None:
            if player.channelDuration is None or player.channelDuration < channel_queue_window_threshold:
                return self.idle("正在引导")

        if player.isEmpowering:
            return self.idle("正在蓄力")

        if player.hasBuff("食物和饮料"):
            return self.idle("正在吃喝")

        if not player.isInCombat:
            # 未进入战斗只干
            # 1. 给自己加盾
            if ctx.spell_cooldown_ready("真言术：盾", spell_queue_window):
                if not player.has_shield:
                    return self.cast(f"player真言术盾")

            return self.idle("未进入战斗")

        # print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}", end="; ")

        # 2. 绝望祷言 冷却好且自己血量 < 50，放 绝望祷言。

        if player.health_base < desperate_prayer_hp_threshold and ctx.spell_cooldown_ready("绝望祷言", spell_queue_window, ignore_gcd=True):
            return self.cast("绝望祷言")

        # 6. 纯净术 冷却好且存在 驱散单位，对该单位放 纯净术。
        # 优先自己
        if ctx.spell_charges_ready("纯净术", 1, spell_queue_window):
            if player.can_dispel:
                return self.cast(f"player纯净术")
            for member in party_members:
                if member.can_dispel:
                    return self.cast(f"{member.unitToken}纯净术")

        # 敌对目标，必须：存在、可攻击、在战斗
        main_enemy = None
        if focus.exists and focus.canAttack and focus.isInCombat:
            main_enemy = focus
        elif target.exists and target.canAttack and target.isInCombat:
            main_enemy = target

        # 当前有敌对目标、处于战斗、且 一键辅助 == "暗言术：痛"，先补 暗言术：痛。
        # 如果没有主目标，当前目标也不再远程范围，也不可以攻击，那么就什么都做不了。
        if main_enemy is not None:
            if ctx.assisted_combat == "暗言术：痛":
                return self.cast(f"{main_enemy.unitToken}痛")

        # 无救赎且血量低于受伤阈值的队友【阈值默认 90，受法力平衡调节】
        without_atonement_and_injured_unit = [member for member in party_members if (member.atonement_remaining <= 0 and member.health_base < injured_hp_threshold)]
        without_atonement_and_injured_unit.sort(key=lambda m: m.health_score)
        # 血量低于受伤阈值的队友
        injured_unit = [member for member in party_members if member.health_base < injured_hp_threshold]
        injured_unit.sort(key=lambda m: m.health_score)  # 按健康分数
        # 无救赎的队友
        without_atonement_unit = [member for member in party_members if member.atonement_remaining <= 0]
        without_atonement_unit.sort(key=lambda m: m.health_score)  # 按健康分数排序，数值越低优先级越高
        # 最低健康分的队友
        lowest_health_score = sorted(party_members, key=lambda m: m.health_score)[0]
        # 最低血量的队友
        lowest_health_percent = sorted(party_members, key=lambda m: m.health_base)[0]
        # 没有盾的队友
        without_shield_unit = [member for member in party_members if not member.has_shield]
        without_shield_unit.sort(key=lambda m: m.health_score)  # 按健康分数排序，数值越低优先级越高

        # 受伤数量 >= 3、
        if len(injured_unit) >= 3:
            # 福音 可用，放 福音。
            if player.buffStack("福音") == 0:
                if ctx.spell_cooldown_ready("福音", spell_queue_window):
                    return self.cast(f"福音")

            # 如果耀层数 == 2，且受伤数量 > 2，放耀
            if ctx.spell_charges_ready("真言术：耀", 2, spell_queue_window):
                if player.castIcon != "真言术：耀":
                    if ctx.latest_succeeded_cast != "真言术：耀":
                        if (player.buffStack("福音") > 0) or (not player.isMoving):
                            return self.cast(f"{injured_unit[0].unitToken}耀")

        # 无救赎且受伤数量 >= 2、真言术：耀 可用、且 福音层数 > 0，放 真言术：耀。
        if len(without_atonement_and_injured_unit) >= 2:
            if player.buffStack("福音") > 0:
                if player.castIcon != "真言术：耀":
                    if ctx.spell_charges_ready("真言术：耀", 1, spell_queue_window):
                        if ctx.latest_succeeded_cast != "真言术：耀":
                            return self.cast(f"{without_atonement_and_injured_unit[0].unitToken}耀")

        # 无救赎且受伤数量 >= 3、真言术：耀 可用，放 真言术：耀。
        if len(without_atonement_and_injured_unit) >= 3:
            if player.castIcon != "真言术：耀":
                if ctx.spell_charges_ready("真言术：耀", 2, spell_queue_window):
                    if ctx.latest_succeeded_cast != "真言术：耀":
                        return self.cast(f"{without_atonement_and_injured_unit[0].unitToken}耀")

        # 灌注爆发逻辑
        # 如果有3个人，血量低于涌动血线，且灌注可用，给自己灌注。
        lower_health_count = len([member for member in party_members if member.health_base < surge_baseline_threshold])
        if lower_health_count >= 3:
            if ctx.spell_cooldown_ready("灌注", spell_queue_window, ignore_gcd=True):
                return self.cast(f"player灌注")

        # 涌动阈值 = surge_baseline_threshold - 圣光涌动CD + 涌动层数*10
        if player.hasBuff("圣光涌动"):
            surge_threshold = surge_baseline_threshold - player.buffRemain("圣光涌动") + player.buffStack("圣光涌动") * 10

            # 11. 圣光涌动 > 0 且 涌动层数 > 0，如果”无救赎且受伤”列表非空，对其中最低血量的单位放 快速治疗。
            if len(without_atonement_and_injured_unit) > 0:
                if ctx.spell_cooldown_ready("快速治疗", spell_queue_window):
                    return self.cast(f"{without_atonement_and_injured_unit[0].unitToken}快速治疗")
            # 12. 同样要求 圣光涌动 > 0 且 涌动层数 > 0，如果全队最低血量 < 涌动阈值，对最低单位放 快速治疗。
            if lowest_health_percent.health_base < surge_threshold:
                if ctx.spell_cooldown_ready("快速治疗", spell_queue_window):
                    return self.cast(f"{lowest_health_percent.unitToken}快速治疗")

        # 暗影愈合 可用、暗影层数 > 0、且最低单位血量 < 暗影愈合阈值，放 快速治疗（会施放暗影愈合）。
        if ctx.spell_cooldown_ready("暗影愈合", spell_queue_window):
            # 暗影愈合阈值 = 70 - 暗影愈合*2 + 暗影层数*15
            shadow_mend_threshold = shadow_mend_baseline_threshold - player.buffRemain("暗影愈合") * 2 + player.buffStack("暗影愈合") * 15
            if lowest_health_percent.health_base < shadow_mend_threshold:
                return self.cast(f"{lowest_health_percent.unitToken}快速治疗")

        # 真言术：盾 逻辑
        # 优先给无救赎且血量低于受伤阈值的队友上盾。
        # 其次自己没盾就上盾
        # 最后给无盾最低健康分的队友上盾。
        # 盾卡CD用出去
        if ctx.spell_cooldown_ready("真言术：盾", spell_queue_window) or ctx.spell_cooldown_ready("虚空之盾", spell_queue_window):
            if len(without_atonement_and_injured_unit) > 0:
                if without_atonement_and_injured_unit[0].health_base < injured_hp_threshold or player.hasBuff("虚空之盾"):
                    return self.cast(f"{without_atonement_and_injured_unit[0].unitToken}真言术盾")

            if not player.has_shield:
                return self.cast(f"player真言术盾")

            if len(without_shield_unit) > 0:

                return self.cast(f"{without_shield_unit[0].unitToken}真言术盾")

        # 19. 苦修 可用，且最低单位血量 < penance_heal_hp_threshold，对最低单位放 苦修。
        if ctx.spell_charges_ready("苦修", 1, spell_queue_window):
            if lowest_health_percent.health_base < penance_heal_hp_threshold:
                return self.cast(f"{lowest_health_percent.unitToken}苦修")

        # 没技能了，用快速治疗干拉血线最低的单位
        if ctx.spell_cooldown_ready("快速治疗", spell_queue_window) or ctx.spell_cooldown_ready("暗影愈合", spell_queue_window):
            if lowest_health_percent.health_base < flash_heal_hp_threshold:
                return self.cast(f"{lowest_health_percent.unitToken}快速治疗")

        # 目标是友方，不浪费防御苦修。
        if main_enemy is None:
            if ctx.spell_charges_ready("苦修", 2, spell_queue_window):
                if target.exists and target.isInCombat and (not target.isEnemy):
                    return self.cast(f"target苦修")

        # 如果当前有敌对目标且在战斗中，进入 Atonement 输出补伤阶段：
        with_atonement_count = len(party_members) - len(without_atonement_unit)
        if (main_enemy is not None) and (with_atonement_count > 0):

            # 暗言术：灭 可用、目标血量 < 20，放 暗言术：灭。
            if main_enemy.healthPercent < shadow_word_death_hp_threshold:
                if ctx.spell_charges_ready("暗言术：灭", 1, spell_queue_window):
                    return self.cast(f"{main_enemy.unitToken}灭")

            # 不在移动、心灵震爆 可用、且 有救赎数量 > 0，放 心灵震爆。
            if ctx.spell_charges_ready("心灵震爆", 1, spell_queue_window):
                if with_atonement_count > 0:
                    if not player.isMoving:
                        return self.cast(f"{main_enemy.unitToken}心灵震爆")

            # 苦修可用，放 苦修。进攻苦修打在爆震之后吃增伤。
            if ctx.spell_charges_ready("苦修", 2, spell_queue_window):
                if with_atonement_count > 0:
                    return self.cast(f"{main_enemy.unitToken}苦修")

            # 只要不在移动，就放 惩击。
            if not player.isMoving:
                if ctx.spell_cooldown_ready("惩击", spell_queue_window):
                    return self.cast(f"{main_enemy.unitToken}惩击")

        # print("END")
        return self.idle("当前没有合适动作")
