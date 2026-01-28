local addonName, addonTable = ...
addonTable.DEBUG            = false

addonTable.logging          = function(msg)
    -- 输出调试日志信息
    -- @param msg 要输出的日志消息
    if addonTable.DEBUG then
        print("|cFFFFBB66[" .. addonName .. "]|r", msg)
    end
end

local log                   = addonTable.logging


addonTable.FrameInitFuncs = {}
addonTable.UpdateFuncs    = {}


local curve = C_CurveUtil.CreateColorCurve()
curve:SetType(Enum.LuaCurveType.Linear)
curve:AddPoint(0.0, CreateColor(0, 0, 0))
curve:AddPoint(1.0, CreateColor(1, 1, 1))
addonTable.curve = curve

local curve_reverse = C_CurveUtil.CreateColorCurve()
curve_reverse:SetType(Enum.LuaCurveType.Linear)
curve_reverse:AddPoint(0.0, CreateColor(1, 1, 1))
curve_reverse:AddPoint(1.0, CreateColor(0, 0, 0))
addonTable.curve_reverse = curve_reverse


local DEBUFF_DISPLAY_COLOR_INFO = {
    -- [0] = DEBUFF_TYPE_NONE_COLOR,
    [0] = { r = 0, g = 0, b = 0, a = 1 },
    [1] = DEBUFF_TYPE_MAGIC_COLOR,
    [2] = DEBUFF_TYPE_CURSE_COLOR,
    [3] = DEBUFF_TYPE_DISEASE_COLOR,
    [4] = DEBUFF_TYPE_POISON_COLOR,
    [9] = DEBUFF_TYPE_BLEED_COLOR, -- enrage
    [11] = DEBUFF_TYPE_BLEED_COLOR,
}
local debuff_curve = C_CurveUtil.CreateColorCurve()
if debuff_curve then
    debuff_curve:SetType(Enum.LuaCurveType.Step)
    for i, c in pairs(DEBUFF_DISPLAY_COLOR_INFO) do
        debuff_curve:AddPoint(i, c)
    end
end
addonTable.debuff_curve = debuff_curve



local frame = CreateFrame("Frame")

frame:RegisterEvent("PLAYER_ENTERING_WORLD")
frame:SetScript("OnEvent", function(self, event, isInitialLogin, isReloadingUi)
    -- 只在初次登录或重新加载 UI 时执行一次
    -- 使用 C_Timer.After(0) 是为了确保在事件循环的下一帧执行
    -- 这样可以给图形引擎留出最后的"握手时间"
    C_Timer.After(0, function()
        wipe(addonTable.UpdateFuncs)
        for _, func in ipairs(addonTable.FrameInitFuncs) do
            func()
        end
    end)

    -- 执行完后注销事件，避免反复进入副本时重复加载
    self:UnregisterEvent("PLAYER_ENTERING_WORLD")
end)



addonTable.timeElapsed = 0
frame:HookScript("OnUpdate", function(self, elapsed)
    local tickOffset       = 1.0 / addonTable.FPS;
    addonTable.timeElapsed = addonTable.timeElapsed + elapsed
    if addonTable.timeElapsed > tickOffset then
        addonTable.timeElapsed = 0
        for _, updater in ipairs(addonTable.UpdateFuncs) do
            updater()
        end
    end
end)


-- 设置游戏变量，确保插件正常运行
SetCVar("secretChallengeModeRestrictionsForced", 1)
SetCVar("secretCombatRestrictionsForced", 1)
SetCVar("secretEncounterRestrictionsForced", 1)
SetCVar("secretMapRestrictionsForced", 1)
SetCVar("secretPvPMatchRestrictionsForced", 1)
SetCVar("secretAuraDataRestrictionsForced", 1)
SetCVar("scriptErrors", 1);
SetCVar("doNotFlashLowHealthWarning", 1);
