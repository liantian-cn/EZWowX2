local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local random = math.random
local insert = table.insert

-- WoW 官方 API
local UnitGetTotalAbsorbs = UnitGetTotalAbsorbs
local UnitGetTotalHealAbsorbs = UnitGetTotalHealAbsorbs
local UnitHealthMax = UnitHealthMax

local DejaVu = _G["DejaVu"]
local Bar = DejaVu.Bar
local MartixInitFuncs = DejaVu.MartixInitFuncs


local function InitFrame()
    for partyIndex = 1, 4 do
        -- eventFrame 构建
        local eventFrame = CreateFrame("Frame") -- 事件框架
        local UNIT_KEY = format("party%d", partyIndex)
        local BASE_X = 21 * partyIndex
        local unitExists = false

        -- cell 实例构建

        -- x:BASE_X - 20 y:24
        -- 用途：当前队友的伤害吸收条
        -- 更新函数：updateMaxHealth、updateDamageAbsorbs
        local damageAbsorbsBar = Bar:New(BASE_X - 20, 24, 10)
        -- x:BASE_X - 20 y:25
        -- 用途：当前队友的治疗吸收条
        -- 更新函数：updateMaxHealth、updateHealAbsorbs
        local healAbsorbsBar = Bar:New(BASE_X - 20, 25, 10)
        -- x:BASE_X - 20 y:24
        -- 用途：当前队友的即将收到治疗条
        -- 更新函数：updateMaxHealth、updateIncomingHeals
        -- local inCominngHealsBar = Bar:New(BASE_X - 20, 24, 10, true)

        -- update 函数构建

        -- 说明：刷新当前队友吸收条的刻度范围。
        -- 依赖事件更新：UNIT_MAXHEALTH。
        -- 依赖定时刷新：2 秒。
        local function updateMaxHealth()
            if not unitExists then
                damageAbsorbsBar:setMinMaxValues(0, 1)
                healAbsorbsBar:setMinMaxValues(0, 1)
                -- inCominngHealsBar:setMinMaxValues(0, 1)
                return
            end
            local maxHealth = UnitHealthMax(UNIT_KEY) or 0
            damageAbsorbsBar:setMinMaxValues(0, maxHealth / 2)
            healAbsorbsBar:setMinMaxValues(0, maxHealth / 2)
            -- inCominngHealsBar:setMinMaxValues(0, maxHealth / 2)
        end

        -- 说明：刷新当前队友的伤害吸收条数值。
        -- 依赖事件更新：UNIT_ABSORB_AMOUNT_CHANGED。
        -- 依赖定时刷新：2 秒。
        local function updateDamageAbsorbs()
            if unitExists then
                damageAbsorbsBar:setValue(UnitGetTotalAbsorbs(UNIT_KEY) or 0)
            else
                damageAbsorbsBar:setValue(0)
            end
        end

        -- 说明：刷新当前队友的治疗吸收条数值。
        -- 依赖事件更新：UNIT_HEAL_ABSORB_AMOUNT_CHANGED。
        -- 依赖定时刷新：2 秒。
        local function updateHealAbsorbs()
            if unitExists then
                healAbsorbsBar:setValue(UnitGetTotalHealAbsorbs(UNIT_KEY) or 0)
            else
                healAbsorbsBar:setValue(0)
            end
        end

        -- 说明：刷新当前队友槽位是否存在有效单位。
        -- 依赖事件更新：GROUP_*、PARTY_MEMBER_*。
        -- 依赖定时刷新：2 秒。
        local function updateUnitExists()
            unitExists = UnitExists(UNIT_KEY)
        end

        -- 说明：整组刷新当前队友槽位的吸收条状态。
        -- 依赖事件更新：GROUP_*、PARTY_MEMBER_*、UNIT_MAXHEALTH、UNIT_ABSORB_AMOUNT_CHANGED、UNIT_HEAL_ABSORB_AMOUNT_CHANGED。
        -- 依赖定时刷新：首次刷新；2 秒。
        local function updateAll()
            updateUnitExists()
            updateMaxHealth()
            updateDamageAbsorbs()
            updateHealAbsorbs()
            -- updateIncomingHeals()
        end

        -- 说明：刷新当前队友的即将收到治疗条数值。
        -- 依赖事件更新：UNIT_HEAL_PREDICTION。
        -- 依赖定时刷新：2 秒。
        -- local function updateIncomingHeals()
        --     inCominngHealsBar:setValue(UnitGetIncomingHeals(UNIT_KEY) or 0)
        -- end

        -- event 注册

        -- UNIT_MAXHEALTH
        -- 事件说明：最大生命值变化时同步刻度，并顺手重刷两条吸收条。
        -- 对应函数：updateMaxHealth、updateDamageAbsorbs、updateHealAbsorbs
        eventFrame:RegisterUnitEvent("UNIT_MAXHEALTH", UNIT_KEY)
        function eventFrame:UNIT_MAXHEALTH(unitToken)
            updateMaxHealth()
            updateDamageAbsorbs()
            updateHealAbsorbs()
        end

        -- UNIT_ABSORB_AMOUNT_CHANGED
        -- 事件说明：伤害吸收变化时只刷新伤害吸收条。
        -- 对应函数：updateDamageAbsorbs
        eventFrame:RegisterUnitEvent("UNIT_ABSORB_AMOUNT_CHANGED", UNIT_KEY)
        function eventFrame:UNIT_ABSORB_AMOUNT_CHANGED(unitToken)
            updateDamageAbsorbs()
        end

        -- UNIT_HEAL_ABSORB_AMOUNT_CHANGED
        -- 事件说明：治疗吸收变化时只刷新治疗吸收条。
        -- 对应函数：updateHealAbsorbs
        eventFrame:RegisterUnitEvent("UNIT_HEAL_ABSORB_AMOUNT_CHANGED", UNIT_KEY)
        function eventFrame:UNIT_HEAL_ABSORB_AMOUNT_CHANGED(unitToken)
            updateHealAbsorbs()
        end

        -- UNIT_HEAL_PREDICTION
        -- 事件说明：即将收到的治疗更新时只刷新即将收到的治疗条。
        -- 对应函数：updateIncomingHeals
        -- function eventFrame:UNIT_HEAL_PREDICTION(unitToken)
        --     updateIncomingHeals()
        -- end

        -- eventFrame:RegisterUnitEvent("UNIT_HEAL_PREDICTION", UNIT_KEY)

        local GroupChangeOnFrame = false

        -- GROUP_ROSTER_UPDATE
        -- 事件说明：队伍成员变化时对应的 party 槽位可能整体换人，直接全刷。
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
        -- 事件说明：玩家加入队伍后，party 槽位重新分配，直接全刷。
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
        -- 事件说明：玩家离队后，party 槽位可能清空或前移，直接全刷。
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
        -- 事件说明：新队伍形成时，party 槽位整体重建，直接全刷。
        -- 对应函数：updateAll
        eventFrame:RegisterEvent("GROUP_FORMED")
        function eventFrame:GROUP_FORMED()
            if GroupChangeOnFrame then
                return
            end
            GroupChangeOnFrame = true
            updateAll()
        end

        -- PARTY_MEMBER_ENABLE
        -- 事件说明：某个队友重新上线、进出可交互状态时刷新当前槽位。
        -- 对应函数：updateAll
        eventFrame:RegisterEvent("PARTY_MEMBER_ENABLE")
        function eventFrame:PARTY_MEMBER_ENABLE(unitToken)
            if unitToken == UNIT_KEY then
                updateAll()
            end
        end

        -- PARTY_MEMBER_DISABLE
        -- 事件说明：某个队友断线、离开可交互状态时刷新当前槽位。
        -- 对应函数：updateAll
        eventFrame:RegisterEvent("PARTY_MEMBER_DISABLE")
        function eventFrame:PARTY_MEMBER_DISABLE(unitToken)
            if unitToken == UNIT_KEY then
                updateAll()
            end
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
                updateAll()
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
end
insert(MartixInitFuncs, InitFrame)
