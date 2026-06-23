local addonName, addonTable = ... -- luacheck: ignore addonName -- 插件入口固定写法

-- Lua 原生函数
local format = string.format
local random = math.random
local select = select
local insert = table.insert

-- WoW 官方 API
local CreateColor = CreateColor
local CreateColorCurve = C_CurveUtil.CreateColorCurve
local Enum = Enum
local CreateFrame = CreateFrame
local UnitAffectingCombat = UnitAffectingCombat
local UnitCanAttack = UnitCanAttack
local UnitClass = UnitClass
local UnitExists = UnitExists
local UnitGroupRolesAssigned = UnitGroupRolesAssigned
local UnitHealthPercent = UnitHealthPercent
local UnitIsDeadOrGhost = UnitIsDeadOrGhost
local UnitIsEnemy = UnitIsEnemy
local UnitIsUnit = UnitIsUnit
local UnitPowerPercent = UnitPowerPercent
local UnitPowerType = UnitPowerType

local DejaVu = _G["DejaVu"]
local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell
local RangedRange = DejaVu.RangedRange -- 默认的远程检测范围
local MeleeRange = DejaVu.MeleeRange   -- 默认的近战检测范围

local LibStub = LibStub
local LRC = LibStub("LibRangeCheck-3.0")
if not LRC then
    print("|cffff0000[单位状态]|r LibRangeCheck-3.0 未找到, 模块无法工作。")
    return
end
local MartixInitFuncs = DejaVu.MartixInitFuncs


