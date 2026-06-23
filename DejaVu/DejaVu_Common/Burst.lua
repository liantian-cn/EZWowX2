local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local random = math.random
local insert = table.insert

-- WoW 官方 API
local CreateFrame = CreateFrame

local DejaVu = _G["DejaVu"]
-- local Config = DejaVu.Config
-- local ConfigRows = DejaVu.ConfigRows
-- local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell
local BurstRemaining = DejaVu.BurstRemaining
local MartixInitFuncs = DejaVu.MartixInitFuncs

local function InitFrame()
    local eventFrame = CreateFrame("Frame")

    -- x:82 y:0
    -- 用途：显示爆发剩余时间强度。
    -- 更新函数：updateCell
    local cell = Cell:New(82, 0)

    -- 说明：按 BurstRemaining 的剩余时间比例刷新爆发显示。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.5 秒。
    local function updateCell()
        local burstRemaining = BurstRemaining()
        burstRemaining = min(51, burstRemaining) -- 确保剩余时间不超过显示上限。
        cell:setCellRGBA(burstRemaining / 51)
    end

    -- 定时路由：每 0.5 秒刷新一次爆发剩余时间。
    -- local fastTimeElapsed = -random() -- 当前未使用，保留 0.1 秒刷新档位结构。
    local lowTimeElapsed = -random()
    -- local superLowTimeElapsed = -random() -- 当前未使用，保留 2 秒刷新档位结构。
    eventFrame:HookScript("OnUpdate", function(_, elapsed)
        -- fastTimeElapsed = fastTimeElapsed + elapsed
        -- if fastTimeElapsed > 0.1 then
        --     fastTimeElapsed = fastTimeElapsed - 0.1
        -- end
        lowTimeElapsed = lowTimeElapsed + elapsed
        if lowTimeElapsed > 0.5 then
            lowTimeElapsed = lowTimeElapsed - 0.5
            updateCell()
        end
        -- superLowTimeElapsed = superLowTimeElapsed + elapsed
        -- if superLowTimeElapsed > 2 then
        --     superLowTimeElapsed = superLowTimeElapsed - 2
        --     controller.refreshAll()
        -- end
    end)

    -- 首次刷新
    updateCell()
end
insert(MartixInitFuncs, InitFrame)
