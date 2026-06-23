local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local random = math.random
local floor = math.floor
local min = math.min
local insert = table.insert

-- WoW 官方 API
local CreateFrame = CreateFrame
local GetTime = GetTime
local UnitAffectingCombat = UnitAffectingCombat

local DejaVu = _G["DejaVu"]
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs


local function InitFrame()
    local eventFrame = CreateFrame("Frame")

    -- x:56 y:9
    -- 用途：显示玩家脱战后累计的战斗时长。
    -- 更新函数：updateCell
    local cell = Cell:New(56, 9)
    local nonCombatTimestamp = GetTime()

    -- 说明：玩家在战斗中时显示累计战斗秒数，脱战时清空并重置计时。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.1 秒。
    local function updateCell()
        if UnitAffectingCombat("player") then
            local combatTime = min(255, floor(GetTime() - nonCombatTimestamp))
            cell:setCellRGBA(combatTime / 255)
        else
            nonCombatTimestamp = GetTime()
            cell:clearCell()
        end
    end

    -- 定时路由：每 0.1 秒刷新战斗计时。
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
