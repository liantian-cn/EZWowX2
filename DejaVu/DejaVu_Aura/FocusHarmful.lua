local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local random                = math.random
local insert                = table.insert
local CreateFrame           = CreateFrame

-- 插件内引用
local CreateAuraController  = addonTable.CreateAuraController

local MAX_AURA_COUNT        = 10
local BASE_X                = 1
local BASE_Y                = 14
local UNIT_KEY              = "focus"
local AURA_FILTER           = "HARMFUL|PLAYER"
local SORT_RULE             = Enum.UnitAuraSortRule.Default
local SORT_DIRECTION        = Enum.UnitAuraSortDirection.Normal

local DejaVu                = _G["DejaVu"]
local MartixInitFuncs       = DejaVu.MartixInitFuncs

local function InitFrame()
    local eventFrame = CreateFrame("Frame")
    local controller = CreateAuraController({
        unitKey = UNIT_KEY,
        auraFilter = AURA_FILTER,
        maxAuraCount = MAX_AURA_COUNT,
        baseX = BASE_X,
        baseY = BASE_Y,
        sortRule = SORT_RULE,
        sortDirection = SORT_DIRECTION,
        colorMode = "Harmful",
    })

    -- 说明：全量刷新 focus 的减益显示。
    -- 依赖事件更新：UNIT_AURA、PLAYER_FOCUS_CHANGED、UNIT_FLAGS。
    -- 依赖定时刷新：无。
    local function refreshAll()
        controller.refreshAll()
    end

    -- 说明：更新 focus 所有减益的剩余时间文本。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.1 秒。
    local function updateRemainingAll()
        controller.updateRemainingAll()
    end

    -- UNIT_AURA
    -- 事件说明：focus 的 Aura 列表变化时，按当前 API 限制刷新减益显示。
    -- 对应函数：refreshAll
    eventFrame:RegisterUnitEvent("UNIT_AURA", UNIT_KEY)
    function eventFrame:UNIT_AURA(unitToken, info)
        -- 因为无法判断 isHarmful 还是 isHelpful，所以只能全量刷新。这个问题在 12.0.5 修正。等那时补回来。
        if info.isFullUpdate then
            refreshAll()
            return
        end
        if info.removedAuraInstanceIDs then
            -- for _, instanceID in ipairs(info.removedAuraInstanceIDs) do
            --     controller.removeAura(instanceID)
            -- end
            refreshAll() -- 临时代替，等 12.0.5 修正 API 后再改回。
            return       -- 因为完全刷新了，所以 return 就行了。
        end
        if info.addedAuras then
            -- for _, aura in ipairs(info.addedAuras) do
            --     controller.addAura(aura.auraInstanceID)
            -- end
            refreshAll() -- 临时代替，等 12.0.5 修正 API 后再改回。
            return       -- 因为完全刷新了，所以 return 就行了。
        end
        if info.updatedAuraInstanceIDs then
            -- for _, instanceID in ipairs(info.updatedAuraInstanceIDs) do
            --     controller.updateRemaining(instanceID)
            -- end
            -- 暂时什么都不用做，等 12.0.5 修正 API 后再改回来。
            return -- 因为完全刷新了，所以 return 就行了。
        end
    end

    -- PLAYER_FOCUS_CHANGED
    -- 事件说明：切换 focus 时刷新整组减益显示。
    -- 对应函数：refreshAll
    eventFrame:RegisterEvent("PLAYER_FOCUS_CHANGED")
    function eventFrame:PLAYER_FOCUS_CHANGED()
        refreshAll()
    end

    -- UNIT_FLAGS
    -- 事件说明：focus 标记状态变化时刷新整组减益显示。
    -- 对应函数：refreshAll
    eventFrame:RegisterUnitEvent("UNIT_FLAGS", UNIT_KEY)
    function eventFrame:UNIT_FLAGS(unitToken)
        refreshAll()
    end

    local fastTimeElapsed = -random() -- 随机初始时间，避免所有事件在同一帧更新。
    -- local lowTimeElapsed = -random()      -- 当前未使用，保留 0.5 秒刷新档位结构。
    -- local superLowTimeElapsed = -random() -- 当前未使用，保留 2 秒刷新档位结构。
    eventFrame:HookScript("OnUpdate", function(frame, elapsed)
        fastTimeElapsed = fastTimeElapsed + elapsed
        if fastTimeElapsed > 0.1 then
            fastTimeElapsed = fastTimeElapsed - 0.1
            updateRemainingAll()
        end
        -- lowTimeElapsed = lowTimeElapsed + elapsed
        -- if lowTimeElapsed > 0.5 then
        --     lowTimeElapsed = lowTimeElapsed - 0.5
        -- end
        -- superLowTimeElapsed = superLowTimeElapsed + elapsed
        -- if superLowTimeElapsed > 2 then
        --     superLowTimeElapsed = superLowTimeElapsed - 2
        --     refreshAll()
        -- end
    end)

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        self[event](self, ...)
    end)

    refreshAll()
end
insert(MartixInitFuncs, InitFrame)
