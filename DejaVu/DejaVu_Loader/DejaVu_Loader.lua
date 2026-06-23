local addonName, addonTable = ... -- 插件入口固定写法
-- luacheck: ignore addonTable

-- Lua 原生函数
local format = string.format
local tostring = tostring

-- 官方 API
local DisableAddOn = C_AddOns.DisableAddOn
local LoadAddOn = C_AddOns.LoadAddOn
local UnitClass = UnitClass
local StaticPopup_Show = _G.StaticPopup_Show
local UnitName = _G.UnitName

local LOAD_ERROR_POPUP = "DEJAVU_LOAD_ERROR"
local sharedAddOnOrder = {
    "DejaVu_Panel",
    "DejaVu_Matrix",
    "DejaVu_Aura",
    "DejaVu_Player",
    "DejaVu_Spell",
    "DejaVu_Enemy",
    "DejaVu_Party",
    "DejaVu_Common",
}
local classAddOnByClass = {
    DEATHKNIGHT = "DejaVu_DeathKnight",
    DEMONHUNTER = "DejaVu_DemonHunter",
    DRUID = "DejaVu_Druid",
    PRIEST = "DejaVu_Priest",
}

-- DejaVu Core
local DejaVu = _G["DejaVu"]
local logging = DejaVu.Logging
local popupDialogs = _G.StaticPopupDialogs

popupDialogs[LOAD_ERROR_POPUP] = {
    text = "DejaVu failed to load add-on:\n%s",
    button1 = _G.OKAY,
    timeout = 0,
    whileDead = true,
    hideOnEscape = true,
}

local function ShowLoadError(addOnNameToLoad, reason)
    local errorMessage = format("%s\nReason: %s", addOnNameToLoad, tostring(reason or "UNKNOWN"))
    logging("failed to load " .. addOnNameToLoad .. ": " .. tostring(reason))
    StaticPopup_Show(LOAD_ERROR_POPUP, errorMessage)
end

local function TryLoadAddOn(addOnNameToLoad)
    local loaded, reason = LoadAddOn(addOnNameToLoad)
    if loaded then
        return true
    end

    ShowLoadError(addOnNameToLoad, reason)
    return false
end

local function LoadAddOnsInOrder(addOnNames)
    for addOnIndex = 1, #addOnNames do
        if not TryLoadAddOn(addOnNames[addOnIndex]) then
            return false
        end
    end
    return true
end

logging(addonName .. " loaded.")

if LoadAddOnsInOrder(sharedAddOnOrder) then
    local classFilename = select(2, UnitClass("player"))
    local classAddOnName = classAddOnByClass[classFilename]

    if classAddOnName then
        TryLoadAddOn(classAddOnName)
    end
end

DisableAddOn("163UI_Info", UnitName("player"))
DisableAddOn("HeyboxPlayerInfo", UnitName("player"))
