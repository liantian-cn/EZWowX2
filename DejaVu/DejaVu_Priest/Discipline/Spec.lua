local addonName, addonTable             = ... -- luacheck: ignore addonName

-- Lua 原生函数
local insert                            = table.insert
local random                            = math.random

-- WoW 官方 API
local CreateFrame                       = CreateFrame
local UnitPower                         = UnitPower
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization
-- /dump C_SpellBook.IsSpellKnown(390632)
local IsSpellKnown                      = C_SpellBook.IsSpellKnown

-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "PRIEST" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是牧师则停止
if currentSpec ~= 1 then return end -- 不是戒律专精则停止

-- DejaVu Core
local DejaVu = _G["DejaVu"]
local Cell = DejaVu.Cell
local MartixInitFuncs = DejaVu.MartixInitFuncs


local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 事件框架

    local cells = {
        dispelAbilities = Cell:New(55, 13) -- 可否驱散疾病
    }

    local function updateDispelAbilities()
        cells.dispelAbilities:setCellBoolean(IsSpellKnown(390632), COLOR.WHITE, COLOR.BLACK)
    end
    eventFrame:RegisterEvent("SPELLS_CHANGED")
    function eventFrame.SPELLS_CHANGED()
        updateDispelAbilities()
    end

    updateDispelAbilities()

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        self[event](...)
    end)
end
insert(MartixInitFuncs, InitFrame)
