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
    local eventFrame = CreateFrame("Frame") -- 事件框架

    -- x:43 y:16
    -- 用途：玩家的伤害吸收条。
    -- 更新函数：updateMaxHealth、updateDamageAbsorbs
    local damageAbsorbsBar = Bar:New(43, 16, 20)
    -- x:64 y:14
    -- 用途：玩家的治疗吸收条。
    -- 更新函数：updateMaxHealth、updateHealAbsorbs
    local healAbsorbsBar = Bar:New(64, 14, 20)
    -- x:43 y:16
    -- 用途：玩家的即将收到治疗条。
    -- 更新函数：updateMaxHealth、updateIncomingHeals
    -- local inCominngHealsBar = Bar:New(43, 16, 20, true)

    -- 说明：刷新玩家两条吸收条的刻度范围。
    -- 依赖事件更新：UNIT_MAXHEALTH。
    -- 依赖定时刷新：2 秒。
    local function updateMaxHealth()
        local maxHealth = UnitHealthMax("player") or 0
        damageAbsorbsBar:setMinMaxValues(0, maxHealth)
        healAbsorbsBar:setMinMaxValues(0, maxHealth)
        -- inCominngHealsBar:setMinMaxValues(0, maxHealth)
    end

    -- 说明：刷新玩家的伤害吸收条数值。
    -- 依赖事件更新：UNIT_ABSORB_AMOUNT_CHANGED。
    -- 依赖定时刷新：2 秒。
    local function updateDamageAbsorbs()
        damageAbsorbsBar:setValue(UnitGetTotalAbsorbs("player") or 0)
    end

    -- 说明：刷新玩家的治疗吸收条数值。
    -- 依赖事件更新：UNIT_HEAL_ABSORB_AMOUNT_CHANGED。
    -- 依赖定时刷新：2 秒。
    local function updateHealAbsorbs()
        healAbsorbsBar:setValue(UnitGetTotalHealAbsorbs("player") or 0)
    end

    -- UNIT_MAXHEALTH
    -- 事件说明：最大生命值变化时同步刻度，并顺手重刷两条吸收条。
    -- 对应函数：updateMaxHealth、updateDamageAbsorbs、updateHealAbsorbs
    eventFrame:RegisterUnitEvent("UNIT_MAXHEALTH", "player")

    function eventFrame:UNIT_MAXHEALTH(unitToken)
        updateMaxHealth()
        updateDamageAbsorbs()
        updateHealAbsorbs()
    end

    -- UNIT_ABSORB_AMOUNT_CHANGED
    -- 事件说明：伤害吸收变化时只刷新伤害吸收条。
    -- 对应函数：updateDamageAbsorbs
    eventFrame:RegisterUnitEvent("UNIT_ABSORB_AMOUNT_CHANGED", "player")

    function eventFrame:UNIT_ABSORB_AMOUNT_CHANGED(unitToken)
        updateDamageAbsorbs()
    end

    -- UNIT_HEAL_ABSORB_AMOUNT_CHANGED
    -- 事件说明：治疗吸收变化时只刷新治疗吸收条。
    -- 对应函数：updateHealAbsorbs
    eventFrame:RegisterUnitEvent("UNIT_HEAL_ABSORB_AMOUNT_CHANGED", "player")

    function eventFrame:UNIT_HEAL_ABSORB_AMOUNT_CHANGED(unitToken)
        updateHealAbsorbs()
    end

    -- 说明：刷新玩家即将收到的治疗条数值。
    -- 依赖事件更新：UNIT_HEAL_PREDICTION。
    -- 依赖定时刷新：2 秒。
    -- local function updateIncomingHeals()
    --     inCominngHealsBar:setValue(UnitGetIncomingHeals("player") or 0)
    -- end

    -- UNIT_HEAL_PREDICTION
    -- 事件说明：即将收到的治疗变化时刷新即将收到的治疗条。
    -- 对应函数：updateIncomingHeals
    -- function eventFrame:UNIT_HEAL_PREDICTION(unitToken)
    --     updateIncomingHeals()
    -- end

    -- UNIT_HEAL_PREDICTION
    -- 事件说明：注册即将收到的治疗事件，当前保持禁用。
    -- 对应函数：updateIncomingHeals
    -- eventFrame:RegisterUnitEvent("UNIT_HEAL_PREDICTION", "player")

    -- local fastTimeElapsed = -random()     -- 当前未使用，保留 0.1 秒刷新档位结构
    -- local lowTimeElapsed = -random()      -- 当前未使用，保留 0.5 秒刷新档位结构
    local superLowTimeElapsed = -random() -- 随机初始时间，避免所有事件在同一帧更新
    eventFrame:HookScript("OnUpdate", function(frame, elapsed)
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
            updateMaxHealth()
            updateDamageAbsorbs()
            updateHealAbsorbs()
            -- updateIncomingHeals()
        end
    end)

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        self[event](self, ...)
    end)

    -- 首次刷新
    updateMaxHealth()
    updateDamageAbsorbs()
    updateHealAbsorbs()
    -- updateIncomingHeals()
end
insert(MartixInitFuncs, InitFrame)
