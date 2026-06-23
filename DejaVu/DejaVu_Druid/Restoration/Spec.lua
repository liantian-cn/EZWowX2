local addonName, addonTable             = ... -- luacheck: ignore addonName

-- Lua 原生函数
local insert                            = table.insert
local random                            = math.random

-- WoW 官方 API
local CreateFrame                       = CreateFrame
local UnitPower                         = UnitPower
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization

-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "DRUID" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是德鲁伊则停止
if currentSpec ~= 4 then return end -- 不是恢复专精则停止

-- DejaVu Core
local DejaVu = _G["DejaVu"]
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs


local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 事件框架

    local cells = {
        -- x:55 y:13
        -- 用途：显示恢复德鲁伊的连击点数量。
        -- 更新函数：UpdateComboPoints
        ComboPoints = Cell:New(55, 13)
    }

    -- 说明：更新恢复德鲁伊当前的连击点显示。
    -- 依赖事件更新：无
    -- 依赖定时刷新：0.1 秒
    local function UpdateComboPoints()
        local power = UnitPower("player", Enum.PowerType.ComboPoints)
        local mean = power * 51 / 255
        cells.ComboPoints:setCellRGBA(mean)
    end

    local fastTimeElapsed = -random()                          -- 0.1 秒刷新连击点数量
    eventFrame:HookScript("OnUpdate", function(frame, elapsed) -- luacheck: ignore frame
        fastTimeElapsed = fastTimeElapsed + elapsed
        if fastTimeElapsed > 0.1 then
            fastTimeElapsed = fastTimeElapsed - 0.1
            UpdateComboPoints()
        end
    end)
end
insert(MartixInitFuncs, InitFrame)
