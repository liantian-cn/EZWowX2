local addonName, addonTable             = ... -- luacheck: ignore addonName

-- Lua 原生函数
local After                             = C_Timer.After
local random                            = math.random
local insert                            = table.insert

-- WoW 官方 API
local CreateFrame                       = CreateFrame
local GetRuneCooldown                   = GetRuneCooldown
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization

-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "DEATHKNIGHT" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是死亡骑士则停止
if currentSpec ~= 1 then return end -- 不是鲜血专精则停止

-- DejaVu Core
local DejaVu = _G["DejaVu"]
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs


local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 事件框架

    local cells = {
        -- x:55 y:13
        -- 用途：显示鲜血死亡骑士当前可用符文数量。
        -- 更新函数：UpdateReadyRunes
        ReadyRunes = Cell:New(55, 13)
    }

    -- 说明：更新鲜血死亡骑士当前可用符文数量。
    -- 依赖事件更新：无
    -- 依赖定时刷新：0.1 秒
    local function UpdateReadyRunes()
        local readyRunes = 0
        for runeIndex = 1, 6 do
            local startTime, duration, runeReady = GetRuneCooldown(runeIndex) -- luacheck: ignore startTime duration
            if runeReady then
                readyRunes = readyRunes + 1
            end
        end
        cells.ReadyRunes:setCellRGBA(readyRunes * 10 / 255)
    end

    local fastTimeElapsed = -random()                          -- 0.1 秒刷新可用符文数量
    eventFrame:HookScript("OnUpdate", function(frame, elapsed) -- luacheck: ignore frame
        fastTimeElapsed = fastTimeElapsed + elapsed
        if fastTimeElapsed > 0.1 then
            fastTimeElapsed = fastTimeElapsed - 0.1
            UpdateReadyRunes()
        end
    end)
end
insert(MartixInitFuncs, InitFrame)
