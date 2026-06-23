# from __future__ import annotations
from datetime import datetime

from terminal.context import Context
from .base import BaseRotation


class DemonHunterDevourer(BaseRotation):
    name = "噬灭DH"
    desc = "目前只适配歼灭者，奥达奇可能会有问题\n" \
        "作者：Alex-coder251\n" \
        "Repo:https://github.com/Alex-coder251/"

    def __init__(self) -> None:
        super().__init__()

        self.macroTable = {
            "target吞噬": "ALT-NUMPAD1",
            "focus吞噬": "ALT-NUMPAD2",
            "就近吞噬": "ALT-NUMPAD3",
            "target收割": "ALT-NUMPAD4",
            "虚空射线": "ALT-NUMPAD5",
            "target根除": "ALT-NUMPAD6",
            "虚空变形": "ALT-NUMPAD7",
            "target坍缩之星": "ALT-NUMPAD8",
            "target瓦解": "ALT-NUMPAD9",
            "focus瓦解": "ALT-NUMPAD0",
            "疾影": "SHIFT-NUMPAD1",
        }

    def main_rotation(self, ctx: Context) -> tuple[str, float, str]:

        # 设置项 #
        # 获取灵魂碎片
        soul_fragments_cell = ctx.spec.cell(0)
        if soul_fragments_cell is None:
            soul_fragments = 0
        else:
            soul_fragments = int(
                soul_fragments_cell.mean / 5
            )  # 与specs.lua对应 计算该单元格内所有像素的平均灰度值（0-255 范围），.mean / 5 将 0-255 的像素亮度转换为灵魂碎片数量刻度（0-51 左右）

        # print(f"当前灵魂碎片数量: {soul_fragments}")

        # 获取恶魔之怒
        # 恶魔之怒最大值，默认120，符能百分比是根据这个值来计算的。因为不同版本恶魔之怒的最大值可能不同，所以让用户自己设置这个值。
        fury_max_cell = ctx.setting.cell(0)
        if fury_max_cell is None:
            fury_max = 120
        else:
            fury_max = fury_max_cell.mean
        fury = int(ctx.player.powerPercent * fury_max / 100)

        # 设置项 #
        # 收割血量阈值，默认15%，当目标血量低于这个值时才使用根除。
        reaper_health_threshold_cell = ctx.setting.cell(4)
        if reaper_health_threshold_cell is None:
            reaper_health_threshold = 15
        else:
            reaper_health_threshold = int(reaper_health_threshold_cell.mean)

        # 设置项
        # 打断模式，默认黑名单模式，只有当施法名称不在黑名单中时才打断。另一种模式是任何可打断的施法都打断。
        dh_interrupt_mode_cell = ctx.setting.cell(1)
        if dh_interrupt_mode_cell is None:
            dh_interrupt_mode = "blacklist"
        else:
            # DejaVu 侧当前用 255 表示 blacklist、127 表示 any，这里用 200 作为分界。
            dh_interrupt_mode = (
                "blacklist" if dh_interrupt_mode_cell.mean >= 200 else "any"
            )
        interrupt_blacklist = ctx.interrupt_blacklist
        spell_stop_list = ctx.spell_stop_list

        # 设置项 #
        # 疾影的血量阈值，默认60%，当目标血量低于这个值时才使用疾影来保命。
        dh_health_threshold_cell = ctx.setting.cell(2)
        if dh_health_threshold_cell is None:
            dh_health_threshold = 60
        else:
            dh_health_threshold = int(dh_health_threshold_cell.mean)

        # 设置项 #
        # 虚空射线符能溢出阈值，默认100，当符
        fury_overflow_threshold_cell = ctx.setting.cell(3)
        if fury_overflow_threshold_cell is None:
            fury_overflow_threshold = 100
        else:
            fury_overflow_threshold = int(fury_overflow_threshold_cell.mean)

        # 设置项 #
        # 变身的血量阈值，默认30%，当目标血量高于这个值时才使用虚空变身。
        void_metamorphosis_health_threshold_cell = ctx.setting.cell(4)
        if void_metamorphosis_health_threshold_cell is None:
            void_metamorphosis_health_threshold = 30
        else:
            void_metamorphosis_health_threshold = int(
                void_metamorphosis_health_threshold_cell.mean
            )

        is_opener = float(ctx.combat_time) <= 10
        # print(f"游戏读取到的延迟容限{ctx.spell_queue_window}")
        spell_queue_window = float(ctx.spell_queue_window or 0.3)
        player = ctx.player
        target = ctx.target
        focus = ctx.focus
        mouseover = ctx.mouseover
        # print(interrupt_blacklist)
        # print(
        #     f"当前符文数量: {fury}, 当前符能: {fury}, 打断模式: {dh_interrupt_mode}, 疾影生命值阈值: {dh_health_threshold}, 虚空射线恶魔之怒溢出阈值: {fury_overflow_threshold}   "
        # )

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
        # 主目标，必须是远程的可工具目标。
        main_target = None
        if focus.exists and focus.canAttack and focus.isInRangedRange:
            main_target = focus
        elif target.exists and target.canAttack and target.isInRangedRange:
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
        # 如果玩家生命值低于设定的阈值，就优先使用疾影来保命
        phase_shift_buff_exists = ctx.player.hasBuff("疾影")
        if (
            (not phase_shift_buff_exists)
            and (player.healthPercent < dh_health_threshold)
            and ctx.spell_cooldown_ready("疾影", spell_queue_window)
        ):
            return self.cast("疾影")

        # 打断逻辑
        target_need_interrupt = False
        focus_need_interrupt = False
        if focus.exists and focus.canAttack and focus.isInRangedRange:
            if (focus.anyCastIcon is not None) and focus.anyCastIsInterruptible:
                # print(focus.anyCastIcon)
                if dh_interrupt_mode == "any":
                    focus_need_interrupt = True
                elif dh_interrupt_mode == "blacklist":
                    # 黑名单模式下，只有当施法名称不在黑名单中时才打断
                    if not (focus.anyCastIcon in interrupt_blacklist):
                        focus_need_interrupt = True

        if target.exists and target.canAttack and target.isInRangedRange:
            # if target.castIcon:
            #     if target.castIsInterruptible:
            #         print("当前目标在施法,当前目标施法可以打断")
            if (target.anyCastIcon is not None) and target.anyCastIsInterruptible:
                # print("a")
                if dh_interrupt_mode == "any":
                    target_need_interrupt = True
                elif dh_interrupt_mode == "blacklist":
                    # 黑名单模式下，只有当施法名称不在黑名单中时才打断
                    if not (target.anyCastIcon in interrupt_blacklist):
                        target_need_interrupt = True

        if ctx.spell_cooldown_ready("瓦解", spell_queue_window, ignore_gcd=True):
            if focus_need_interrupt:
                return self.cast("focus瓦解")
                # print("focus迎头痛击")
            elif target_need_interrupt:
                return self.cast("target瓦解")
                # print("target迎头痛击")

        # 停止施法名单检查：如果目标或焦点正在释放名单上的法术，则停止施法
        player_need_spell_stop = False
        trigger_spell = None  # 初始化一个变量来记录是谁触发了黑名单
        print(f"目标施放法术：{target.anyCastIcon}")
        print(f"停止施法黑名单列表：{spell_stop_list}")

        if target.exists and (target.anyCastIcon in spell_stop_list):
            trigger_spell = target.anyCastIcon
            player_need_spell_stop = True
        elif focus.exists and (focus.anyCastIcon in spell_stop_list):
            trigger_spell = focus.anyCastIcon
            player_need_spell_stop = True

        # 执行停止逻辑
        if player_need_spell_stop:
            # 这里的日志会动态显示到底是哪个技能触发的
            return self.idle(f"检测到黑名单技能 [{trigger_spell}]，停止施法")

        # 泄能打虚空射线
        if (
            (fury >= fury_overflow_threshold)
            and (not player.isMoving)
            and ctx.spell_cooldown_ready("虚空射线", spell_queue_window)
        ):
            if target.isInRangedRange:
                return self.cast("虚空射线")

        # # 近战范围有敌人，就积极用吞噬
        # if ctx.spell_charges_ready("吞噬", 2, spell_queue_window):
        #     if player.enemyCount >= 1:
        #         return self.cast("吞噬")
        #         # print("吞噬", end="; ")

        # 散落的灵魂碎片
        scattered_souls_fragments_Count = ctx.player.buffStack("灵魂残片")

        moment_of_craving_RemainingTime = ctx.player.buffRemain("噬欲时刻")

        moment_of_craving_exists = ctx.player.hasBuff("噬欲时刻")

        # 开启爆发逻辑
        if (
            (not player.isMoving)
            and (soul_fragments >= 48)
            and main_target.healthPercent > void_metamorphosis_health_threshold
            and moment_of_craving_exists
        ):
            if ctx.spell_cooldown_ready("虚空变形", spell_queue_window):
                return self.cast("虚空变形")

        # 聚能打收割
        if (
            (fury >= 70)
            and (scattered_souls_fragments_Count >= 4)
            and (main_target is not None)
        ):
            # 1. 优先检查“收割”
            if ctx.spell_cooldown_ready("收割", spell_queue_window):
                return self.cast("target收割")
            # 2. 如果“收割”没好，且“没有噬欲时刻buff”，则检查“根除”
            if not moment_of_craving_exists:
                if ctx.spell_cooldown_ready("根除", spell_queue_window):
                    return self.cast("target根除")

        # 聚能打根除
        # 优先处理“根除”逻辑 (优先级最高)
        # 条件：(碎片 >= 8 且 怒气 >= 54) 或者 (时间快到了 <= 1)
        if ctx.spell_cooldown_ready("根除", spell_queue_window):
            if (
                (scattered_souls_fragments_Count >= 8 and fury >= 50)
                or (0 < moment_of_craving_RemainingTime <= 1)
                or (main_target.healthPercent < reaper_health_threshold)
            ):
                return self.cast("target根除")

        # if (
        #     (fury >= 50)
        #     and (scattered_souls_fragments_Count >= 8)
        #     and (moment_of_craving_RemainingTime >= 1)
        # ):
        #     if ctx.spell_cooldown_ready("根除", spell_queue_window):
        #         return self.cast("target根除")

        # 爆发泄魂打坍缩之星，打坍缩之心前利用疾速多攒点魂
        collapsing_star_exists = ctx.player.hasBuff("坍缩之星")
        if collapsing_star_exists and soul_fragments >= 28:
            # 1. 只有同时满足这些条件，才执行“吞噬”
            if (fury >= 80) and (scattered_souls_fragments_Count < 8):
                return self.cast("target吞噬")

            # 2. 只要上述条件有一个不满足（即：怒气不足 80 OR 地上碎片 >= 10）
            # 且 CD 好了，就执行“坍缩之星”
            if ctx.spell_cooldown_ready("坍缩之星", spell_queue_window):
                return self.cast("target坍缩之星")

        # 大米逻辑，有了就打
        # if (
        #     collapsing_star_exists
        #     and soul_fragments >= 28
        #     and ctx.spell_cooldown_ready("坍缩之星", spell_queue_window)
        # ):
        #     return self.cast("target坍缩之星")

        # 爆发时虚空射线好了就用
        if (
            collapsing_star_exists
            and (not player.isMoving)
            and ctx.spell_cooldown_ready("虚空射线", spell_queue_window)
        ):
            if target.isInRangedRange:
                return self.cast("虚空射线")

        # 吞噬作为填充技能。
        if ctx.spell_cooldown_ready("吞噬", spell_queue_window):
            if main_target is focus:
                return self.cast("focus吞噬")
            elif main_target is target:
                return self.cast("target吞噬")
            elif player.enemyCount >= 1:
                return self.cast("就近吞噬")
        # print("end")
        return self.idle("当前没有合适动作")
