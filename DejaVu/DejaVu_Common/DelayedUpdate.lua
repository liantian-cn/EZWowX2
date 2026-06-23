local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local tonumber = tonumber
local After = C_Timer.After
local random = math.random
local insert = table.insert

-- WoW 官方 API
local CreateFrame = CreateFrame
local GetTime = GetTime
local SlashCmdList = SlashCmdList

local DejaVu = _G["DejaVu"]
local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs


local function InitFrame()
    local eventFrame = CreateFrame("Frame")

    -- x:55 y:9
    -- 用途：显示延迟更新等待状态。
    -- 更新函数：updateCell
    local cell = Cell:New(55, 9)
    local delayTimestamp = GetTime()

    -- 说明：根据当前延迟截止时间刷新等待状态。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.1 秒。
    local function updateCell()
        cell:setCellBoolean(
            delayTimestamp > GetTime(),
            COLOR.STATUS_BOOLEAN.IS_WAITING_DELAYED_UPDATE,
            COLOR.BLACK
        )
    end

    -- 说明：处理 /delay 命令并更新延迟截止时间。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：无。
    _G.SLASH_DELAY1 = "/delay"
    SlashCmdList["DELAY"] = function(msg)
        local delaySeconds = tonumber(msg)
        if delaySeconds then
            delayTimestamp = GetTime() + delaySeconds
            updateCell()
        end
    end

    -- 定时路由：每 0.1 秒刷新延迟等待状态。
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
        --     updateCell()
        -- end
    end)

    -- 首次刷新
    updateCell()
end
insert(MartixInitFuncs, InitFrame)
