local addonName, addonTable             = ... -- luacheck: ignore addonName

-- Lua 原生函数
local After                             = C_Timer.After
local random                            = math.random
local insert                            = table.insert -- 表插入

-- WoW 官方 API
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
DejaVu.RangedRange = 40 -- 默认的远程检测范围
DejaVu.MeleeRange = 5   -- 默认的近战检测范围
