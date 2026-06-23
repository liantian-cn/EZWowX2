from __future__ import annotations
from typing import cast
from .base import BaseRotation
from terminal.context import Context, Unit
from datetime import datetime


class RestorationPartyMember(Unit):
    can_dispel: bool


class DruidGuardian57(BaseRotation):
    name = "57更新熊"
    desc = "适用于57版本的熊德。"

    def __init__(self) -> None:
        super().__init__()

        self.macroTable = {
            "target月火术": "ALT-NUMPAD1",
            # "填充月火术": "ALT-NUMPAD1",
            "focus月火术": "ALT-NUMPAD2",
            "填充裂伤": "ALT-NUMPAD3",
            "target裂伤": "ALT-NUMPAD3",
            "focus裂伤": "ALT-NUMPAD4",
            # "target毁灭": "ALT-NUMPAD5",
            # "focus毁灭": "ALT-NUMPAD6",
            # "target摧折": "ALT-NUMPAD7",
            # "focus摧折": "ALT-NUMPAD8",
            # "target重殴": "ALT-NUMPAD9",
            # "填充毁灭": "ALT-NUMPAD9",
            # "focus重殴": "ALT-NUMPAD0",
            # "target赤红之月": "ALT-F1",
            # "focus赤红之月": "ALT-F2",
            "target明月普照": "ALT-F3",
            # "填充明月普照": "ALT-F3",
            "focus明月普照": "ALT-F5",
            # "开怪痛击": "ALT-F6",
            "痛击": "ALT-F6",
            # "补痛击": "ALT-F6",
            # "AOE痛击": "ALT-F6",
            # "填充痛击": "ALT-F6",
            # "填充横扫": "ALT-F7",
            # "any切换目标": "ALT-F8",
            # "狂暴": "ALT-F9",
            # "化身": "SHIFT-NUMPAD1",
            # "低保铁鬃": "SHIFT-NUMPAD2",
            # "泻怒铁鬃": "SHIFT-NUMPAD2",
            # "填充铁鬃": "SHIFT-NUMPAD2",
            "狂暴回复": "SHIFT-NUMPAD3",
            "树皮术": "SHIFT-NUMPAD4",
            "player生存本能": "SHIFT-NUMPAD5",
            "target迎头痛击": "SHIFT-NUMPAD6",
            "focus迎头痛击": "SHIFT-NUMPAD7",
            "any熊形态": "SHIFT-NUMPAD8",
            "裂伤": "SHIFT-NUMPAD9",
            # "溢出裂伤": "SHIFT-NUMPAD9",
            # "补怒裂伤": "SHIFT-NUMPAD9",
            # "毁灭": "SHIFT-NUMPAD0",
            "target安抚": "SHIFT-F1",
            "focus安抚": "SHIFT-F2",
            # "野性之心": "SHIFT-F3",
            "痛击铁鬃": "SHIFT-F5",
            "碎甲咆哮": "SHIFT-F6",
            # "": "SHIFT-F7",
            "target月火铁鬃": "SHIFT-'",
            "focus月火铁鬃": "ALT-'",
        }

    def calculate_party_health_score(self, ctx: Context) -> list[RestorationPartyMember]:
        party_members: list[RestorationPartyMember] = []
        for unit in ctx.parties:
            if unit.exists and unit.isInRangedRange and unit.alive:
                # if unit.exists and unit.alive:
                party_members.append(cast(RestorationPartyMember, unit))
        party_members.append(cast(RestorationPartyMember, ctx.player))

        for member in party_members:

            # 先找出单位身上可驱散的 debuff，再按黑名单过滤。
            dispel_list = [debuff.title for debuff in member.debuff if (debuff.type in ["CURSE", "POISON"])]
            can_dispel = len(dispel_list) > 0

            member.can_dispel = can_dispel

        return party_members

    def main_rotation(self, ctx: Context) -> tuple[str, float, str]:

        # print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}, 旋转: {self.name}")
        if not ctx.enable:
            return self.idle("总开关未开启")

        if ctx.delay:
            return self.idle("延迟开关开启")

        spell_queue_window = 0.6
        # print(f"{spell_queue_window=}")
        player = ctx.player
        target = ctx.target
        focus = ctx.focus
        mouseover = ctx.mouseover

        # 狂暴回复阈值 min: 30 max: 70 default: 50 step: 2
        # 当玩家生命值低于该值时优先使用狂暴回复
        guardian_frenzied_regeneration_threshold_cell = ctx.setting.cell(2)
        if guardian_frenzied_regeneration_threshold_cell is None:
            frenzied_regeneration_threshold = 50.0  # 默认值，50%
        else:
            frenzied_regeneration_threshold = float(guardian_frenzied_regeneration_threshold_cell.mean)

        # 树皮阈值 min: 20 max: 60 default: 40 step: 2
        # 当玩家生命值低于该值时优先使用树皮术
        guardian_barkskin_threshold_cell = ctx.setting.cell(3)
        if guardian_barkskin_threshold_cell is None:
            barkskin_threshold = 40.0  # 默认值，40%
        else:
            barkskin_threshold = float(guardian_barkskin_threshold_cell.mean)

        # 生存本能阈值 min: 10 max: 50 default: 30 step: 2
        # 当玩家生命值低于该值时优先使用生存本能
        guardian_survival_instincts_threshold_cell = ctx.setting.cell(4)
        if guardian_survival_instincts_threshold_cell is None:
            survival_instincts_threshold = 30.0  # 默认值，30%
        else:
            survival_instincts_threshold = float(guardian_survival_instincts_threshold_cell.mean)

        # 打断逻辑  blacklist = 使用黑名单 all = 任意打断, default: blacklist
        guardian_interrupt_logic_cell = ctx.setting.cell(7)
        if guardian_interrupt_logic_cell is None:
            interrupt_logic = "blacklist"  # 默认值，使用黑名单
        else:
            interrupt_logic = "blacklist" if guardian_interrupt_logic_cell.mean >= 200 else "any"
        interrupt_blacklist = ctx.interrupt_blacklist

        # 化身逻辑  manual=手动 burst_mode=爆发模式 combat_mode = 战斗时间模式 default:burst_mode
        guardian_incarnation_logic_cell = ctx.setting.cell(8)
        if guardian_incarnation_logic_cell is None:
            incarnation_logic = "burst_mode"  # 默认值，爆发模式
        else:
            if guardian_incarnation_logic_cell.mean > 200:
                incarnation_logic = "manual"
            elif guardian_incarnation_logic_cell.mean > 100:
                incarnation_logic = "burst_mode"
            else:
                incarnation_logic = "combat_mode"

        # 怒气上限
        rage_limit = 100

        if not player.alive:
            return self.idle("玩家已死亡")

        if player.isChatInputActive:
            return self.idle("正在聊天输入")

        if player.isMounted:
            return self.idle("骑乘中")

        if player.castIcon is not None:
            return self.idle("正在施法")

        if player.channelIcon is not None:
            return self.idle("正在引导")

        if player.isEmpowering:
            return self.idle("正在蓄力")

        if player.hasBuff("食物和饮料"):
            return self.idle("正在吃喝")

        if not player.isInCombat:
            return self.idle("未进入战斗")

        if player.hasBuff("旅行形态"):
            return self.idle("旅行形态中")

        if not player.hasBuff("熊形态"):
            return self.cast("any熊形态")

        main_target = None
        if focus.exists and focus.canAttack and focus.isInMeleeRange:
            main_target = focus
        elif target.exists and target.canAttack and target.isInMeleeRange:
            main_target = target

        # 如果没有主目标，当前目标也不再远程范围，也不可以攻击，那么就什么都做不了。
        if main_target is None:
            if target.exists and target.canAttack and target.isInRangedRange:
                pass
            else:
                # print("当前目标不可攻击或不在远程范围，且焦点也不可攻击或不在近战范围，无法使用技能")
                return self.idle("没有合适的目标")
        # print(f"{player.powerPercent=}")
        # print(f"{rage_limit=}")
        rage = float(player.powerPercent)
        # print(f"main_target: {main_target.unitToken if main_target else None}, rage: {rage:.1f}")
        # is_opener = float(ctx.combat_time) <= opener_time
        # is_aoe = int(player.enemyCount) >= aoe_enemy_count
        enemy_in_range = int(player.enemyCount) >= 1
        player_is_stand = not player.isMoving

        # 低于 狂暴回复阈值且有怒气时优先使用狂暴回复
        if (rage > 10) and ctx.spell_charges_ready("狂暴回复", 1, spell_queue_window):
            if (player.healthPercent < frenzied_regeneration_threshold):
                if not player.hasBuff("狂暴回复"):
                    return self.cast("狂暴回复")

        # 低于树皮术阈值时优先使用树皮术
        # 树皮术不受公共CD限制，所以即使在公共CD内也可以使用，除非设置了忽略公共CD。
        # 不和生存本能叠加，所以当生存本能未准备好时才使用树皮术。
        if ctx.spell_cooldown_ready("树皮术", spell_queue_window, ignore_gcd=True):
            if (player.healthPercent < barkskin_threshold):
                if not player.hasBuff("树皮术"):
                    if not player.hasBuff("生存本能"):
                        return self.cast("树皮术")

        # 低于生存本能阈值时优先使用生存本能
        if ctx.spell_charges_ready("生存本能", 1, spell_queue_window):
            if (player.healthPercent < survival_instincts_threshold):
                if not player.hasBuff("生存本能"):
                    return self.cast("player生存本能")

        # 打断逻辑
        target_need_interrupt = False
        focus_need_interrupt = False
        if focus.exists and focus.canAttack and focus.isInMeleeRange:
            if (focus.anyCastIcon is not None) and focus.anyCastIsInterruptible:
                # print(focus.anyCastIcon)
                if interrupt_logic == "any":
                    focus_need_interrupt = True
                elif interrupt_logic == "blacklist":
                    # 黑名单模式下，只有当施法名称不在黑名单中时才打断
                    if not (focus.anyCastIcon in interrupt_blacklist):
                        focus_need_interrupt = True

        if target.exists and target.canAttack and target.isInMeleeRange:
            # if target.castIcon:
            #     if target.castIsInterruptible:
            #         print("当前目标在施法,当前目标施法可以打断")
            if (target.anyCastIcon is not None) and target.anyCastIsInterruptible:
                # print("a")
                if interrupt_logic == "any":
                    target_need_interrupt = True
                elif interrupt_logic == "blacklist":
                    # 黑名单模式下，只有当施法名称不在黑名单中时才打断
                    if not (target.anyCastIcon in interrupt_blacklist):
                        target_need_interrupt = True

        if ctx.spell_cooldown_ready("迎头痛击", spell_queue_window, ignore_gcd=True):
            if focus_need_interrupt:
                return self.cast("focus迎头痛击")
            elif target_need_interrupt:
                return self.cast("target迎头痛击")

        if ctx.assisted_combat == "明月普照" and (main_target is not None):
            return self.cast(f"{main_target.unitToken}明月普照")
        # 卡CD打明月普照，目标血量要大于10%。
        if ctx.spell_cooldown_ready("明月普照", 1.5, ignore_usable=True) and (main_target is not None):
            if main_target.healthPercent > 10:
                return self.cast(f"{main_target.unitToken}明月普照")

        # 痛击好了打痛击
        if ctx.assisted_combat == "痛击":
            if rage > 55:
                return self.cast("痛击铁鬃")
            return self.cast("痛击")
        if ctx.spell_cooldown_ready("痛击", 1.2, ignore_usable=True, ignore_gcd=True):
            # print(f"痛击 ready {datetime.now().strftime('%H:%M:%S')}")
            if enemy_in_range:
                if rage > 50:
                    return self.cast("痛击铁鬃")
                return self.cast("痛击")

        # 碎甲咆哮，4、5层痛击用
        if ctx.spell_cooldown_ready("碎甲咆哮", 1, ignore_usable=True) and (main_target is not None):
            # print(f"碎甲咆哮 ready {datetime.now().strftime('%H:%M:%S')}")
            if not ctx.spell_cooldown_ready("化身", 1, ignore_usable=True, ignore_gcd=True):
                # print("化身未准备好，优先使用碎甲咆哮")
                # if main_target.debuffStack("痛击") >= 4:
                return self.cast("碎甲咆哮")

        # 安抚逻辑
        if ctx.spell_cooldown_ready("安抚", spell_queue_window, ignore_gcd=True) and (main_target is not None):
            debuff_list = [debuff.title for debuff in main_target.debuff if (debuff.type in ["ENRAGE",])]
            if len(debuff_list) > 0:
                return self.cast(f"{main_target.unitToken}安抚")

        # 痛击CD打月火
        if ctx.spell_cooldown_ready("月火术", spell_queue_window) and (main_target is not None):
            if rage > 55:
                return self.cast(f"{main_target.unitToken}月火铁鬃")
            return self.cast(f"{main_target.unitToken}月火术")

        return self.idle("公共CD中")