local function InitFrame()
    for partyIndex = 1, 4 do
        -- eventFrame 构建
        local eventFrame = CreateFrame("Frame")
        local UNIT_KEY = format("party%d", partyIndex)
        local BASE_X = 21 * partyIndex
        local cell = {}
        local GetUnitAuraInstanceIDs = C_UnitAuras.GetUnitAuraInstanceIDs
        local zeroToOneCurve = CreateColorCurve()
        zeroToOneCurve:SetType(Enum.LuaCurveType.Linear)
        zeroToOneCurve:AddPoint(0.0, CreateColor(0, 0, 0, 1))
        zeroToOneCurve:AddPoint(1.0, CreateColor(1, 1, 1, 1))

        -- cell 实例构建

        -- x:BASE_X - 9 y:24
        -- 用途：队友单位是否存在
        -- 更新函数：updateUnitExists
        cell.exists = Cell:New(BASE_X - 9, 24) -- 单位存在状态
        -- x:BASE_X - 9 y:25
        -- 用途：队友单位是否存活
        -- 更新函数：updateUnitBasicStatus
        cell.isAlive = Cell:New(BASE_X - 9, 25) -- 单位是否存活
        -- x:BASE_X - 8 y:24
        -- 用途：队友单位职业
        -- 更新函数：updateClassAndRole
        cell.unitClass = Cell:New(BASE_X - 8, 24) -- 单位职业
        -- x:BASE_X - 8 y:25
        -- 用途：队友单位职责
        -- 更新函数：updateClassAndRole
        cell.unitRole = Cell:New(BASE_X - 8, 25) -- 单位角色
        -- x:BASE_X - 7 y:24
        -- 用途：队友单位生命值百分比
        -- 更新函数：updateHealth
        cell.healthPercent = Cell:New(BASE_X - 7, 24) -- 单位生命值百分比
        -- x:BASE_X - 7 y:25
        -- 用途：队友单位能量值百分比
        -- 更新函数：updatePower
        cell.powerPercent = Cell:New(BASE_X - 7, 25) -- 单位能量百分比
        -- x:BASE_X - 6 y:24
        -- 用途：队友单位是否敌对
        -- 更新函数：updateUnitBasicStatus
        cell.isEnemy = Cell:New(BASE_X - 6, 24) -- 单位是否敌对
        -- x:BASE_X - 6 y:25
        -- 用途：队友单位是否可攻击
        -- 更新函数：updateUnitBasicStatus
        cell.canAttack = Cell:New(BASE_X - 6, 25) -- 单位是否可攻击
        -- x:BASE_X - 5 y:24
        -- 用途：队友单位是否在远程范围内
        -- 更新函数：updateRangeStatus
        cell.isInRangedRange = Cell:New(BASE_X - 5, 24) -- 单位是否在远程范围内
        -- x:BASE_X - 5 y:25
        -- 用途：队友单位是否在近战范围内
        -- 更新函数：updateRangeStatus
        cell.isInMeleeRange = Cell:New(BASE_X - 5, 25) -- 单位是否在近战范围内
        -- x:BASE_X - 4 y:24
        -- 用途：队友单位是否在战斗中
        -- 更新函数：updateUnitBasicStatus
        cell.isInCombat = Cell:New(BASE_X - 4, 24) -- 单位是否在战斗中
        -- x:BASE_X - 4 y:25
        -- 用途：队友单位是否为当前目标
        -- 更新函数：updateUnitBasicStatus
        cell.isTarget = Cell:New(BASE_X - 4, 25) -- 单位是否为目标
        -- x:BASE_X - 3 y:24
        -- 用途：队友单位是否有大防御
        -- 更新函数：updateAura
        cell.hasBigDefense = Cell:New(BASE_X - 3, 24) -- 有大防御值
        -- x:BASE_X - 3 y:25
        -- 用途：队友单位是否有可驱散减益
        -- 更新函数：updateAura
        cell.hasDispellableDebuff = Cell:New(BASE_X - 3, 25) -- 有可驱散的减益效果
        local unitExists = false

        -- update 函数构建

        -- 清空当前队友格子的所有状态
        -- 当队友离队、离线或当前 party 槽位为空时使用
        local function clearAll()
            cell.exists:clearCell()               -- 单位存在状态
            cell.isAlive:clearCell()              -- 单位是否存活
            cell.unitClass:clearCell()            -- 单位职业
            cell.unitRole:clearCell()             -- 单位角色
            cell.healthPercent:clearCell()        -- 单位生命值百分比
            cell.powerPercent:clearCell()         -- 单位能量百分比
            cell.isEnemy:clearCell()              -- 单位是否敌对
            cell.canAttack:clearCell()            -- 单位是否可攻击
            cell.isInRangedRange:clearCell()      -- 单位是否在远程范围内
            cell.isInMeleeRange:clearCell()       -- 单位是否在近战范围内
            cell.isInCombat:clearCell()           -- 单位是否在战斗中
            cell.isTarget:clearCell()             -- 单位是否为目标
            cell.hasBigDefense:clearCell()        -- 有大防御值
            cell.hasDispellableDebuff:clearCell() -- 有可驱散的减益效果
        end

        -- 说明：检测当前队友槽位是否存在有效单位，并刷新存在状态。
        -- 依赖事件更新：GROUP_*、PARTY_MEMBER_*、UNIT_FLAGS、UNIT_TARGETABLE_CHANGED。
        -- 依赖定时刷新：2 秒。
        local function updateUnitExists()
            unitExists = UnitExists(UNIT_KEY)

            if not unitExists then
                clearAll()
                return
            end

            cell.exists:setCell(COLOR.STATUS_BOOLEAN.EXISTS)
        end

        -- 说明：刷新当前队友的职业和职责显示。
        -- 依赖事件更新：GROUP_*、PLAYER_ROLES_ASSIGNED。
        -- 依赖定时刷新：2 秒。
        local function updateClassAndRole()
            if not unitExists then
                return
            end

            local classFile = select(2, UnitClass(UNIT_KEY))
            cell.unitClass:setCell(COLOR.CLASS[classFile] or COLOR.BLACK)
            cell.unitRole:setCell(COLOR.ROLE[UnitGroupRolesAssigned(UNIT_KEY)] or COLOR.ROLE.NONE)
        end

        -- 说明：刷新当前队友的生命值百分比显示。
        -- 依赖事件更新：UNIT_HEALTH、UNIT_MAXHEALTH。
        -- 依赖定时刷新：2 秒。
        local function updateHealth()
            if not unitExists then
                return
            end

            cell.healthPercent:setCell(UnitHealthPercent(UNIT_KEY, false, zeroToOneCurve))
        end

        -- 说明：刷新当前队友的能量值百分比显示。
        -- 依赖事件更新：UNIT_POWER_UPDATE、UNIT_MAXPOWER、UNIT_DISPLAYPOWER。
        -- 依赖定时刷新：2 秒。
        local function updatePower()
            if not unitExists then
                return
            end

            cell.powerPercent:setCell(UnitPowerPercent(UNIT_KEY, UnitPowerType(UNIT_KEY), false, zeroToOneCurve))
        end

        -- 说明：刷新当前队友的存活、友敌、可攻击、战斗和目标状态。
        -- 依赖事件更新：UNIT_FLAGS、UNIT_FACTION、PLAYER_TARGET_CHANGED、UNIT_TARGETABLE_CHANGED。
        -- 依赖定时刷新：2 秒。
        local function updateUnitBasicStatus()
            if not unitExists then
                return
            end

            cell.isAlive:setCellBoolean(UnitIsDeadOrGhost(UNIT_KEY), COLOR.BLACK, COLOR.STATUS_BOOLEAN.IS_ALIVE)
            cell.isEnemy:setCellBoolean(UnitIsEnemy(UNIT_KEY, "player"), COLOR.STATUS_BOOLEAN.IS_ENEMY, COLOR.BLACK)
            cell.canAttack:setCellBoolean(UnitCanAttack("player", UNIT_KEY), COLOR.STATUS_BOOLEAN.CAN_ATTACK, COLOR.BLACK)
            cell.isInCombat:setCellBoolean(UnitAffectingCombat(UNIT_KEY), COLOR.STATUS_BOOLEAN.IS_IN_COMBAT, COLOR.BLACK)
            cell.isTarget:setCellBoolean(UnitIsUnit(UNIT_KEY, "target"), COLOR.STATUS_BOOLEAN.IS_TARGET, COLOR.BLACK)
        end

        -- 说明：刷新当前队友的远程和近战距离状态。
        -- 依赖事件更新：无。
        -- 依赖定时刷新：0.5 秒。
        local function updateRangeStatus()
            if not unitExists then
                return
            end

            local maxRange = select(2, LRC:GetRange(UNIT_KEY)) or 99
            cell.isInRangedRange:setCellBoolean(
                maxRange <= RangedRange,
                COLOR.STATUS_BOOLEAN.IS_IN_RANGED_RANGE,
                COLOR.BLACK
            )
            cell.isInMeleeRange:setCellBoolean(
                maxRange <= MeleeRange,
                COLOR.STATUS_BOOLEAN.IS_IN_MELEE_RANGE,
                COLOR.BLACK
            )
        end

        -- 说明：刷新当前队友的大防御和可驱散减益状态。
        -- 依赖事件更新：UNIT_AURA。
        -- 依赖定时刷新：2 秒。
        local function updateAura()
            if not unitExists then
                return
            end

            local bigDefenseTable = GetUnitAuraInstanceIDs(UNIT_KEY, "HELPFUL|BIG_DEFENSIVE") or {}
            local dispellableDebuffTable = GetUnitAuraInstanceIDs(UNIT_KEY, "HARMFUL|RAID_PLAYER_DISPELLABLE") or {}
            cell.hasBigDefense:setCellBoolean(#bigDefenseTable > 0, COLOR.STATUS_BOOLEAN.HAS_BIG_DEFENSE, COLOR.BLACK)
            cell.hasDispellableDebuff:setCellBoolean(
                #dispellableDebuffTable > 0,
                COLOR.STATUS_BOOLEAN.HAS_DISPELLABLE_DEBUFF,
                COLOR.BLACK
            )
        end

        -- 说明：整组刷新当前队友槽位的全部显示状态。
        -- 依赖事件更新：GROUP_*、PARTY_MEMBER_*、PLAYER_ROLES_ASSIGNED、UNIT_AURA、UNIT_HEALTH、UNIT_MAXHEALTH、UNIT_POWER_UPDATE、UNIT_MAXPOWER、UNIT_DISPLAYPOWER、UNIT_FLAGS、UNIT_FACTION、PLAYER_TARGET_CHANGED、UNIT_TARGETABLE_CHANGED。
        -- 依赖定时刷新：首次刷新；距离 0.5 秒，其余 2 秒。
        local function updateAll()
            updateUnitExists()
            updateClassAndRole()
            updateHealth()
            updatePower()
            updateUnitBasicStatus()
            updateRangeStatus()
            updateAura()
        end

        local GroupChangeOnFrame = false

        -- event 注册

        -- GROUP_ROSTER_UPDATE
        -- 事件说明：队伍成员变化时，当前 party 槽位可能整体换人，直接全刷。
        -- 对应函数：updateAll
        eventFrame:RegisterEvent("GROUP_ROSTER_UPDATE")
        function eventFrame:GROUP_ROSTER_UPDATE()
            if GroupChangeOnFrame then
                return
            end
            GroupChangeOnFrame = true
            updateAll()
        end

        -- GROUP_JOINED
        -- 事件说明：玩家加入队伍后，当前 party 槽位可能重排，直接全刷。
        -- 对应函数：updateAll
        eventFrame:RegisterEvent("GROUP_JOINED")
        function eventFrame:GROUP_JOINED()
            if GroupChangeOnFrame then
                return
            end
            GroupChangeOnFrame = true
            updateAll()
        end

        -- GROUP_LEFT
        -- 事件说明：玩家离队后，当前 party 槽位可能清空或前移，直接全刷。
        -- 对应函数：updateAll
        eventFrame:RegisterEvent("GROUP_LEFT")
        function eventFrame:GROUP_LEFT()
            if GroupChangeOnFrame then
                return
            end
            GroupChangeOnFrame = true
            updateAll()
        end

        -- GROUP_FORMED
        -- 事件说明：新队伍形成时，当前 party 槽位整体重建，直接全刷。
        -- 对应函数：updateAll
        eventFrame:RegisterEvent("GROUP_FORMED")
        function eventFrame:GROUP_FORMED()
            if GroupChangeOnFrame then
                return
            end
            GroupChangeOnFrame = true
            updateAll()
        end

        -- PLAYER_ROLES_ASSIGNED
        -- 事件说明：职责指派变化时刷新职业和职责显示。
        -- 对应函数：updateClassAndRole
        eventFrame:RegisterEvent("PLAYER_ROLES_ASSIGNED")
        function eventFrame:PLAYER_ROLES_ASSIGNED()
            updateClassAndRole()
        end

        -- PARTY_MEMBER_ENABLE
        -- 事件说明：某个队友重新上线或恢复可交互时刷新当前槽位。
        -- 对应函数：updateAll
        eventFrame:RegisterEvent("PARTY_MEMBER_ENABLE")
        function eventFrame:PARTY_MEMBER_ENABLE(unitToken)
            if unitToken == UNIT_KEY then
                updateAll()
            end
        end

        -- PARTY_MEMBER_DISABLE
        -- 事件说明：某个队友断线或失去可交互时刷新当前槽位。
        -- 对应函数：updateAll
        eventFrame:RegisterEvent("PARTY_MEMBER_DISABLE")
        function eventFrame:PARTY_MEMBER_DISABLE(unitToken)
            if unitToken == UNIT_KEY then
                updateAll()
            end
        end

        -- UNIT_AURA
        -- 事件说明：Aura 变化时刷新友方异常状态。
        -- 对应函数：updateAura
        eventFrame:RegisterUnitEvent("UNIT_AURA", UNIT_KEY)
        function eventFrame:UNIT_AURA(unitToken, info)
            if info.isFullUpdate or info.removedAuraInstanceIDs or info.addedAuras then
                updateAura()
            end
        end

        -- UNIT_MAXHEALTH
        -- 事件说明：最大生命值变化时刷新血量百分比。
        -- 对应函数：updateHealth
        eventFrame:RegisterUnitEvent("UNIT_MAXHEALTH", UNIT_KEY)
        function eventFrame:UNIT_MAXHEALTH(unitToken)
            updateHealth()
        end

        -- UNIT_HEALTH
        -- 事件说明：当前生命值变化时刷新血量百分比。
        -- 对应函数：updateHealth
        eventFrame:RegisterUnitEvent("UNIT_HEALTH", UNIT_KEY)
        function eventFrame:UNIT_HEALTH(unitToken)
            updateHealth()
        end

        -- UNIT_POWER_UPDATE
        -- 事件说明：能量变化时刷新能量百分比。
        -- 对应函数：updatePower
        eventFrame:RegisterUnitEvent("UNIT_POWER_UPDATE", UNIT_KEY)
        -- UNIT_MAXPOWER
        -- 事件说明：最大能量值变化时刷新能量百分比。
        -- 对应函数：updatePower
        eventFrame:RegisterUnitEvent("UNIT_MAXPOWER", UNIT_KEY)
        -- UNIT_DISPLAYPOWER
        -- 事件说明：能量制式变化时刷新能量百分比。
        -- 对应函数：updatePower
        eventFrame:RegisterUnitEvent("UNIT_DISPLAYPOWER", UNIT_KEY)
        function eventFrame:UNIT_POWER_UPDATE(unitToken)
            updatePower()
        end

        function eventFrame:UNIT_MAXPOWER(unitToken)
            updatePower()
        end

        function eventFrame:UNIT_DISPLAYPOWER(unitToken)
            updatePower()
        end

        -- UNIT_FLAGS
        -- 事件说明：队友旗标变化时刷新存在、基础状态和距离。
        -- 对应函数：updateUnitExists、updateUnitBasicStatus、updateRangeStatus
        eventFrame:RegisterUnitEvent("UNIT_FLAGS", UNIT_KEY)
        function eventFrame:UNIT_FLAGS(unitToken)
            updateUnitExists()
            updateUnitBasicStatus()
            updateRangeStatus()
        end

        -- UNIT_FACTION
        -- 事件说明：阵营可攻击性变化时刷新友敌和可攻击状态。
        -- 对应函数：updateUnitBasicStatus
        eventFrame:RegisterUnitEvent("UNIT_FACTION", UNIT_KEY)
        function eventFrame:UNIT_FACTION(unitToken)
            updateUnitBasicStatus()
        end

        -- PLAYER_TARGET_CHANGED
        -- 事件说明：当前目标变化时更新是否为目标，并顺手刷新一次距离。
        -- 对应函数：updateUnitBasicStatus、updateRangeStatus
        eventFrame:RegisterEvent("PLAYER_TARGET_CHANGED")
        function eventFrame:PLAYER_TARGET_CHANGED()
            updateUnitBasicStatus()
            updateRangeStatus()
        end

        -- UNIT_TARGETABLE_CHANGED
        -- 事件说明：可交互性变化时刷新存在、基础状态和距离。
        -- 对应函数：updateUnitExists、updateUnitBasicStatus、updateRangeStatus
        eventFrame:RegisterUnitEvent("UNIT_TARGETABLE_CHANGED", UNIT_KEY)
        function eventFrame:UNIT_TARGETABLE_CHANGED(unitToken)
            updateUnitExists()
            updateUnitBasicStatus()
            updateRangeStatus()
        end

        -- 路由

        -- local fastTimeElapsed = -random()     -- 当前未使用，保留 0.1 秒刷新档位结构
        local lowTimeElapsed = -random()      -- 随机初始时间，避免所有队友格子在同一帧中速刷新
        local superLowTimeElapsed = -random() -- 随机初始时间，避免所有队友格子在同一帧低频补正
        eventFrame:HookScript("OnUpdate", function(frame, elapsed)
            GroupChangeOnFrame = false        -- 每帧重置，避免同一帧内重复处理多个队伍结构事件
            -- fastTimeElapsed = fastTimeElapsed + elapsed
            -- if fastTimeElapsed > 0.1 then
            --     fastTimeElapsed = fastTimeElapsed - 0.1
            -- end
            lowTimeElapsed = lowTimeElapsed + elapsed
            if lowTimeElapsed > 0.5 then
                lowTimeElapsed = lowTimeElapsed - 0.5
                updateRangeStatus()
            end
            superLowTimeElapsed = superLowTimeElapsed + elapsed
            if superLowTimeElapsed > 2 then
                superLowTimeElapsed = superLowTimeElapsed - 2
                updateUnitExists()
                updateClassAndRole()
                updateHealth()
                updatePower()
                updateUnitBasicStatus()
                updateAura()
            end
        end)

        eventFrame:SetScript("OnEvent", function(self, event, ...)
            self[event](self, ...)
        end)

        -- 首次刷新
        updateAll()
    end
end
insert(MartixInitFuncs, InitFrame)
