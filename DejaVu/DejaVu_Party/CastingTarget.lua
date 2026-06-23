local addonName, addonTable = ... -- luacheck: ignore addonName -- 插件入口固定写法

-- Lua 原生函数
local pairs = pairs
local random = math.random
local insert = table.insert

-- WoW 官方 API
local UnitName = UnitName
local issecretvalue = issecretvalue
local CreateFrame = CreateFrame
local UnitExists = UnitExists


local DejaVu = _G["DejaVu"]
local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell


local party_members = {
    "player",
    "party1",
    "party2",
    "party3",
    "party4",
}
local MartixInitFuncs = DejaVu.MartixInitFuncs


local function InitFrame()
    -- eventFrame 构建
    local eventFrame = CreateFrame("Frame") -- 事件框架

    -- cell 实例构建
    local cell = {
        -- x:61 y:14
        -- 用途：玩家自身被施法点名的显示状态
        -- 更新函数：updateCastingTarget、updateClearCastingTarget、updateAll
        player = Cell:New(61, 14),
        -- x:19 y:24
        -- 用途：party1 被施法点名的显示状态
        -- 更新函数：updateCastingTarget、updateClearCastingTarget、updateAll
        party1 = Cell:New(19, 24),
        -- x:40 y:24
        -- 用途：party2 被施法点名的显示状态
        -- 更新函数：updateCastingTarget、updateClearCastingTarget、updateAll
        party2 = Cell:New(40, 24),
        -- x:61 y:24
        -- 用途：party3 被施法点名的显示状态
        -- 更新函数：updateCastingTarget、updateClearCastingTarget、updateAll
        party3 = Cell:New(61, 24),
        -- x:82 y:24
        -- 用途：party4 被施法点名的显示状态
        -- 更新函数：updateCastingTarget、updateClearCastingTarget、updateAll
        party4 = Cell:New(82, 24),
    }

    local currentCastingTarget = nil

    -- update 函数构建

    -- 说明：按照当前施法目标刷新点名显示，高亮目标并清空其他格子。
    -- 依赖事件更新：UNIT_SPELLCAST_SENT。
    -- 依赖定时刷新：无。
    local function updateCastingTarget(unitToken)
        for k, c in pairs(cell) do
            if k == unitToken then
                c:setCell(COLOR.GREEN)
            else
                c:setCell(COLOR.BLACK)
            end
        end
    end

    -- 说明：清空指定施法目标对应的点名显示。
    -- 依赖事件更新：UNIT_SPELLCAST_INTERRUPTED、UNIT_SPELLCAST_STOP。
    -- 依赖定时刷新：无。
    local function updateClearCastingTarget(unitToken)
        if not unitToken or not cell[unitToken] then
            return
        end

        cell[unitToken]:setCell(COLOR.BLACK)
    end

    -- 说明：首刷时清空全部点名格子，并在有记录目标时恢复显示。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：首次刷新。
    local function updateAll()
        for _, c in pairs(cell) do
            c:setCell(COLOR.BLACK)
        end

        if currentCastingTarget then
            updateCastingTarget(currentCastingTarget)
        end
    end

    -- event 注册

    -- UNIT_SPELLCAST_SENT
    -- 事件说明：玩家开始施法并发送目标名时，记录并刷新被点名队友槽位。
    -- 对应函数：updateCastingTarget
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SENT", "player")
    function eventFrame:UNIT_SPELLCAST_SENT(unitTarget, targetName, castGUID, spellID)
        if not issecretvalue(targetName) then
            for _, partyUnit in pairs(party_members) do
                if UnitExists(partyUnit) and (UnitName(partyUnit) == targetName) then
                    currentCastingTarget = partyUnit
                    -- print("当前施法目标:", partyUnit, targetName)
                    updateCastingTarget(partyUnit)
                    break
                end
            end
            -- print(state.castTargetUnit, state.castTargetName, state.castTargetIndex)
        end
    end

    -- UNIT_SPELLCAST_INTERRUPTED
    -- 事件说明：玩家施法被打断时，清空当前点名队友槽位。
    -- 对应函数：updateClearCastingTarget
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTED", "player")
    function eventFrame:UNIT_SPELLCAST_INTERRUPTED()
        updateClearCastingTarget(currentCastingTarget)
        currentCastingTarget = nil
        -- print("施法被打断，清除施法目标")
    end

    -- UNIT_SPELLCAST_STOP
    -- 事件说明：玩家施法自然结束时，清空当前点名队友槽位。
    -- 对应函数：updateClearCastingTarget
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_STOP", "player")
    function eventFrame:UNIT_SPELLCAST_STOP()
        updateClearCastingTarget(currentCastingTarget)
        currentCastingTarget = nil
        -- print("施法结束，清除施法目标")
    end

    -- 路由

    -- local fastTimeElapsed = -random()     -- 当前未使用，保留 0.1 秒刷新档位结构
    -- local lowTimeElapsed = -random()      -- 当前未使用，保留 0.5 秒刷新档位结构
    local superLowTimeElapsed = -random() -- 随机初始时间，避免所有事件在同一帧更新
    eventFrame:HookScript("OnUpdate", function(frame, elapsed)
        GroupChangeOnFrame = false        -- 每帧重置触发器状态，确保状态更新函数在同一帧内只执行一次

        -- fastTimeElapsed = fastTimeElapsed + elapsed
        -- if fastTimeElapsed > 0.1 then
        --     fastTimeElapsed = fastTimeElapsed - 0.1
        -- end
        -- lowTimeElapsed = lowTimeElapsed + elapsed
        -- if lowTimeElapsed > 0.5 then
        --     lowTimeElapsed = lowTimeElapsed - 0.5
        -- end
        superLowTimeElapsed = superLowTimeElapsed + elapsed
        if superLowTimeElapsed > 2 then
            superLowTimeElapsed = superLowTimeElapsed - 2
            -- updateMaxHealth()
            -- updateDamageAbsorbs()
            -- updateHealAbsorbs()
        end
    end)

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        self[event](self, ...)
    end)

    -- 首次刷新
    updateAll()
end
insert(MartixInitFuncs, InitFrame)
