local addonName, addonTable             = ... 

-- Lua 原生函数
local random                            = math.random
local insert                            = table.insert

-- WoW 官方 API
local CreateFrame                       = CreateFrame
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization
-- 新增需要的 API 引用
local GetPlayerAuraBySpellID            = C_UnitAuras.GetPlayerAuraBySpellID
local IsSpellKnown                      = C_SpellBook.IsSpellKnown

-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "DEMONHUNTER" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是恶魔猎手则停止
if currentSpec ~= 3 then return end -- 不是噬灭专精则停止

-- DejaVu Core
local DejaVu = _G["DejaVu"]
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs

local function InitFrame()
    local eventFrame = CreateFrame("Frame")

    local cells = {
        -- x:55 y:13
        -- 用途：显示恶魔猎手当前灵魂碎片数量
        SoulFragments = Cell:New(55, 13)
    }

    -- 说明：参考 SecondaryResourceBar.lua 的逻辑获取碎片层数
    local function UpdateSoulFragments()
        -- 1. 检测碎片 Buff (ID: 1225789 或 1227702)
        local auraData = GetPlayerAuraBySpellID(1225789) or GetPlayerAuraBySpellID(1227702)
        local current_soul = auraData and auraData.applications or 0
        
        -- -- 2. 获取当前天赋下的最大上限 (35 或 50)
        -- local max = IsSpellKnown(1247534) and 35 or 50
        
        -- 3. 将数值映射到单元格
        -- 这里的计算公式取决于你外部程序识别的精度，通常建议 (当前值/最大值)*255
        -- 或者直接按比例输出，如 current_soul * 5 / 255
        cells.SoulFragments:setCellRGBA(current_soul * 5 / 255)
    end

    local fastTimeElapsed = -random()  -- 0.1 秒刷新可用灵魂碎片数量
    eventFrame:HookScript("OnUpdate", function(frame, elapsed)
        fastTimeElapsed = fastTimeElapsed + elapsed
        if fastTimeElapsed > 0.1 then
            fastTimeElapsed = fastTimeElapsed - 0.1
            UpdateSoulFragments()
        end
    end)
end
insert(MartixInitFuncs, InitFrame)
