-- DejaVu 的 luacheck 根配置。
-- 目标: 提供 Lua 5.1 + 常见 WoW 全局的基础检查环境, 
-- 特殊 API 继续优先在文件内用 `-- luacheck: globals ...` 显式声明。

std = "lua51"
max_line_length = 360

read_globals = {
    "C_AddOns",
    "C_CurveUtil",
    "C_Container",
    "C_Item",
    "C_Spell",
    "C_SpellActivationOverlay",
    "C_SpellBook",
    "C_Timer",
    "C_UnitAuras",
    "CreateColor",
    "CreateFrame",
    "Enum",
    "GameFontHighlight",
    "GameTooltip",
    "GetRuneCooldown",
    "GetCurrentKeyBoardFocus",
    "GetInventoryItemID",
    "GetPhysicalScreenSize",
    "GetScreenHeight",
    "GetSpecialization",
    "GetTime",
    "GetUnitSpeed",
    "IsInGroup",
    "IsInRaid",
    "IsMounted",
    "issecretvalue",
    "SetCVar",
    "SetOverrideBindingClick",
    "SpellIsTargeting",
    "UIParent",
    "UnitAffectingCombat",
    "UnitCastingDuration",
    "UnitCastingInfo",
    "UnitCanAttack",
    "UnitChannelDuration",
    "UnitChannelInfo",
    "UnitClass",
    "UnitEmpoweredStageDurations",
    "UnitExists",
    "UnitGroupRolesAssigned",
    "UnitGetTotalAbsorbs",
    "UnitGetTotalHealAbsorbs",
    "UnitHealthPercent",
    "UnitHealthMax",
    "UnitInVehicle",
    "UnitIsDeadOrGhost",
    "UnitIsEnemy",
    "UnitIsUnit",
    "UnitPower",
    "UnitPowerPercent",
    "UnitPowerType",
    "wipe",
}

globals = {
    "DejaVuSave",
    "DejaVu_CoreSave",
    "SlashCmdList",
}

ignore = {
    "211",
    "212",
    "213",
}

files["DejaVu_Panel/DejaVu_Panel.lua"] = {
    ignore = {
        "311/COLOR",
    }
}
