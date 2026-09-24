from __future__ import annotations
from typing import cast
from .base import BaseRotation
from terminal.context import Context, Unit
from datetime import datetime


__all__ = ["DruidRestoration",]

# 全局变量。设置窗体不够，这些修改较少的，放在变量里。
WILD_GROWTH_COUNT_THRESHOLD = 2  # 野性成长人数阈值
# TANK_HEALTH_SCORE_MULTIPLIER = 1.10
# HEALER_HEALTH_SCORE_MULTIPLIER = 0.95


class RestorationPartyMember(Unit):
    # 只在当前 rotation 内补充类型信息，不改 Unit 本体。
    rejuvenation_remaining: float
    germination_remaining: float
    regrowth_remaining: float
    wild_growth_remaining: float
    lifebloom_remaining: float
    health_score: float
    health_deficit: float
    health_base: float
    rejuvenation_count: int
    hot_count: int
    dispel_list: list[str]
    debuff_list: list[str]
    buff_list: list[str]
    can_dispel: bool


class DruidRestoration(BaseRotation):
    name = "奶德"
    desc = "奶德的循环逻辑。\n 使用\"/burst 时间\"启动预铺模式。"

    def __init__(self) -> None:
        super().__init__()

        # self.tank_health_score_multiplier = TANK_HEALTH_SCORE_MULTIPLIER  # TANK 健康分数系数
        # self.tank_deficit_ignore_percent = 15  # 计算坦克的血量时，当坦克的血量缺口小于这个百分比时，认为坦克是满血的
        # self.healer_health_score_multiplier = HEALER_HEALTH_SCORE_MULTIPLIER  # HEALER 健康分数系数
        self.ironbark_hp_threshold = 50  # 铁木树皮血量阈值
        self.barkskin_hp_threshold = 65  # 树皮术血量阈值
        self.convoke_party_hp_threshold = 65  # 万灵队血阈值
        self.convoke_single_hp_threshold = 20  # 万灵单体阈值
        self.wild_growth_count_threshold = WILD_GROWTH_COUNT_THRESHOLD  # 野性成长人数阈值
        self.wild_growth_hp_threshold = 95  # 野性成长血量阈值
        self.tranquility_party_hp_threshold = 50  # 宁静队血阈值
        self.nature_swiftness_hp_threshold = 60  # 自然迅捷血量阈值
        self.swiftmend_hp_threshold = 90  # 迅捷治愈血量
        self.swiftmend_count_threshold = 2  # 迅捷治愈人数
        self.regrowth_hp_threshold = 85  # 愈合血量
        self.rejuvenation_hp_threshold = 99  # 回春血量
        self.abundance_stack_threshold = 5  # 丰饶层数阈值
        self.hot_hp_threshold = 2.0  # 每个hot增加的血量阈值
        self.dispel_types = {"MAGIC", "CURSE", "POISON"}  # 可驱散的 debuff 类型
        self.dispel_blacklist: list[str] = []

        self.macroTable = {
            "player铁木树皮": "ALT-NUMPAD1",
            "party1铁木树皮": "ALT-NUMPAD2",
            "party2铁木树皮": "ALT-NUMPAD3",
            "party3铁木树皮": "ALT-NUMPAD4",
            "party4铁木树皮": "ALT-NUMPAD5",
            "player自然之愈": "ALT-NUMPAD6",
            "party1自然之愈": "ALT-NUMPAD7",
            "party2自然之愈": "ALT-NUMPAD8",
            "party3自然之愈": "ALT-NUMPAD9",
            "party4自然之愈": "ALT-NUMPAD0",
            "player共生关系": "ALT-F1",
            "party1共生关系": "ALT-F2",
            "party2共生关系": "ALT-F3",
            "party3共生关系": "ALT-F5",
            "party4共生关系": "ALT-F6",
            "player生命绽放": "ALT-F7",
            "party1生命绽放": "ALT-F8",
            "party2生命绽放": "ALT-F9",
            "party3生命绽放": "ALT-F10",
            "party4生命绽放": "ALT-F11",
            "player野性成长": "ALT-F12",
            "party1野性成长": "ALT-,",
            "party2野性成长": "ALT-.",
            "party3野性成长": "ALT-/",
            "party4野性成长": "ALT-;",
            "player愈合": "ALT-'",
            "party1愈合": "ALT-[",
            "party2愈合": "ALT-]",
            "party3愈合": "ALT-=",
            "party4愈合": "ALT-`",
            "player回春术": "SHIFT-NUMPAD1",
            "party1回春术": "SHIFT-NUMPAD2",
            "party2回春术": "SHIFT-NUMPAD3",
            "party3回春术": "SHIFT-NUMPAD4",
            "party4回春术": "SHIFT-NUMPAD5",
            "树皮术": "SHIFT-NUMPAD6",
            "万灵之召": "SHIFT-NUMPAD7",
            "宁静": "SHIFT-NUMPAD8",
            "自然迅捷": "SHIFT-NUMPAD9",
            "迅捷治愈": "SHIFT-NUMPAD0",
            "target斜掠": "SHIFT-F1",
            "target撕碎": "SHIFT-F2",
            "target割裂": "SHIFT-F3",
            "target野性之心": "SHIFT-F5",
            "target月火术": "SHIFT-F6",
            "target愤怒": "SHIFT-F7",
            "激活": "SHIFT-F8",
            "mouseover复生": "SHIFT-F9",
        }

    def calculate_party_health_score(self, ctx: Context) -> list[RestorationPartyMember]:
        spell_queue_window = float(ctx.spell_queue_window or 0.3)
        party_members: list[RestorationPartyMember] = []
        for unit in ctx.parties:
            if unit.exists and unit.isInRangedRange and unit.alive:
                # if unit.exists and unit.alive:
                party_members.append(cast(RestorationPartyMember, unit))
        party_members.append(cast(RestorationPartyMember, ctx.player))
        # print(f"{ctx.player.castIcon=}")

        for member in party_members:
            unit_role = member.unitRole
            health_percent = member.healthPercent
            damage_absorbs = member.damageAbsorbs
            heal_absorbs = member.healAbsorbs
            rejuvenation_remaining = member.buffRemain("回春术")
            germination_remaining = member.buffRemain("萌芽")
            regrowth_remaining = member.buffRemain("愈合")
            wild_growth_remaining = member.buffRemain("野性成长")
            lifebloom_remaining = member.buffRemain("生命绽放")

            # 血量基线使用“当前血量 - 治疗吸收”，数值越低说明越危险。
            health_base = health_percent - heal_absorbs

            # 计算hot数量，并且每个hot，增加大约点血量。
            rejuvenation_count = 0      # 回春数量，萌芽算回春（游戏机制）
            hot_count = 0               # hot机制下的总层数，回春、萌芽、愈合、野性成长、生命绽放都算
            if rejuvenation_remaining > spell_queue_window:
                rejuvenation_count += 1
                hot_count += 1
            if germination_remaining > spell_queue_window:
                rejuvenation_count += 1
                hot_count += 1
            if regrowth_remaining > spell_queue_window:
                hot_count += 1
            if wild_growth_remaining > spell_queue_window:
                hot_count += 1
            if lifebloom_remaining > spell_queue_window:
                hot_count += 1

            if member.isPlayerCastingTarget:
                if ctx.player.castIcon == "愈合":
                    # print(f"{member.unitToken}正在被施法选中{health_base}")
                    health_base = health_base + 15  # 假设玩家正在施放的愈合会被打断，那么就把这个愈合提供的血量加回基线里，数值越低说明越危险。

            # 先找出单位身上可驱散的 debuff，再按黑名单过滤。
            dispel_list = [debuff.title for debuff in member.debuff if (debuff.type in self.dispel_types)]
            can_dispel = len(dispel_list) > 0
            for dispel in dispel_list:
                if dispel in self.dispel_blacklist:
                    can_dispel = False
                    break

            # 记录完整 debuff 列表，方便调试和后续扩展判断。
            debuff_list = [debuff.title for debuff in member.debuff if (debuff.title not in ["嗜血", "英勇", "赛季词缀", "良性Debuff", "中度醉拳", "轻度醉拳", "重度醉拳"])]
            # print(f"{member.unitToken}的debuff列表: {debuff_list}")

            # 记录完整 buff 列表，方便调试和后续扩展判断。
            buff_list = [buff.title for buff in member.buff]

            # 血量缺口表示补满到 100% 还需要多少治疗量。
            health_deficit = 100 - health_base
            # 积分计算过程
            # 积分是基于血量基线的，血量基线越低说明越危险，优先级越高。
            # 积分是后续所有判断的标准。
            health_score = health_base + damage_absorbs  # 基础健康分数，治疗吸收越多越安全

            # 角色修正
            # 坦克的积分视为身上有3个hot。
            # 治疗的积分视为身上少1个hot
            if unit_role == "TANK":
                health_score += 3 * self.hot_hp_threshold
            elif unit_role == "HEALER":
                health_score -= 1 * self.hot_hp_threshold

            # hot修正 （每个 HoT 提供的血量阈值乘以 HoT 数量，越多越安全）
            health_score += hot_count * self.hot_hp_threshold
            # debuff修正，每个debuff，积分-10分
            health_score += len(debuff_list) * (-10)

            # 积分最大100分
            health_score = min(health_score, 100)

            member.rejuvenation_remaining = rejuvenation_remaining  # 回春术剩余时间
            member.germination_remaining = germination_remaining  # 萌芽剩余时间，等价于第二个回春
            member.regrowth_remaining = regrowth_remaining  # 愈合剩余时间
            member.wild_growth_remaining = wild_growth_remaining  # 野性成长剩余时间
            member.lifebloom_remaining = lifebloom_remaining  # 生命绽放剩余时间
            member.health_score = health_score  # 综合健康分数，数值越低越优先处理
            member.health_deficit = health_deficit  # 血量缺口，数值越高说明越缺治疗
            member.health_base = health_base  # 当前血量减治疗吸收后的基线，数值越低越危险
            member.dispel_list = dispel_list  # 可驱散debuff列表
            member.debuff_list = debuff_list  # debuff列表
            member.buff_list = buff_list  # buff列表
            member.rejuvenation_count = rejuvenation_count  # 回春层数，可能是 0 层、1 层、2 层
            member.can_dispel = can_dispel  # 是否有可驱散的debuff
            member.hot_count = hot_count  # 身上剩余的 HoT 数量（回春、萌芽、愈合、野性成长、生命绽放）
        #     print(f"{member.unitToken}的状态: 血量基线={health_base:.2f}%", end="; ")
        # print(f"{datetime.now().strftime('%H:%M:%S')}")
        return party_members

    def read_config(self, ctx: Context):
        restoration_ironbark_hp_threshold_cell = ctx.setting.cell(0)
        if restoration_ironbark_hp_threshold_cell is None:
            self.ironbark_hp_threshold = 50
        else:
            self.ironbark_hp_threshold = float(restoration_ironbark_hp_threshold_cell.mean)
            # print(f"{self.ironbark_hp_threshold=}", end="; ")

        restoration_barkskin_hp_threshold_cell = ctx.setting.cell(1)
        if restoration_barkskin_hp_threshold_cell is None:
            self.barkskin_hp_threshold = 65
        else:
            self.barkskin_hp_threshold = float(restoration_barkskin_hp_threshold_cell.mean)
            # print(f"{self.barkskin_hp_threshold=}", end="; ")

        restoration_convoke_party_hp_threshold_cell = ctx.setting.cell(2)
        if restoration_convoke_party_hp_threshold_cell is None:
            self.convoke_party_hp_threshold = 65
        else:
            self.convoke_party_hp_threshold = float(restoration_convoke_party_hp_threshold_cell.mean)
            # print(f"{self.convoke_party_hp_threshold=}", end="; ")

        restoration_convoke_single_hp_threshold_cell = ctx.setting.cell(3)
        if restoration_convoke_single_hp_threshold_cell is None:
            self.convoke_single_hp_threshold = 20
        else:
            self.convoke_single_hp_threshold = float(restoration_convoke_single_hp_threshold_cell.mean)
            # print(f"{self.convoke_single_hp_threshold=}", end="; ")

        restoration_wild_growth_hp_threshold_cell = ctx.setting.cell(4)
        if restoration_wild_growth_hp_threshold_cell is None:
            self.wild_growth_hp_threshold = 95
        else:
            self.wild_growth_hp_threshold = float(restoration_wild_growth_hp_threshold_cell.mean)
            # print(f"{self.wild_growth_hp_threshold=}", end="; ")

        restoration_tranquility_party_hp_threshold_cell = ctx.setting.cell(5)
        if restoration_tranquility_party_hp_threshold_cell is None:
            self.tranquility_party_hp_threshold = 50
        else:
            self.tranquility_party_hp_threshold = float(restoration_tranquility_party_hp_threshold_cell.mean)
            # print(f"{self.tranquility_party_hp_threshold=}", end="; ")

        restoration_nature_swiftness_hp_threshold_cell = ctx.setting.cell(6)
        if restoration_nature_swiftness_hp_threshold_cell is None:
            self.nature_swiftness_hp_threshold = 60
        else:
            self.nature_swiftness_hp_threshold = float(restoration_nature_swiftness_hp_threshold_cell.mean)
            # print(f"{self.nature_swiftness_hp_threshold=}", end="; ")

        restoration_swiftmend_hp_threshold_cell = ctx.setting.cell(7)
        if restoration_swiftmend_hp_threshold_cell is None:
            self.swiftmend_hp_threshold = 90
        else:
            self.swiftmend_hp_threshold = float(restoration_swiftmend_hp_threshold_cell.mean)
            # print(f"{self.swiftmend_hp_threshold=}", end="; ")

        restoration_swiftmend_count_threshold_cell = ctx.setting.cell(8)
        if restoration_swiftmend_count_threshold_cell is None:
            self.swiftmend_count_threshold = 2
        else:
            self.swiftmend_count_threshold = int(round(restoration_swiftmend_count_threshold_cell.mean)/20)
            # print(f"{self.swiftmend_count_threshold=}", end="; ")

        restoration_regrowth_hp_threshold_cell = ctx.setting.cell(9)
        if restoration_regrowth_hp_threshold_cell is None:
            self.regrowth_hp_threshold = 85
        else:
            self.regrowth_hp_threshold = float(restoration_regrowth_hp_threshold_cell.mean)
            # print(f"{self.regrowth_hp_threshold=}", end="; ")

        restoration_rejuvenation_hp_threshold_cell = ctx.setting.cell(10)
        if restoration_rejuvenation_hp_threshold_cell is None:
            self.rejuvenation_hp_threshold = 99
        else:
            self.rejuvenation_hp_threshold = float(restoration_rejuvenation_hp_threshold_cell.mean)
            # print(f"{self.rejuvenation_hp_threshold=}", end="; ")

        restoration_abundance_stack_threshold_cell = ctx.setting.cell(11)
        if restoration_abundance_stack_threshold_cell is None:
            self.abundance_stack_threshold = 5
        else:
            self.abundance_stack_threshold = int(round(restoration_abundance_stack_threshold_cell.mean)/20)
            # print(f"{self.abundance_stack_threshold=}", end="; ")

        # restoration_tank_deficit_ignore_percent_cell = ctx.setting.cell(12)
        # if restoration_tank_deficit_ignore_percent_cell is None:
        #     self.tank_deficit_ignore_percent = 15
        # else:
        #     self.tank_deficit_ignore_percent = float(restoration_tank_deficit_ignore_percent_cell.mean)
            # print(f"{self.tank_deficit_ignore_percent=}", end="; ")

        restoration_hot_hp_threshold_cell = ctx.setting.cell(13)
        if restoration_hot_hp_threshold_cell is None:
            self.hot_hp_threshold = 3.2
        else:
            self.hot_hp_threshold = float(restoration_hot_hp_threshold_cell.mean/20)
            # print(f"{self.hot_hp_threshold=}", end="; ")

        self.dispel_blacklist = ctx.dispel_blacklist

    def main_rotation(self, ctx: Context) -> tuple[str, float, str]:
        self.read_config(ctx)
        party_members = self.calculate_party_health_score(ctx)
        spell_queue_window = float(ctx.spell_queue_window or 0.3)

        if not ctx.enable:
            # print("总开关未开启")
            return self.idle("总开关未开启")

        if ctx.delay:
            # print("延迟开关开启")
            return self.idle("延迟开关开启")

        player = [member for member in party_members if member.unitToken == "player"][0]
        # for member in party_members:
        #     if (len(member.buff_list) > 0) and (member.unitToken != "player"):
        #         print(f"{member.unitToken}的buff列表: {member.buff_list}", end="; ")

        # print(f"{player.powerPercent=}", end="; ")
        # print(f"{player.powerPercent=}")
        # print(f"{player.unitToken=}", end="; ")
        # print(f"{player.health_score=}", end="; ")
        # print(f"{player.health_deficit=}", end="; ")
        # print(f"{player.health_base=}", end="; ")
        # print(f"{player.rejuvenation_remaining=}", end="; ")
        # print(f"{player.rejuvenation_count=}", end="; ")
        # print(self.ironbark_hp_threshold)
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

        if player.hasBuff("旅行形态"):
            return self.idle("旅行形态中")

        # 队伍平均健康分数。
        health_score_avg = sum(member.health_score for member in party_members) / len(party_members)
        # 当前最低健康分的目标
        lowest_health_score_unit = min(party_members, key=lambda member: member.health_score)
        lowest_health_score = lowest_health_score_unit.health_score
        # 丰饶层数供迅捷治愈逻辑使用。
        abundance_stack = player.buffStack("丰饶")
        # print(f"队伍平均治疗基线: {party_health_base_avg:.2f}, 最低血量的队员: {lowest_health_base_member.unitToken}({lowest_health_base_member.health_base:.2f}), 丰饶层数: {abundance_stack}")

        # print(f"{in_cat_form=}", end="; ")
        player_in_movement = player.isMoving
        player_is_stand = not player_in_movement
        # print(f"{player.unitToken}的状态: {'移动中' if player_in_movement else '站立不动'}", end="; ")
        tank_members = [member for member in party_members if member.unitRole == "TANK"]
        if tank_members:
            tank_member = tank_members[0]
        else:
            tank_member = None
        # print(f"{tank_member.unitToken if tank_member else '没有坦克'}的血量基线: {tank_member.health_score if tank_member else 'N/A'}", end="; ")

        # 1.2 共生关系逻辑（优先补坦克常驻 buff）
        # 有坦克且共生关系可用时，检查坦克身上是否还没有共生关系。
        # 如果满足条件，就给坦克补共生关系。
        # if (tank_member is not None) and ctx.spell_cooldown_ready("共生关系", spell_queue_window):
        #     if not tank_member.hasBuff("共生关系"):
        #         return self.cast(f"{tank_member.unitToken}共生关系")
            # print(f"对{tank_member.unitToken}施放共生关系", end="; ")

        if (not player.isInCombat) and (ctx.burst_time <= 0):  # 爆发模式则忽略战斗判断，直接开始预铺
            return self.idle("未进入战斗")
        # if not player.hasBuff("熊形态"):
        #     return self.cast("any熊形态")

        # 0.1 铁木树皮逻辑（优先保最低血线目标）
        # 铁木树皮冷却完成时，检查当前最低健康分的队友是否低于铁木树皮阈值。
        # 如果满足条件，就对这个最低健康分目标施放铁木树皮。
        # 铁木树皮不对坦克释放。
        # print(lowest_health_score_unit.health_score, end="; ")
        # print(1)
        if ctx.spell_cooldown_ready("铁木树皮", spell_queue_window, ignore_gcd=True):
            # print("铁木树皮冷却好了", end="; ")
            # print(lowest_health_score_unit.unitToken, end="; ")
            # print(f"血量基线: {lowest_health_score_unit.health_score}", end="; ")
            if lowest_health_score < self.ironbark_hp_threshold:
                return self.cast(f"{lowest_health_score_unit.unitToken}铁木树皮")
                # print(f"对{lowest_health_score_unit.unitToken}施放铁木树皮", end="; ")

        # 0.2 树皮术逻辑（自己保命）
        # 树皮术冷却完成时，检查玩家自己的健康分是否低于树皮术阈值。
        # 如果满足条件，就对自己施放树皮术。
        if ctx.spell_cooldown_ready("树皮术", spell_queue_window, ignore_gcd=True):
            # print("树皮术冷却好了", end="; ")
            # print(f"血量基线: {player.health_base}", end="; ")
            if player.health_score < self.barkskin_hp_threshold:
                return self.cast("树皮术")
                # print("对自己施放树皮术", end="; ")

        # 0.3 自然之愈逻辑（优先驱散可驱散 debuff）
        # 自然之愈可用时，顺序检查队伍成员身上是否存在可驱散且不在黑名单里的 debuff。
        # 找到符合条件的成员后，就对该成员施放自然之愈。
        if ctx.spell_charges_ready("自然之愈", 1, spell_queue_window):
            for member in party_members:
                if member.can_dispel:
                    return self.cast(f"{member.unitToken}自然之愈")
                    # print(f"对{member.unitToken}施放自然之愈驱散", end="; ")

        # 1.1 生命绽放逻辑（优先维持坦克常驻 HoT）
        # 有坦克且生命绽放可用时，检查坦克身上的生命绽放剩余时间是否低于 3.5 秒。
        # 如果满足条件，就给坦克补生命绽放。
        if (tank_member is not None) and ctx.spell_cooldown_ready("生命绽放", spell_queue_window):
            if tank_member.buffRemain("生命绽放") < 3.5:
                return self.cast(f"{tank_member.unitToken}生命绽放")
                # print(f"对{tank_member.unitToken}施放生命绽放", end="; ")

        # 1.3 万灵之召逻辑（队血危险或单体濒危时开爆发）
        # 万灵之召可用时，检查队伍平均健康分是否低于队血阈值，或最低健康分是否低于单体阈值。
        # 只要两种条件任意一种满足，就施放万灵之召。
        if ctx.spell_cooldown_ready("万灵之召", spell_queue_window):
            if (health_score_avg <= self.convoke_party_hp_threshold):
                return self.cast("万灵之召")
                # print("施放万灵之召", end="; ")

            if (lowest_health_score <= self.convoke_single_hp_threshold):
                return self.cast("万灵之召")
                # print("施放万灵之召", end="; ")

        # 1.4 野性成长逻辑（满足人数后补群 HoT）
        # 玩家站定且野性成长可用时，统计血量基线低于野性成长阈值的人数是否达到设定人数。
        # 如果满足条件，就把野性成长打给当前血量基线最低的单位。
        # wild_growth_targets = [member for member in party_members if member.health_score < self.wild_growth_hp_threshold]
        # print(f"野性成长目标: {wild_growth_targets}")
        if ctx.spell_cooldown_ready("野性成长", spell_queue_window) and player_is_stand:
            # print("野性成长冷却好了", end="; ")
            wild_growth_targets = [member for member in party_members if member.health_score < self.wild_growth_hp_threshold]
            # print(f"野性成长目标: {wild_growth_targets}")
            if len(wild_growth_targets) >= self.wild_growth_count_threshold:
                return self.cast(f"{lowest_health_score_unit.unitToken}野性成长")
                # print(f"对{lowest_health_score_unit.unitToken}施放野性成长", end="; ")

        # 1.5 宁静逻辑（大掉血时补强力群疗）
        # 玩家站定且宁静可用时，检查队伍平均血量基线是否低于宁静阈值。
        # 如果满足条件，就直接施放宁静。
        if ctx.spell_cooldown_ready("宁静", spell_queue_window) and player_is_stand:
            if health_score_avg <= self.tranquility_party_hp_threshold:
                return self.cast("宁静")
                # print("施放宁静", end="; ")

        # 1.6 自然迅捷逻辑（最低血线危险时预备瞬发）
        # 自然迅捷可用时，检查当前最低健康分的单位是否低于自然迅捷阈值。
        # 如果满足条件，就先施放自然迅捷。
        # 针对非坦克玩家
        if ctx.spell_cooldown_ready("自然迅捷", spell_queue_window, ignore_gcd=True):
            if lowest_health_score < self.nature_swiftness_hp_threshold:
                return self.cast("自然迅捷")
                # print("施放自然迅捷", end="; ")

        # 1.7 迅捷治愈逻辑
        # 统计迅捷治愈的人数：健康分低于阈值，且身上有2层hot。
        # 如果满足人数条件，就施放迅捷治愈。
        if ctx.spell_charges_ready("迅捷治愈", 1, spell_queue_window):
            swiftmend_targets = [member for member in party_members if (member.health_score < self.swiftmend_hp_threshold) and (member.hot_count > 1)]
            if (len(swiftmend_targets) >= self.swiftmend_count_threshold):
                return self.cast("迅捷治愈")
                # print("施放迅捷治愈", end="; ")

        # 1.8 愈合逻辑（优先单抬已有 HoT 的低血目标）
        # 愈合可用时，检查最低血量基线目标是否低于愈合阈值，并且身上至少已有一个 HoT。
        # 如果满足条件，就对这个最低血量基线目标施放愈合。
        if ctx.spell_cooldown_ready("愈合", spell_queue_window) and player_is_stand:
            if (lowest_health_score < self.regrowth_hp_threshold):
                if (lowest_health_score_unit.hot_count > 1):
                    return self.cast(f"{lowest_health_score_unit.unitToken}愈合")
                else:
                    return self.cast(f"{lowest_health_score_unit.unitToken}回春术")
                # print(f"对{lowest_health_score_unit.unitToken}施放愈合", end="; ")

        # 1.9 回春术逻辑（优先补 0 层回春）
        # 回春术可用时，筛选回春数量为 0 且健康分低于回春阈值的队友。
        # 在这些目标里，选择 health_score 最低的单位施放回春术。
        if ctx.spell_cooldown_ready("回春术", spell_queue_window):
            rejuvenation_targets = [member for member in party_members if (member.rejuvenation_count == 0) and (member.health_score < self.rejuvenation_hp_threshold)]
            if rejuvenation_targets:
                target = min(rejuvenation_targets, key=lambda member: member.health_score)
                return self.cast(f"{target.unitToken}回春术")
                # print(f"对{target.unitToken}施放回春术", end="; ")

        # 1.10 回春术逻辑（继续补到 2 层回春）
        # 回春术可用时，筛选回春数量为 1 且健康分低于回春阈值的队友。
        # 在这些目标里，选择 health_score 最低的单位继续补第二层回春。
        if ctx.spell_cooldown_ready("回春术", spell_queue_window):
            rejuvenation_targets = [member for member in party_members if (member.rejuvenation_count == 1) and (member.health_score < self.rejuvenation_hp_threshold)]
            if rejuvenation_targets:
                target = min(rejuvenation_targets, key=lambda member: member.health_score)
                return self.cast(f"{target.unitToken}回春术")
                # print(f"对{target.unitToken}施放回春术", end="; ")

        # 2.1 爆发预铺逻辑（爆发期尽量补满回春层数）
        # 爆发模式开启且回春术可用时，先给 0 层回春的目标补第一层，再给 1 层回春的目标补第二层。
        # 每一轮都在候选目标里选择 health_score 最低的单位施放回春术。
        if ctx.spell_cooldown_ready("回春术", spell_queue_window) and (ctx.burst_time > 0):
            # 先给没回春的铺一圈
            rejuvenation_targets = [member for member in party_members if (member.rejuvenation_count == 0)]
            # rejuvenation_targets = [member for member in party_members if (member.rejuvenation_count == 0)]

            # for member in rejuvenation_targets:
            #     print(f"{member.unitToken=} {member.health_score=} {member.unitRole=}", end="; ")
            # print()
            # print("")
            if rejuvenation_targets:
                target = min(rejuvenation_targets, key=lambda member: member.health_score)
                return self.cast(f"{target.unitToken}回春术")
                # print(f"对{target.unitToken}施放回春术", end="; ")

            # 再给有回春的铺一圈第二层
            rejuvenation_targets = [member for member in party_members if (member.rejuvenation_count == 1)]
            if rejuvenation_targets:
                target = min(rejuvenation_targets, key=lambda member: member.health_score)
                return self.cast(f"{target.unitToken}回春术")
                # print(f"对{target.unitToken}施放回春术", end="; ")

            # 再给回春层数小于4的铺一圈第三层
            rejuvenation_targets = [member for member in party_members if (member.rejuvenation_remaining < 4) or (member.germination_remaining < 4)]
            if rejuvenation_targets:
                target = min(rejuvenation_targets, key=lambda member: member.health_score)
                return self.cast(f"{target.unitToken}回春术")

        # 3.0 保持丰饶
        # 3.1 如果丰饶层数小于阈值，给无回春目标释放回春
        # 一个玩家最多贡献2个丰饶，在阈值之上需要进一步限制。
        party_count = len(party_members)  # 队伍人数
        abundance_stack_threshold_per_unit = self.abundance_stack_threshold / 5  # 当前阈值对应平均每个玩家的丰饶数
        abundance_stack_limit = party_count * abundance_stack_threshold_per_unit    # 适合当前小队的丰饶层数
        if ctx.spell_cooldown_ready("回春术", spell_queue_window) and (abundance_stack < abundance_stack_limit):
            rejuvenation_targets = [member for member in party_members if (member.rejuvenation_count == 0)]

            if rejuvenation_targets:
                target = min(rejuvenation_targets, key=lambda member: member.health_score)
                return self.cast(f"{target.unitToken}回春术")
                # print(f"对{target.unitToken}施放回春术", end="; ")

            rejuvenation_targets = [member for member in party_members if (member.rejuvenation_count == 1)]
            if rejuvenation_targets:
                target = min(rejuvenation_targets, key=lambda member: member.health_score)
                return self.cast(f"{target.unitToken}回春术")
                # print(f"对{target.unitToken}施放回春术", end="; ")

        # 3.2 激活
        # 蓝低于90，就用了。
        if ctx.spell_cooldown_ready("激活", spell_queue_window, ignore_gcd=True):
            if (player.powerPercent < 90):
                return self.cast(f"激活")

        # 3.2 复生逻辑
        # 如果鼠标指向，死亡、是友方。
        # 如果复生在CD。人物不在移动。
        # 复生
        mouseover = ctx.mouseover
        if mouseover.exists and (not mouseover.alive) and (not mouseover.isEnemy):
            if ctx.spell_cooldown_ready("复生", spell_queue_window) and player_is_stand:
                return self.cast(f"mouseover复生")

        # 针对所有健康分数大于99，但血量缺口大于10的目标
        not_finished_targets = [member for member in party_members if (member.health_score > 99) and (member.health_deficit > 10)]
        # 按血量缺口，从大到小排序，
        not_finished_targets.sort(key=lambda member: member.health_deficit, reverse=True)
        if len(not_finished_targets) > 0:
            # print(f"健康分数大于99但血量缺口较大的目标: {[member.unitToken for member in not_finished_targets]}", end="; ")
            if ctx.spell_cooldown_ready("愈合", spell_queue_window):
                target = not_finished_targets[0]
                return self.cast(f"{target.unitToken}愈合")
                # print(f"对{target.unitToken}施放愈合", end="; ")
        # 4.0 战斗部分，在治疗之外的填充

        target = ctx.target
        combat_point_cell = ctx.spec.cell(0)  # 连击点
        in_cat_form = player.hasBuff("猎豹形态")
        if combat_point_cell is not None:
            combat_point = combat_point_cell.mean/51
        else:
            combat_point = 0

        # 4.1 近战逻辑（没有合适的治疗目标时就近打怪）
        # 在猫形态，野性之心能用则野性之心
        # 连击点数 = 5。释放割裂，目标没有割裂则割裂。
        # 连击点数 < 5
        #   - 目标没有斜掠则斜掠
        #   - 撕碎
        if target.exists and target.isInMeleeRange and target.canAttack:
            if in_cat_form and ctx.spell_cooldown_ready("野性之心", spell_queue_window):
                # print(f"对{target.unitToken}施放野性之心", end="; ")
                return self.cast("target野性之心")
            elif (combat_point >= 5) and in_cat_form and ctx.spell_cooldown_ready("割裂", spell_queue_window) and (not target.hasDebuff("割裂")):
                return self.cast("target割裂")
            elif ctx.spell_cooldown_ready("斜掠", spell_queue_window) and (not target.hasDebuff("斜掠")):
                return self.cast("target斜掠")
            elif ctx.spell_cooldown_ready("撕碎", spell_queue_window):
                return self.cast("target撕碎")

        if target.exists and target.isInRangedRange and (not target.isInMeleeRange) and target.canAttack and target.isInCombat:
            if ctx.spell_cooldown_ready("月火术", spell_queue_window) and (not target.hasDebuff("月火术")):
                return self.cast("target月火术")
            elif ctx.spell_cooldown_ready("愤怒", spell_queue_window):
                return self.cast("target愤怒")

        # print(f"当前战斗积分: {combat_point:.2f}", end="; ")

        # print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}")
        return self.idle("当前没有合适动作")
