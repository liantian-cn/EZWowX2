local addonName, addonTable       = ... -- 插件入口固定写法

-- Lua 原生函数
local random                      = math.random
local min                         = math.min
local insert                      = table.insert

-- WoW 官方 API
local CreateColorCurve            = C_CurveUtil.CreateColorCurve
local Enum                        = Enum

local GetCurrentKeyBoardFocus     = GetCurrentKeyBoardFocus
local GetInventoryItemID          = GetInventoryItemID
local IsPlayerMoving              = IsPlayerMoving
local IsInGroup                   = IsInGroup
local IsInRaid                    = IsInRaid
local IsMounted                   = IsMounted
local IsUsableItem                = C_Item.IsUsableItem
local SpellIsTargeting            = SpellIsTargeting
local UnitAffectingCombat         = UnitAffectingCombat
local UnitCanAttack               = UnitCanAttack
local UnitChannelInfo             = UnitChannelInfo
local UnitEmpoweredStageDurations = UnitEmpoweredStageDurations
local UnitExists                  = UnitExists
local UnitInVehicle               = UnitInVehicle
local UnitIsDeadOrGhost           = UnitIsDeadOrGhost
local UnitIsUnit                  = UnitIsUnit
local GetUnitAuraInstanceIDs      = C_UnitAuras.GetUnitAuraInstanceIDs
local IsSpellInRange              = C_Spell.IsSpellInRange

local GetItemCooldown             = C_Container.GetItemCooldown

local LibStub                     = LibStub
local LRC                         = LibStub("LibRangeCheck-3.0")
if not LRC then
    print("|cffff0000[单位状态]|r LibRangeCheck-3.0 未找到, 模块无法工作。")
    return
end

-- DejaVu Core
local DejaVu = _G["DejaVu"]
local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell
local BadgeCell = DejaVu.BadgeCell
local MeleeRange = DejaVu.MeleeRange -- 默认的近战检测范围
local MartixInitFuncs = DejaVu.MartixInitFuncs

local function itemUsable(itemId)
    if not itemId then
        return false
    end

    local startTime, duration, enable = GetItemCooldown(itemId)
    local usable, noMana = IsUsableItem(itemId)
    return enable == 1 and duration == 0 and usable and not noMana
end

local function slotUsable(slotId)
    return itemUsable(GetInventoryItemID("player", slotId))
end

local zeroToOneCurve = CreateColorCurve()
zeroToOneCurve:SetType(Enum.LuaCurveType.Linear)
zeroToOneCurve:AddPoint(0.0, CreateColor(0, 0, 0, 1))
zeroToOneCurve:AddPoint(1.0, CreateColor(1, 1, 1, 1))

local cell = {} -- 状态单元格，提供给外部调用以更新状态显示                                    -- 触发器，提供给外部调用以触发状态更新



