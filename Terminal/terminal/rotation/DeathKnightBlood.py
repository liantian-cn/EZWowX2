# from __future__ import annotations
from datetime import datetime

from terminal.context import Context
from .base import BaseRotation


class DeathKnightBlood(BaseRotation):
    name = "血DK"
    desc = "目前只适配死亡使者，萨莱因可能会有问题"

    def __init__(self) -> None:
        super().__init__()

        self.macroTable = {
            "target灵界打击": "ALT-NUMPAD1",
            "focus灵界打击": "ALT-NUMPAD2",
            "target精髓分裂": "ALT-NUMPAD3",
            "focus精髓分裂": "ALT-NUMPAD4",
            "target死神印记": "ALT-NUMPAD5",
            "focus死神印记": "ALT-NUMPAD6",
            "target心脏打击": "ALT-NUMPAD7",
            "focus心脏打击": "ALT-NUMPAD8",
            "target心灵冰冻": "ALT-NUMPAD9",
            "focus心灵冰冻": "ALT-NUMPAD0",
            "就近灵界打击": "SHIFT-NUMPAD1",
            "就近心脏打击": "SHIFT-NUMPAD2",
            "死神的抚摩": "SHIFT-NUMPAD3",
            "player枯萎凋零": "SHIFT-NUMPAD4",
            "cursor枯萎凋零": "SHIFT-NUMPAD7",
            "血液沸腾": "SHIFT-NUMPAD5",
            "亡者复生": "SHIFT-NUMPAD6",
            "target符文刃舞": "SHIFT-NUMPAD8",
            "focus符文刃舞": "SHIFT-NUMPAD9",
        }

    def main_rotation(self, ctx: Context) -> tuple[str, float, str]:

        runes_cell = ctx.spec.cell(0)
        if runes_cell is None:
            runes = 1
        else:
            runes = int(runes_cell.mean/10)

        # 设置项 #
        # 符能最大值，默认120，符能百分比是根据这个值来计算的。因为不同版本符能的最大值可能不同，所以让用户自己设置这个值。
        runic_power_max_cell = ctx.setting.cell(0)
        if runic_power_max_cell is None:
            runic_power_max = 120
        else:
            runic_power_max = runic_power_max_cell.mean
        runic_power = int(ctx.player.powerPercent * runic_power_max/100)
        # 设置项
        # 打断模式，默认黑名单模式，只有当施法名称不在黑名单中时才打断。另一种模式是任何可打断的施法都打断。
        dk_interrupt_mode_cell = ctx.setting.cell(1)
        if dk_interrupt_mode_cell is None:
            dk_interrupt_mode = "blacklist"
        else:
            dk_interrupt_mode = "blacklist" if dk_interrupt_mode_cell.mean >= 200 else "any"
        interrupt_blacklist = ctx.interrupt_blacklist

        # 设置项 #
        # 灵界打击的血量阈值，默认55%，当目标血量低于这个值时才使用灵界打击来保命。
        ds_health_threshold_cell = ctx.setting.cell(2)
        if ds_health_threshold_cell is None:
            ds_health_threshold = 55
        else:
            ds_health_threshold = int(ds_health_threshold_cell.mean)

        # 设置项 #
        # 灵界打击符能溢出阈值，默认100，当符
        ds_power_overflow_threshold_cell = ctx.setting.cell(3)
        if ds_power_overflow_threshold_cell is None:
            ds_power_overflow_threshold = 100
        else:
            ds_power_overflow_threshold = int(ds_power_overflow_threshold_cell.mean)

        # 设置项 #
        # 死神印记的血量阈值，默认30%，当目标血量高于这个值时才使用死神印记。
        reaper_mark_health_threshold_cell = ctx.setting.cell(4)
        if reaper_mark_health_threshold_cell is None:
            reaper_mark_health_threshold = 30
        else:
            reaper_mark_health_threshold = int(reaper_mark_health_threshold_cell.mean)

        # 设置项 #
        # 符文刃舞模式，默认手动模式，0-100战斗模式，100-200爆发模式，200以上手动模式
        dancing_rune_mode_cell = ctx.setting.cell(5)
        if dancing_rune_mode_cell is None:
            dancing_rune_mode = "manual"
        elif dancing_rune_mode_cell.mean > 200:
            dancing_rune_mode = "manual"
        elif dancing_rune_mode_cell.mean > 100:
            dancing_rune_mode = "burst_mode"
        else:
            dancing_rune_mode = "combat_mode"
        # print(f"runic_power={runic_power}, runes={runes}, dk_interrupt_mode={dk_interrupt_mode}, ds_health_threshold={ds_health_threshold}, ds_power_overflow_threshold={ds_power_overflow_threshold}, reaper_mark_health_threshold={reaper_mark_health_threshold}", end="; ")
        is_opener = float(ctx.combat_time) <= 10
        spell_queue_window = float(ctx.spell_queue_window or 0.3)
        player = ctx.player
        target = ctx.target
        focus = ctx.focus
        mouseover = ctx.mouseover
        # print(interrupt_blacklist)
        # print(f"当前符文数量: {runes}, 当前符能: {runic_power}, 打断模式: {dk_interrupt_mode}, 灵打生命值阈值: {ds_health_threshold}, 灵打符能溢出阈值: {ds_power_overflow_threshold}   ")

        # print(f"ctx.combat_time -> {ctx.combat_time:.1f}s", end="; ")
        # print(f"ctx.burst_time -> {ctx.burst_time:.1f}s", end="; ")
        # print(f"dancing_rune_mode -> {dancing_rune_mode}")

        if not ctx.enable:
            return self.idle("总开关未开启")

        if ctx.delay:
            # print("延迟开关开启，当前不执行任何技能", end="; ")
            return self.idle("延迟开关开启")

        if not player.alive:
            return self.idle("玩家已死亡")

        if player.isChatInputActive:
            return self.idle("正在聊天输入")

        if player.isMounted:
            return self.idle("骑乘中")

        if player.castIcon is not None:
            return self.idle("正在施法")

        if player.channelIcon is not None:
            # print(f"正在引导{player.channelIcon}")
            return self.idle("正在引导")

        if player.isEmpowering:
            return self.idle("正在蓄力")

        if player.hasBuff("食物和饮料"):
            return self.idle("正在吃喝")

        if not player.isInCombat:
            return self.idle("未进入战斗")

        # print(f"{datetime.now()}", end=";")
        # 主目标，必须是近战的可工具目标。
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
        # print(main_target.unitToken)
        # print(player.enemyCount)

        # 基础保命逻辑
        # 如果玩家生命值低于设定的阈值，并且符能足够，就优先使用灵界打击来保命
        # 灵界打击需要40符文能量，计算到像素误差，这里使用42

        if (player.healthPercent < ds_health_threshold) and (runic_power >= 42) and ctx.spell_cooldown_ready("灵界打击", spell_queue_window):
            if main_target is not None:
                return self.cast(main_target.unitToken + "灵界打击")
                # print(main_target.unitToken + "灵界打击")
            elif player.enemyCount >= 1:
                return self.cast("就近灵界打击")
                # print("就近灵界打击")
        # print(dk_interrupt_mode)
        # 打断逻辑
        target_need_interrupt = False
        focus_need_interrupt = False
        if focus.exists and focus.canAttack and focus.isInMeleeRange:
            if (focus.anyCastIcon is not None) and focus.anyCastIsInterruptible:
                # print(focus.anyCastIcon)
                if dk_interrupt_mode == "any":
                    focus_need_interrupt = True
                elif dk_interrupt_mode == "blacklist":
                    # 黑名单模式下，只有当施法名称不在黑名单中时才打断
                    if not (focus.anyCastIcon in interrupt_blacklist):
                        focus_need_interrupt = True

        if target.exists and target.canAttack and target.isInMeleeRange:
            # if target.castIcon:
            #     if target.castIsInterruptible:
            #         print("当前目标在施法,当前目标施法可以打断")
            if (target.anyCastIcon is not None) and target.anyCastIsInterruptible:
                # print("a")
                if dk_interrupt_mode == "any":
                    target_need_interrupt = True
                elif dk_interrupt_mode == "blacklist":
                    # 黑名单模式下，只有当施法名称不在黑名单中时才打断
                    if not (target.anyCastIcon in interrupt_blacklist):
                        target_need_interrupt = True

        if ctx.spell_cooldown_ready("心灵冰冻", spell_queue_window, ignore_gcd=True):
            if focus_need_interrupt:
                return self.cast("focus心灵冰冻")
                # print("focus迎头痛击")
            elif target_need_interrupt:
                return self.cast("target心灵冰冻")
                # print("target迎头痛击")

        # 白骨之盾
        # 骨盾还是血DK的核心逻辑
        BoneShieldCount = ctx.player.buffStack("白骨之盾")
        BoneShieldRemainingTime = ctx.player.buffRemain("白骨之盾")
        # print(f"当前白骨之盾层数: {BoneShieldCount}, 白骨之盾剩余时间: {BoneShieldRemainingTime}", end="; ")

        # 破灭，死神印记炸了后的buff
        ExterminateRemainingTime = ctx.player.buffRemain("破灭")
        ExterminateExists = ctx.player.hasBuff("破灭")
        # print(f"破灭buff剩余时间: {ExterminateRemainingTime}, 破灭buff存在: {ExterminateExists}", end="; ")

        # 死神印记
        # 死亡使者核心
        ReaperMarkUsable = ctx.spell_cooldown_ready("死神印记", spell_queue_window)
        # print(f"死神印记可用: {ReaperMarkUsable}", end="; ")

        # 死神的抚摩
        # 1符文=2骨盾
        DeathCaressUsable = ctx.spell_cooldown_ready("死神的抚摩", spell_queue_window)
        # print(f"死神的抚摩可用: {DeathCaressUsable}", end="; ")

        # 精髓分裂
        # 2符文=3骨盾
        # 可打出镰刀
        # 留镰刀则不能用
        MarrowrendUsable = ctx.spell_cooldown_ready("精髓分裂", spell_queue_window, ignore_usable=True)
        # print(f"精髓分裂可用: {MarrowrendUsable}", end="; ")

        # 补骨盾逻辑，当骨盾剩余层数<5，并且骨盾剩余时间<5秒时，要积极的补骨盾。

        if (BoneShieldCount < 5) or (BoneShieldRemainingTime < 5):
            # 如果符文多，优先用精髓分裂来补骨盾
            # 优先使用死神的抚摩，因为死神的抚摩是直接补满5层骨盾的
            # 如果死神的抚摩可用就用死神的抚摩，否则如果精髓分裂可用就用精髓分裂
            # 如果死神印记可用，并且敌人血量高于设定的阈值，就用死神印记来补骨盾。
            if ReaperMarkUsable and (main_target is not None):
                if main_target.healthPercent > reaper_mark_health_threshold:
                    return self.cast(f"{main_target.unitToken}死神印记")
                    # print(f"{main_target.unitToken}死神印记", end="; ")
            if runes >= 3 and (main_target is not None):
                return self.cast(f"{main_target.unitToken}精髓分裂")
            if DeathCaressUsable:
                return self.cast("死神的抚摩")
                # print("死神的抚摩", end="; ")

            # 精髓分裂使用条件
            # 如果没有破灭，那就随便打。
            # 如果有破别，那么只在血量高于设定的阈值使用。
            if MarrowrendUsable and (main_target is not None):
                if not ExterminateExists:
                    return self.cast(f"{main_target.unitToken}精髓分裂")
                    # print(f"{main_target.unitToken}精髓分裂", end="; ")
                else:
                    if (main_target is not None) and (main_target.healthPercent > reaper_mark_health_threshold):
                        return self.cast(f"{main_target.unitToken}精髓分裂")
                        # print(f"{main_target.unitToken}精髓分裂", end="; ")

        # 如果破灭的剩余时间小于5秒，那么无论如何都用了。
        if MarrowrendUsable and (main_target is not None) and (ExterminateRemainingTime > 0):
            return self.cast(f"{main_target.unitToken}精髓分裂")
            # print(f"{main_target.unitToken}精髓分裂", end="; ")

        # 枯萎凋零
        # 2层才用。
        # 不能用鼠标的时候。 不能移动的时候。 身上没有枯萎凋零buff的时候。
        # 鼠标指向存在，且是敌人，且在近战范围内，就用鼠标指向的目标。
        if ctx.spell_charges_ready("枯萎凋零", 1, spell_queue_window):
            if (not ctx.use_mouse) and (not player.isMoving) and (not player.hasBuff("枯萎凋零")):
                return self.cast("player枯萎凋零")
                # print("mouseover枯萎凋零", end="; ")

        # 死亡印记多打出去
        if ReaperMarkUsable and (main_target is not None):
            if main_target.healthPercent > reaper_mark_health_threshold:
                return self.cast(f"{main_target.unitToken}死神印记")
                # print(f"{main_target.unitToken}死神印记", end="; ")

        if ctx.spell_charges_ready("枯萎凋零", 1, spell_queue_window):
            if (not ctx.use_mouse) and (not player.isMoving) and (not player.hasBuff("枯萎凋零")):
                if mouseover.exists and mouseover.canAttack and mouseover.isInMeleeRange:
                    return self.cast("cursor枯萎凋零")
                    # print("mouseover枯萎凋零", end="; ")

        # 进展范围有敌人，就积极用血沸
        if ctx.spell_charges_ready("血液沸腾", 2, spell_queue_window):
            if player.enemyCount >= 1:
                return self.cast("血液沸腾")
                # print("血液沸腾", end="; ")

        # 泄能打灵打
        if (runic_power >= ds_power_overflow_threshold) and ctx.spell_cooldown_ready("灵界打击", spell_queue_window):
            if main_target is not None:
                return self.cast(main_target.unitToken + "灵界打击")
                # print(main_target.unitToken + "灵界打击")
            elif player.enemyCount >= 1:
                return self.cast("就近灵界打击")
                # print("就近灵界打击")

        # [符文刃舞]
        # 根据设置使用。
        if ctx.spell_cooldown_ready("符文刃舞", spell_queue_window) and (main_target is not None) and (player.enemyCount >= 3):
            if dancing_rune_mode == "burst_mode":
                if ctx.burst_time > 0:
                    return self.cast(f"{main_target.unitToken}符文刃舞")
            elif dancing_rune_mode == "combat_mode":
                if ctx.combat_time < 10:
                    return self.cast(f"{main_target.unitToken}符文刃舞")

        # 符文有3个以上，积极打心打
        if runes >= 3:
            if ctx.spell_cooldown_ready("心脏打击", spell_queue_window):
                if (main_target is not None):
                    return self.cast(f"{main_target.unitToken}心脏打击")
                elif player.enemyCount >= 1:
                    return self.cast("就近心脏打击")

        # 如果目标也在近战，看起来没拉更多怪的欲望，那就更积极的用血沸腾
        if ctx.spell_charges_ready("血液沸腾", 1, spell_queue_window):
            if target.exists and target.canAttack and target.isInMeleeRange:
                return self.cast("血液沸腾")
                # print("血液沸腾", end="; ")

        # 只要骨盾还没满，那就随便补。
        if BoneShieldCount < 9:
            if DeathCaressUsable:
                return self.cast("死神的抚摩")
                # print("死神的抚摩", end="; ")

        # 亡者复生是随便的填充技能。没有任何消耗，也聊胜于无。
        if ctx.spell_cooldown_ready("亡者复生", spell_queue_window):
            # print("亡者复生", end="; ")
            return self.cast("亡者复生")

        if DeathCaressUsable:
            return self.cast("死神的抚摩")

        # 心打作为填充技能。
        if runes > 1:
            if ctx.spell_cooldown_ready("心脏打击", spell_queue_window):
                if (main_target is not None):
                    return self.cast(f"{main_target.unitToken}心脏打击")
                    # print(f"{main_target.unitToken}心脏打击", end="; ")
                elif player.enemyCount >= 1:
                    return self.cast("就近心脏打击")
                    # print("就近心脏打击", end="; ")

        # print("end")
        return self.idle("当前没有合适动作")
