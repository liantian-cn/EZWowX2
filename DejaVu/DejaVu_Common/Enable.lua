local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local random = math.random
local insert = table.insert

-- WoW 官方 API
local CreateFrame = CreateFrame

local DejaVu = _G["DejaVu"]
-- local Config = DejaVu.Config
-- local ConfigRows = DejaVu.ConfigRows
local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell
-- local BurstRemaining = DejaVu.BurstRemaining
local MartixInitFuncs = DejaVu.MartixInitFuncs


local function InitFrame()
    local eventFrame = CreateFrame("Frame")

    -- x:83 y:0
    -- 用途：显示 DejaVu 全局启用状态。
    -- 更新函数：updateCell
    local cell = Cell:New(83, 0)

    -- 说明：根据 DejaVu.Enable 刷新全局开关显示。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.1 秒。
    local function updateCell()
        cell:setCellBoolean(DejaVu.Enable == true, COLOR.GREEN, COLOR.BLACK)
    end

    -- 定时路由：每 0.1 秒轮询全局启用状态。
    local fastTimeElapsed = -random()
    -- local lowTimeElapsed = -random() -- 当前未使用，保留 0.5 秒刷新档位结构。
    -- local superLowTimeElapsed = -random() -- 当前未使用，保留 2 秒刷新档位结构。
    eventFrame:HookScript("OnUpdate", function(_, elapsed)
        fastTimeElapsed = fastTimeElapsed + elapsed
        if fastTimeElapsed > 0.1 then
            fastTimeElapsed = fastTimeElapsed - 0.1
            updateCell()
        end
        -- lowTimeElapsed = lowTimeElapsed + elapsed
        -- if lowTimeElapsed > 0.5 then
        --     lowTimeElapsed = lowTimeElapsed - 0.5
        --     updateCell()
        -- end
        -- superLowTimeElapsed = superLowTimeElapsed + elapsed
        -- if superLowTimeElapsed > 2 then
        --     superLowTimeElapsed = superLowTimeElapsed - 2
        --     controller.refreshAll()
        -- end
    end)
end
insert(MartixInitFuncs, InitFrame)
