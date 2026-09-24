from __future__ import annotations
from datetime import datetime
from terminal.context import Context
from .base import BaseRotation


class DruidGuardianElune(BaseRotation):
    name = "熊(艾露恩)"
    desc = "适配5.7更新"

    def __init__(self) -> None:
        super().__init__()

        self.macroTable = {
            "target月火术": "ALT-NUMPAD1",
            "填充月火术": "ALT-NUMPAD1",
            "focus月火术": "ALT-NUMPAD2",
            "填充裂伤": "ALT-NUMPAD3",
            "target裂伤": "ALT-NUMPAD3",
            "focus裂伤": "ALT-NUMPAD4",
            "target毁灭": "ALT-NUMPAD5",
            "focus毁灭": "ALT-NUMPAD6",
            "target摧折": "ALT-NUMPAD7",
            "focus摧折": "ALT-NUMPAD8",
            "target重殴": "ALT-NUMPAD9",
            "填充毁灭": "ALT-NUMPAD9",
            "focus重殴": "ALT-NUMPAD0",
            "target赤红之月": "ALT-F1",
            "focus赤红之月": "ALT-F2",
            "target明月普照": "ALT-F3",
            "填充明月普照": "ALT-F3",
            "focus明月普照": "ALT-F5",
            "开怪痛击": "ALT-F6",
            "痛击": "ALT-F6",
            "补痛击": "ALT-F6",
            "AOE痛击": "ALT-F6",
            "填充痛击": "ALT-F6",
            "填充横扫": "ALT-F7",
            "any切换目标": "ALT-F8",
            "狂暴": "ALT-F9",
            "化身": "SHIFT-NUMPAD1",
            "低保铁鬃": "SHIFT-NUMPAD2",
            "泻怒铁鬃": "SHIFT-NUMPAD2",
            "填充铁鬃": "SHIFT-NUMPAD2",
            "狂暴回复": "SHIFT-NUMPAD3",
            "树皮术": "SHIFT-NUMPAD4",
            "player生存本能": "SHIFT-NUMPAD5",
            "target迎头痛击": "SHIFT-NUMPAD6",
            "focus迎头痛击": "SHIFT-NUMPAD7",
            "any熊形态": "SHIFT-NUMPAD8",
            "裂伤": "SHIFT-NUMPAD9",
            "溢出裂伤": "SHIFT-NUMPAD9",
            "补怒裂伤": "SHIFT-NUMPAD9",
            "毁灭": "SHIFT-NUMPAD0",
            "target安抚": "SHIFT-F1",
            "focus安抚": "SHIFT-F2",
            "野性之心": "SHIFT-F3",
        }

    def main_rotation(self, ctx: Context) -> tuple[str, float, str]:

        # print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}, 旋转: {self.name}")
        if not ctx.enable:
            return self.idle("总开关未开启")

        if ctx.delay:
            return self.idle("延迟开关开启")

        spell_queue_window = float(ctx.spell_queue_window or 0.4)
        # print(f"{spell_queue_window=}")
        player = ctx.player
        target = ctx.target
        focus = ctx.focus
        mouseover = ctx.mouseover

        # AOE敌人数量 min: 2 max: 10 default: 4 step: 1
        # 设置判定为AOE条件的敌人数量
        guardian_aoe_enemy_count_cell = ctx.setting.cell(0)
        if guardian_aoe_enemy_count_cell is None:
            aoe_enemy_count = 4  # 默认值，10级别
        else:
            aoe_enemy_count = round(guardian_aoe_enemy_count_cell.mean/10)

        # 起手时间判定 min: 5 max: 45 default: 10 step: 5
        # 即脱离战斗后多长时间内再次进入战斗时认为是起手阶段
        guardian_opener_time_cell = ctx.setting.cell(1)
        if guardian_opener_time_cell is None:
            opener_time = 10.0  # 默认值，5秒
        else:
            opener_time = float(guardian_opener_time_cell.mean)

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

        # 怒气溢出阈值 min: 60 max: 120 default: 100 step: 5
        # 高于该怒气时，不再使用攒怒技能。
        # guardian_rage_overflow_threshold_cell = ctx.setting.cell(5)
        # if guardian_rage_overflow_threshold_cell is None:
        #     rage_overflow_threshold = 100.0  # 默认值，100
        # else:
        #     rage_overflow_threshold = float(guardian_rage_overflow_threshold_cell.mean)

        # 重殴怒气下限 min: 90 max: 130 default: 120 step: 5
        # 当玩家怒气高于该值时，才会使用重殴泄怒
        # guardian_rage_threshold_cell = ctx.setting.cell(6)
        # if guardian_rage_threshold_cell is None:
        #     rage_threshold = 120.0  # 默认值，120
        # else:
        #     rage_threshold = float(guardian_rage_threshold_cell.mean)

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

        # 铁鬃逻辑  one = 保持1层 two = 保持2层 more = 无线堆叠 default: two
        # 会在铁宗持续时间过低时间使用铁宗。
        # 保持1层时，实际铁鬃覆盖1-2层。
        # 保持2层时，实际铁鬃覆盖1-3层。
        # 无限堆叠，除了保留狂暴恢复德怒气外，全部打铁鬃。
        guardian_ironfur_logic_cell = ctx.setting.cell(9)
        if guardian_ironfur_logic_cell is None:
            ironfur_logic = "two"  # 默认值，保持2层
        else:
            if (guardian_ironfur_logic_cell.mean > 120) and (guardian_ironfur_logic_cell.mean <= 134):
                ironfur_logic = "one"
            elif (guardian_ironfur_logic_cell.mean > 56) and (guardian_ironfur_logic_cell.mean <= 70):
                ironfur_logic = "two"
            elif (guardian_ironfur_logic_cell.mean > 184) and (guardian_ironfur_logic_cell.mean <= 198):
                ironfur_logic = "bypass"
            else:
                ironfur_logic = "more"

        # 怒气上限
        guardian_rage_limit_cell = ctx.setting.cell(10)
        if guardian_rage_limit_cell is None:
            rage_limit = 120.0  # 默认值，120
        else:
            rage_limit = float(guardian_rage_limit_cell.mean)
        # print(f"{interrupt_logic=} {incarnation_logic=} {ironfur_logic=} {rage_limit=}")

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

        if player.hasBuff("枭兽形态"):
            if ctx.spell_cooldown_ready("野性之心", spell_queue_window, ignore_gcd=True):
                return self.cast("野性之心")
            else:
                return self.cast("any熊形态")

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
        rage = float(player.powerPercent) * rage_limit / 100.0
        # print(f"main_target: {main_target.unitToken if main_target else None}, rage: {rage:.1f}")
        is_opener = float(ctx.combat_time) <= opener_time
        is_aoe = int(player.enemyCount) >= aoe_enemy_count
        enemy_in_range = int(player.enemyCount) >= 1
        player_is_stand = not player.isMoving

        # 开怪使用赤红之月
        if ctx.spell_cooldown_ready("赤红之月", spell_queue_window) and (main_target is not None):
            if is_opener:
                return self.cast(f"{main_target.unitToken}赤红之月")

        # 开怪优先补月火
        if ctx.spell_cooldown_ready("月火术", spell_queue_window) and (main_target is not None):
            if not main_target.hasDebuff("月火术"):
                if is_opener:
                    return self.cast(f"{main_target.unitToken}月火术")

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

        # print(f"{ctx.spell_cooldown_ready("铁鬃", spell_queue_window, ignore_gcd=True)=}")
        # print(f"{rage=}")
        if ctx.spell_cooldown_ready("铁鬃", 0.1, ignore_gcd=True) and (rage > 41):
            # 如果没有铁鬃，或者铁鬃剩余时间不足2秒，那么就先用一个铁鬃。
            if (not player.hasBuff("铁鬃")) or (player.buffRemain("铁鬃") < 2):
                return self.cast("低保铁鬃")

            if ironfur_logic == "two":
                if player.buffStack("铁鬃") < 2:
                    return self.cast("低保铁鬃")

        if ctx.spell_cooldown_ready("铁鬃", 0.1, ignore_gcd=True) and (rage > 51):
            if ironfur_logic == "more":
                return self.cast("低保铁鬃")

        if ctx.spell_cooldown_ready("安抚", spell_queue_window) and (main_target is not None):
            buff_type_list = [debuff.type for debuff in main_target.debuff]
            if "ENRAGE" in buff_type_list:
                return self.cast(f"{main_target.unitToken}安抚")
            # print(buff_type_list)
            # print("安抚好了")

        # 优先使用痛击。
        # 痛击盾是目前版本的主要治疗
        if ctx.spell_cooldown_ready("痛击", spell_queue_window, ignore_usable=True):
            # print(f"痛击 ready {datetime.now().strftime('%H:%M:%S')}")
            if enemy_in_range or (main_target is not None):
                return self.cast("痛击")
        if ctx.assisted_combat == "痛击":
            return self.cast("痛击")

        # 化身的爆发逻辑
        if ctx.spell_cooldown_ready("化身", spell_queue_window, ignore_gcd=True) or ctx.spell_cooldown_ready("狂暴", spell_queue_window):
            if incarnation_logic == "manual":
                pass
            elif incarnation_logic == "burst_mode":
                if ctx.burst_time > 0:
                    return self.cast("化身")
            elif incarnation_logic == "combat_mode":
                if is_opener:
                    return self.cast("化身")

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

        # 开怪阶段优先使用明月普照
        # 玩家站定才用
        # print(f"{main_target.unitToken if main_target else None} {ctx.assisted_combat}")
        if ctx.assisted_combat == "明月普照" and (main_target is not None):
            if main_target.healthPercent > 30:  # 目标血量高于30%时才用明月普照开怪
                if player_is_stand:
                    return self.cast(f"{main_target.unitToken}明月普照")

        # 泄怒逻辑：
        # 泄怒逻辑：
        if (rage > 110):
            if ctx.spell_cooldown_ready("铁鬃", 0.1, ignore_gcd=True):
                return self.cast("泻怒铁鬃")

        if (rage > 90):
            if (player.buffRemain("铁鬃") < 3) or (player.buffStack("铁鬃") <= 2):
                if ctx.spell_cooldown_ready("铁鬃", 0.1, ignore_gcd=True):
                    return self.cast("泻怒铁鬃")

            if ctx.spell_known("毁灭"):
                return self.cast("毁灭")

            if (main_target is not None) and ctx.spell_known("摧折"):
                return self.cast(f"{main_target.unitToken}摧折")

        # 在怒气较高时，如果铁鬃逻辑是bypass，那么就直接用毁灭或者摧折，不考虑铁鬃的层数和剩余时间。
        if (rage > 60) and (ironfur_logic == "bypass"):
            if ctx.spell_known("毁灭"):
                return self.cast("毁灭")

            if (main_target is not None) and ctx.spell_known("摧折"):
                return self.cast(f"{main_target.unitToken}摧折")

        if ctx.assisted_combat == "毁灭":
            return self.cast("毁灭")
        # 60怒才用毁灭

        if ctx.assisted_combat == "裂伤":
            return self.cast("裂伤")

        # 2层裂伤优先打出去。
        if ctx.spell_charges_ready("裂伤", 1, spell_queue_window) and (main_target is not None):
            return self.cast("溢出裂伤")

        # # 裂伤一层时，没2层优先那么高。
        # if ctx.spell_charges_ready("裂伤", 1, spell_queue_window):
        #     return self.cast("裂伤")

        # 星河守护者时，优先用掉月火。
        if ctx.spell_cooldown_ready("月火术", spell_queue_window) and (main_target is not None):
            if player.hasBuff("星河守护者"):
                if not is_aoe:
                    return self.cast(f"{main_target.unitToken}月火术")
                if player.buffRemain("星河守护者") < 4:
                    return self.cast(f"{main_target.unitToken}月火术")
            # 目标没月火，补
            if not main_target.hasDebuff("月火术"):
                return self.cast(f"{main_target.unitToken}月火术")

        if ctx.assisted_combat == "月火术" and (main_target is not None):
            return self.cast(f"{main_target.unitToken}月火术")

        if ctx.gcd_ready():
            # print(f"{rage=}")

            if rage > 60 and (main_target is not None) and ctx.spell_cooldown_ready("摧折", spell_queue_window):
                return self.cast(f"{main_target.unitToken}摧折")

            if rage > 40 and (main_target is not None) and ctx.spell_cooldown_ready("摧折", spell_queue_window):
                if (player.buffRemain("铁鬃") > 4) or (player.buffStack("铁鬃") >= 2):
                    return self.cast(f"{main_target.unitToken}摧折")

            if ctx.spell_cooldown_ready("痛击", spell_queue_window) and (main_target is not None):
                if enemy_in_range:
                    return self.cast("AOE痛击")

            if ctx.spell_cooldown_ready("月火术", spell_queue_window) and (main_target is not None):
                if player.hasBuff("星河守护者"):
                    return self.cast(f"{main_target.unitToken}月火术")

            if enemy_in_range:
                return self.cast("填充横扫")

            if ctx.spell_cooldown_ready("月火术", spell_queue_window) and (main_target is not None):
                return self.cast(f"{main_target.unitToken}月火术")

            return self.idle("当前没有合适动作")
        else:
            return self.idle("公共CD中")
