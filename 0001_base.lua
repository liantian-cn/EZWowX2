-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local After = C_Timer.After
local GetTime = GetTime
local max = math.max
local min = math.min
local print = print
local tostring = tostring
local GetPhysicalScreenSize = GetPhysicalScreenSize
local GetScreenHeight = GetScreenHeight

-- 插件级变量定义/引用

addonTable.DEBUG = true             -- 是否开启调试模式
addonTable.VERSION = "12.1.0.68209" -- 插件版本
addonTable.SPEC = {}
addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
}

-- 本地变量定义

-- 代码部分

addonTable.logging = function(msg)
    print("|cFFFFBB66[" .. addonName .. "]|r" .. tostring(msg))
end


addonTable.debug = function(msg)
    if addonTable.DEBUG then
        print("|cFFFFBB66[" .. addonName .. "]|r" .. tostring(msg))
    end
end

addonTable.GetUIScaleFactor = function(pixelValue)
    local physicalHeight = select(2, GetPhysicalScreenSize())
    local UI_scale = UIParent:GetScale()
    return pixelValue * 768 / physicalHeight / UI_scale
end



SetCVar("useUiScale", 0)
SetCVar("secretChallengeModeRestrictionsForced", 1)
SetCVar("secretCombatRestrictionsForced", 1)
SetCVar("secretEncounterRestrictionsForced", 1)
SetCVar("secretMapRestrictionsForced", 1)
SetCVar("secretPvPMatchRestrictionsForced", 1)
SetCVar("secretAuraDataRestrictionsForced", 1)
SetCVar("scriptErrors", 1);
SetCVar("doNotFlashLowHealthWarning", 1);
SetCVar("lossOfControl", 0);
SetCVar("cameraIndirectVisibility", 1);
SetCVar("cameraIndirectOffset", 10);
SetCVar("SpellQueueWindow", 300);
SetCVar("targetNearestDistance", 5)
SetCVar("cameraDistanceMaxZoomFactor", 2.6)
SetCVar("CameraReduceUnexpectedMovement", 1)
SetCVar("synchronizeSettings", 1)
SetCVar("synchronizeConfig", 1)
SetCVar("synchronizeBindings", 1)
SetCVar("synchronizeMacros", 1)
SetCVar("LowLatencyMode", 0)      --低延迟模式 0:关闭 1:内置 2:NVIDIA Reflex 3:NVIDIA Reflex + Boost 4:Intel XeLL
SetCVar("ffxAntiAliasingMode", 0) --基于图像的技术 0:无 1:FXAA低 2:FXAA高 3:CMAA 4:CMAA2
SetCVar("MSAAQuality", 0)         --多重采样技术 0:无 1:色彩 2x / 景深 2x 2:色彩 4x / 景深 4x 3:色彩 8x / 景深 8x
SetCVar("Contrast", 50)           --对比度 minValue, maxValue, step = 0, 100, 1
SetCVar("Brightness", 50)         --亮度 minValue, maxValue, step = 0, 100, 1
SetCVar("Gamma", 1)               --伽马值 minValue, maxValue, step = .3, 2.8, .1
