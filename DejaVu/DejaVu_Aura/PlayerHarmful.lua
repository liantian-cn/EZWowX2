local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local random                = math.random
local insert                = table.insert
local CreateFrame           = CreateFrame

-- 插件内引用
local CreateAuraController  = addonTable.CreateAuraController

local MAX_AURA_COUNT        = 10
local BASE_X                = 1
local BASE_Y                = 9
local UNIT_KEY              = "player"
-- local AURA_FILTER = "HARMFUL"
local AURA_FILTER           = "HARMFUL"
local SORT_RULE             = Enum.UnitAuraSortRule.Default
local SORT_DIRECTION        = Enum.UnitAuraSortDirection.Normal
local DejaVu                = _G["DejaVu"]
local MartixInitFuncs       = DejaVu.MartixInitFuncs


local function InitFrame()
    -- 先构建 eventFrame
    local eventFrame = CreateFrame("Frame")

    -- 构建 aura 控制器
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

    -- 构建 update 函数
    -- 说明：处理玩家 Harmful Aura 的结构变化，必要时全量刷新整组槽位。
    -- 依赖事件更新：UNIT_AURA。
    -- 依赖定时刷新：无。
    local function updateHarmfulAuras(info)
        if info.isFullUpdate then
            controller.refreshAll()
            return
        end
        if info.removedAuraInstanceIDs then
            -- for _, instanceID in ipairs(info.removedAuraInstanceIDs) do
            --     controller.removeAura(instanceID)
            -- end
            controller.refreshAll() -- 临时代替，等12.0.5修正API后再改回来
            return                  -- 因为完全刷新了，所以return就行了
        end
        if info.addedAuras then
            -- for _, aura in ipairs(info.addedAuras) do
            --     controller.addAura(aura.auraInstanceID)
            -- end
            controller.refreshAll() -- 临时代替，等12.0.5修正API后再改回来
            return                  -- 因为完全刷新了，所以return就行了
        end
        if info.updatedAuraInstanceIDs then
            -- for _, instanceID in ipairs(info.updatedAuraInstanceIDs) do
            --     controller.updateRemaining(instanceID)
            -- end
            -- 暂时什么都不用做 临时代替，等12.0.5修正API后再改回来
            return -- 因为完全刷新了，所以return就行了
        end
    end

    -- 说明：批量更新时间相关显示，不重排 aura 结构。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.1 秒。
    local function updateHarmfulAuraRemaining()
        controller.updateRemainingAll()
    end

    -- 事件注册和事件函数
    -- UNIT_AURA
    -- 事件说明：玩家减益结构变化时刷新玩家 Harmful Aura 列表。
    -- 对应函数：updateHarmfulAuras
    eventFrame:RegisterUnitEvent("UNIT_AURA", UNIT_KEY)
    function eventFrame.UNIT_AURA(unitTarget, updateInfo)
        updateHarmfulAuras(updateInfo)
    end

    -- 路由
    local fastTimeElapsed = -random() -- 随机初始时间，避免所有事件在同一帧更新
    -- local lowTimeElapsed = -random()      -- 当前未使用，保留 0.5 秒刷新档位结构
    -- local superLowTimeElapsed = -random() -- 当前未使用，保留 2 秒刷新档位结构
    eventFrame:HookScript("OnUpdate", function(_, elapsed)
        fastTimeElapsed = fastTimeElapsed + elapsed
        if fastTimeElapsed > 0.1 then
            fastTimeElapsed = fastTimeElapsed - 0.1
            updateHarmfulAuraRemaining()
        end
        -- lowTimeElapsed = lowTimeElapsed + elapsed
        -- if lowTimeElapsed > 0.5 then
        --     lowTimeElapsed = lowTimeElapsed - 0.5
        -- end
        -- superLowTimeElapsed = superLowTimeElapsed + elapsed
        -- if superLowTimeElapsed > 2 then
        --     superLowTimeElapsed = superLowTimeElapsed - 2
        --     controller.refreshAll()
        -- end
    end)

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        self[event](...)
    end)

    -- 首次刷新
    controller.refreshAll()
end
insert(MartixInitFuncs, InitFrame)