local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 事件框架

    -- x:45 y:14
    -- 用途：单位施法图标
    -- 更新函数：updateCastAndChannel
    cell.castIcon = BadgeCell:New(45, 14)
    -- x:47 y:14
    -- 用途：单位通道图标
    -- 更新函数：updateCastAndChannel
    cell.channelIcon = BadgeCell:New(47, 14)
    -- x:49 y:15
    -- 用途：玩家存活状态
    -- 更新函数：updateUnitBasicStatus
    cell.isAlive = Cell:New(49, 15)
    -- x:50 y:14
    -- 用途：玩家职业
    -- 更新函数：updateClassAndRole
    cell.unitClass = Cell:New(50, 14)
    -- x:50 y:15
    -- 用途：玩家角色
    -- 更新函数：updateClassAndRole
    cell.unitRole = Cell:New(50, 15)
    -- x:51 y:14
    -- 用途：玩家生命值百分比
    -- 更新函数：updateHealth
    cell.healthPercent = Cell:New(51, 14)
    -- x:51 y:15
    -- 用途：玩家主能量百分比
    -- 更新函数：updatePower
    cell.powerPercent = Cell:New(51, 15)
    -- x:52 y:14
    -- 用途：玩家是否在战斗中
    -- 更新函数：updateUnitBasicStatus
    cell.isInCombat = Cell:New(52, 14)
    -- x:52 y:15
    -- 用途：玩家是否为当前目标
    -- 更新函数：updateUnitBasicStatus
    cell.isTarget = Cell:New(52, 15)
    -- x:53 y:14
    -- 用途：玩家是否有大防御增益
    -- 更新函数：updateAura
    cell.hasBigDefense = Cell:New(53, 14)
    -- x:53 y:15
    -- 用途：玩家是否有可驱散减益
    -- 更新函数：updateAura
    cell.hasDispellableDebuff = Cell:New(53, 15)
    -- x:54 y:14
    -- 用途：玩家施法进度
    -- 更新函数：updateCastAndChannelDuration
    cell.castDuration = Cell:New(54, 14)
    -- x:54 y:15
    -- 用途：玩家通道进度
    -- 更新函数：updateCastAndChannelDuration
    cell.channelDuration = Cell:New(54, 15)
    -- x:55 y:14
    -- 用途：玩家是否处于蓄力状态
    -- 更新函数：updateCastAndChannel
    cell.isEmpowering = Cell:New(55, 14)
    -- x:55 y:15
    -- 用途：玩家蓄力阶段
    -- 更新函数：updateCastAndChannel
    cell.empoweringStage = Cell:New(55, 15)
    -- x:56 y:14
    -- 用途：玩家是否在移动
    -- 更新函数：updateMovement_start、updateMovement_stop、updateMovement_fix
    cell.isMoving = Cell:New(56, 14)
    -- x:56 y:15
    -- 用途：玩家是否在坐骑或载具中
    -- 更新函数：updateUnitActionStatus
    cell.isMounted = Cell:New(56, 15)
    -- x:57 y:14
    -- 用途：近战范围内敌人数量
    -- 更新函数：updateEnemyCount
    cell.enemyCount = Cell:New(57, 14)
    -- x:57 y:15
    -- 用途：玩家是否正在选择法术目标
    -- 更新函数：updateUnitActionStatus
    cell.isSpellTargeting = Cell:New(57, 15)
    -- x:58 y:14
    -- 用途：玩家是否正在聊天输入
    -- 更新函数：updateUnitActionStatus
    cell.isChatInputActive = Cell:New(58, 14)
    -- x:58 y:15
    -- 用途：玩家是否在队伍或团队中
    -- 更新函数：updateUnitGroupStatus
    cell.isInGroupOrRaid = Cell:New(58, 15)
    -- x:59 y:14
    -- 用途：饰品1是否可用
    -- 更新函数：updateTrinketUsable
    cell.trinket1CooldownUsable = Cell:New(59, 14)
    -- x:59 y:15
    -- 用途：饰品2是否可用
    -- 更新函数：updateTrinketUsable
    cell.trinket2CooldownUsable = Cell:New(59, 15)
    -- x:60 y:14
    -- 用途：生命石是否可用
    -- 更新函数：updateHealingItemUsable
    cell.healthstoneCooldownUsable = Cell:New(60, 14)
    -- x:60 y:15
    -- 用途：治疗药水是否可用
    -- 更新函数：updateHealingItemUsable
    cell.healingPotionCooldownUsable = Cell:New(60, 15)





    -- 说明：更新玩家的职业和小队角色显示。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：2秒。
    local function updateClassAndRole()
        cell.unitClass:setCell(COLOR.CLASS[select(2, UnitClass("player"))])
        cell.unitRole:setCell(COLOR.ROLE[UnitGroupRolesAssigned("player")] or COLOR.ROLE.NONE)
    end


    -- 说明：更新玩家的大防御增益和可驱散减益状态。
    -- 依赖事件更新：UNIT_AURA。
    -- 依赖定时刷新：2秒。
    local function updateAura()
        local bigDefenseTable = GetUnitAuraInstanceIDs("player", "HELPFUL|BIG_DEFENSIVE")
        local dispellableDebuffTable = GetUnitAuraInstanceIDs("player", "HARMFUL|RAID_PLAYER_DISPELLABLE") or {}
        cell.hasBigDefense:setCellBoolean(#bigDefenseTable > 0, COLOR.STATUS_BOOLEAN.HAS_BIG_DEFENSE, COLOR.BLACK)
        cell.hasDispellableDebuff:setCellBoolean(#dispellableDebuffTable > 0, COLOR.STATUS_BOOLEAN.HAS_DISPELLABLE_DEBUFF, COLOR.BLACK)
    end

    -- 说明：更新玩家生命值百分比。
    -- 依赖事件更新：UNIT_MAXHEALTH、UNIT_HEALTH。
    -- 依赖定时刷新：2秒。
    local function updateHealth()
        local color = UnitHealthPercent("player", false, zeroToOneCurve)
        cell.healthPercent:setCell(color)
    end

    -- 说明：更新玩家主能量百分比。
    -- 依赖事件更新：UNIT_POWER_UPDATE。
    -- 依赖定时刷新：2秒。
    local function updatePower()
        cell.powerPercent:setCell(UnitPowerPercent("player", UnitPowerType("player"), false, zeroToOneCurve))
    end

    -- 说明：更新玩家的存活、战斗和目标状态。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.5秒。
    local function updateUnitBasicStatus()
        cell.isAlive:setCellBoolean(UnitIsDeadOrGhost("player"), COLOR.BLACK, COLOR.STATUS_BOOLEAN.IS_ALIVE)
        cell.isInCombat:setCellBoolean(UnitAffectingCombat("player"), COLOR.STATUS_BOOLEAN.IS_IN_COMBAT, COLOR.BLACK)
        cell.isTarget:setCellBoolean(UnitIsUnit("player", "target"), COLOR.STATUS_BOOLEAN.IS_TARGET, COLOR.BLACK)
    end

    -- 说明：更新玩家的坐骑、选目标法术和聊天输入状态。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.5秒。
    local function updateUnitActionStatus()
        cell.isMounted:setCellBoolean(UnitInVehicle("player") or IsMounted(), COLOR.STATUS_BOOLEAN.IS_MOUNTED, COLOR.BLACK)
        cell.isSpellTargeting:setCellBoolean(SpellIsTargeting(), COLOR.STATUS_BOOLEAN.IS_SPELL_TARGETING, COLOR.BLACK)
        cell.isChatInputActive:setCellBoolean(
            GetCurrentKeyBoardFocus() ~= nil,
            COLOR.STATUS_BOOLEAN.IS_CHAT_INPUT_ACTIVE,
            COLOR.BLACK
        )
    end

    -- 说明：玩家开始移动时立即点亮移动状态。
    -- 依赖事件更新：PLAYER_STARTED_MOVING。
    -- 依赖定时刷新：无。
    local function updateMovement_start()
        cell.isMoving:setCell(COLOR.STATUS_BOOLEAN.IS_MOVING)
    end

    -- 说明：玩家停止移动时立即熄灭移动状态。
    -- 依赖事件更新：PLAYER_STOPPED_MOVING。
    -- 依赖定时刷新：无。
    local function updateMovement_stop()
        cell.isMoving:setCell(COLOR.BLACK)
    end

    -- 说明：补正移动状态，防止移动事件丢失或顺序抖动。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：2秒。
    local function updateMovement_fix()
        cell.isMoving:setCellBoolean(IsPlayerMoving(), COLOR.STATUS_BOOLEAN.IS_MOVING, COLOR.BLACK)
    end

    -- 说明：更新玩家是否在队伍或团队中。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：2秒。
    local function updateUnitGroupStatus()
        cell.isInGroupOrRaid:setCellBoolean(IsInGroup() or IsInRaid(), COLOR.STATUS_BOOLEAN.IS_IN_GROUP_OR_RAID, COLOR.BLACK)
    end

    -- 说明：更新两个饰品的可用状态。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：2秒。
    local function updateTrinketUsable()
        cell.trinket1CooldownUsable:setCellBoolean(slotUsable(13), COLOR.STATUS_BOOLEAN.TRINKET_1_USABLE, COLOR.BLACK)
        cell.trinket2CooldownUsable:setCellBoolean(slotUsable(14), COLOR.STATUS_BOOLEAN.TRINKET_2_USABLE, COLOR.BLACK)
    end

    -- 说明：更新生命石和治疗药水的可用状态。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：2秒。
    local function updateHealingItemUsable()
        cell.healthstoneCooldownUsable:setCellBoolean(itemUsable(224464), COLOR.STATUS_BOOLEAN.HEALTHSTONE_USABLE, COLOR.BLACK)
        cell.healingPotionCooldownUsable:setCellBoolean(itemUsable(258138), COLOR.STATUS_BOOLEAN.HEALING_POTION_USABLE, COLOR.BLACK)
    end

    -- 说明：更新近战范围内的敌人数量。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.5秒。
    local function updateEnemyCount()
        local count = 0

        for i = 1, 10 do
            local unit = "nameplate" .. i
            if UnitExists(unit) and UnitCanAttack("player", unit) then
                local maxRange = select(2, LRC:GetRange(unit)) or 99
                if maxRange <= MeleeRange then
                    count = count + 1
                end
            end
        end

        cell.enemyCount:setCellRGBA(min(count / 51, 1))
    end

    -- 说明：更新玩家的施法、通道和蓄力状态。
    -- 依赖事件更新：UNIT_SPELLCAST_INTERRUPTED、UNIT_SPELLCAST_START、UNIT_SPELLCAST_STOP、UNIT_SPELLCAST_SUCCEEDED、UNIT_SPELLCAST_CHANNEL_START、UNIT_SPELLCAST_CHANNEL_STOP、UNIT_SPELLCAST_FAILED、UNIT_SPELLCAST_CHANNEL_UPDATE、UNIT_SPELLCAST_EMPOWER_START、UNIT_SPELLCAST_EMPOWER_STOP。
    -- 依赖定时刷新：2秒。
    local inCasting = false
    local inChanneling = false
    local function updateCastAndChannel()
        local castIcon = select(3, UnitCastingInfo("player"))
        if castIcon then
            inCasting = true
            cell.castIcon:setCell(castIcon, COLOR.SPELL_TYPE.PLAYER_SPELL) -- 单位施法图标
            cell.channelIcon:clearCell()                                   -- 通道图标
            cell.channelDuration:clearCell()                               -- 通道持续时间
            cell.isEmpowering:clearCell()                                  -- 蓄力状态
            cell.empoweringStage:clearCell()                               -- 蓄力阶段
            return                                                         -- 在施法就不可在通道, 这里可以返回了。
        else
            inCasting = false
            cell.castIcon:clearCell()     -- 单位施法图标
            cell.castDuration:clearCell() -- 单位施法是否可中断
        end

        local channelIcon = select(3, UnitChannelInfo("player"))
        if channelIcon then
            inChanneling = true
            cell.channelIcon:setCell(channelIcon, COLOR.SPELL_TYPE.PLAYER_SPELL) -- 单位通道图标
            cell.castIcon:clearCell()                                            -- 单位施法图标
            cell.castDuration:clearCell()                                        -- 单位施法剩余
            local isEmpowered = select(9, UnitChannelInfo("player"))
            if isEmpowered then
                cell.isEmpowering:setCellBoolean(true, COLOR.STATUS_BOOLEAN.IS_EMPOWERING, COLOR.BLACK)
                cell.empoweringStage:setCell(zeroToOneCurve(UnitEmpoweredStageDurations("player")))
            else
                cell.isEmpowering:setCell(COLOR.BLACK)
                cell.empoweringStage:setCell(COLOR.BLACK)
            end -- isEmpowered
        else
            inChanneling = false
            cell.channelIcon:clearCell()     -- 通道图标
            cell.channelDuration:clearCell() -- 通道持续时间
        end
    end

    -- 说明：更新施法和通道的进度条颜色。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.1秒。
    local function updateCastAndChannelDuration()
        local castDuration = inCasting and UnitCastingDuration("player") or nil
        if castDuration then
            cell.castDuration:setCell(castDuration:EvaluateElapsedPercent(zeroToOneCurve))
        else
            cell.castDuration:clearCell()
        end

        local channelDuration = inChanneling and UnitChannelDuration("player") or nil
        if channelDuration then
            cell.channelDuration:setCell(channelDuration:EvaluateElapsedPercent(zeroToOneCurve))
        else
            cell.channelDuration:clearCell()
        end
    end

    -- UNIT_AURA
    -- 事件说明：Aura 结构变化时刷新玩家的大防御和可驱散减益状态。
    -- 对应函数：updateAura
    eventFrame:RegisterUnitEvent("UNIT_AURA", "player")

    function eventFrame:UNIT_AURA(unitToken, info)
        if info.isFullUpdate or info.removedAuraInstanceIDs or info.addedAuras then
            updateAura()
        end
    end

    -- UNIT_MAXHEALTH
    -- 事件说明：最大生命值变化时刷新生命值百分比。
    -- 对应函数：updateHealth
    eventFrame:RegisterUnitEvent("UNIT_MAXHEALTH", "player")

    function eventFrame:UNIT_MAXHEALTH(unitToken)
        updateHealth()
    end

    -- UNIT_HEALTH
    -- 事件说明：当前生命值变化时刷新生命值百分比。
    -- 对应函数：updateHealth
    eventFrame:RegisterUnitEvent("UNIT_HEALTH", "player")

    function eventFrame:UNIT_HEALTH(unitToken)
        updateHealth()
    end

    -- UNIT_POWER_UPDATE
    -- 事件说明：主能量变化时刷新能量百分比。
    -- 对应函数：updatePower
    eventFrame:RegisterUnitEvent("UNIT_POWER_UPDATE", "player")

    function eventFrame:UNIT_POWER_UPDATE(unitToken)
        updatePower()
    end

    -- PLAYER_STARTED_MOVING
    -- 事件说明：玩家开始移动时立即点亮移动状态。
    -- 对应函数：updateMovement_start
    eventFrame:RegisterEvent("PLAYER_STARTED_MOVING")

    function eventFrame:PLAYER_STARTED_MOVING()
        updateMovement_start()
    end

    -- PLAYER_STOPPED_MOVING
    -- 事件说明：玩家停止移动时立即熄灭移动状态。
    -- 对应函数：updateMovement_stop
    eventFrame:RegisterEvent("PLAYER_STOPPED_MOVING")

    function eventFrame:PLAYER_STOPPED_MOVING()
        updateMovement_stop()
    end

    -- UNIT_SPELLCAST_INTERRUPTED
    -- 事件说明：施法被打断时刷新施法、通道和蓄力状态。
    -- 对应函数：updateCastAndChannel
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTED", "player")

    function eventFrame:UNIT_SPELLCAST_INTERRUPTED(unitToken)
        updateCastAndChannel()
    end

    -- UNIT_SPELLCAST_START
    -- 事件说明：开始施法时刷新施法、通道和蓄力状态。
    -- 对应函数：updateCastAndChannel
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_START", "player")

    function eventFrame:UNIT_SPELLCAST_START(unitToken)
        updateCastAndChannel()
    end

    -- UNIT_SPELLCAST_STOP
    -- 事件说明：施法结束时刷新施法、通道和蓄力状态。
    -- 对应函数：updateCastAndChannel
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_STOP", "player")

    function eventFrame:UNIT_SPELLCAST_STOP(unitToken)
        updateCastAndChannel()
    end

    -- UNIT_SPELLCAST_SUCCEEDED
    -- 事件说明：施法成功时刷新施法、通道和蓄力状态。
    -- 对应函数：updateCastAndChannel
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", "player")

    function eventFrame:UNIT_SPELLCAST_SUCCEEDED(unitToken)
        updateCastAndChannel()
    end

    -- UNIT_SPELLCAST_CHANNEL_START
    -- 事件说明：开始通道时刷新施法、通道和蓄力状态。
    -- 对应函数：updateCastAndChannel
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_START", "player")

    function eventFrame:UNIT_SPELLCAST_CHANNEL_START(unitToken)
        updateCastAndChannel()
    end

    -- UNIT_SPELLCAST_CHANNEL_STOP
    -- 事件说明：通道结束时刷新施法、通道和蓄力状态。
    -- 对应函数：updateCastAndChannel
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_STOP", "player")

    function eventFrame:UNIT_SPELLCAST_CHANNEL_STOP(unitToken)
        updateCastAndChannel()
    end

    -- UNIT_SPELLCAST_FAILED
    -- 事件说明：施法失败时刷新施法、通道和蓄力状态。
    -- 对应函数：updateCastAndChannel
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED", "player")

    function eventFrame:UNIT_SPELLCAST_FAILED(unitToken)
        updateCastAndChannel()
    end

    -- UNIT_SPELLCAST_CHANNEL_UPDATE
    -- 事件说明：通道进度变化时刷新施法、通道和蓄力状态。
    -- 对应函数：updateCastAndChannel
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_UPDATE", "player")

    function eventFrame:UNIT_SPELLCAST_CHANNEL_UPDATE(unitToken)
        updateCastAndChannel()
    end

    -- UNIT_SPELLCAST_EMPOWER_START
    -- 事件说明：开始蓄力时刷新施法、通道和蓄力状态。
    -- 对应函数：updateCastAndChannel
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_START", "player")

    function eventFrame:UNIT_SPELLCAST_EMPOWER_START(unitToken)
        updateCastAndChannel()
    end

    -- UNIT_SPELLCAST_EMPOWER_STOP
    -- 事件说明：蓄力结束时刷新施法、通道和蓄力状态。
    -- 对应函数：updateCastAndChannel
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_STOP", "player")

    function eventFrame:UNIT_SPELLCAST_EMPOWER_STOP(unitToken)
        updateCastAndChannel()
    end

    local fastTimeElapsed = -random()     -- 0.1 秒刷新施法和通道进度
    local lowTimeElapsed = -random()      -- 0.5 秒刷新基础状态、动作状态和附近敌人数量
    local superLowTimeElapsed = -random() -- 2 秒补正事件驱动和低频状态
    eventFrame:HookScript("OnUpdate", function(frame, elapsed)
        fastTimeElapsed = fastTimeElapsed + elapsed
        if fastTimeElapsed > 0.1 then
            fastTimeElapsed = fastTimeElapsed - 0.1
            updateCastAndChannelDuration()
        end
        lowTimeElapsed = lowTimeElapsed + elapsed
        if lowTimeElapsed > 0.5 then
            lowTimeElapsed = lowTimeElapsed - 0.5
            updateEnemyCount()
            updateUnitBasicStatus()
            updateUnitActionStatus()
        end
        superLowTimeElapsed = superLowTimeElapsed + elapsed
        if superLowTimeElapsed > 2 then
            superLowTimeElapsed = superLowTimeElapsed - 2
            updateClassAndRole()
            updateAura()
            updateHealth()
            updatePower()
            updateUnitGroupStatus()
            updateTrinketUsable()
            updateHealingItemUsable()
            updateCastAndChannel()
            updateMovement_fix()
        end
    end)

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        self[event](self, ...)
    end)

    -- 首次刷新
    updateEnemyCount()
    updateUnitBasicStatus()
    updateUnitActionStatus()
    updateClassAndRole()
    updateAura()
    updateHealth()
    updatePower()
    updateUnitGroupStatus()
    updateTrinketUsable()
    updateHealingItemUsable()
    updateCastAndChannel()
    updateCastAndChannelDuration()
    updateMovement_fix()
end
insert(MartixInitFuncs, InitFrame)
