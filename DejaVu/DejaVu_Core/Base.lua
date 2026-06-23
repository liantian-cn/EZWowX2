local addonName, DejaVu_Core = ...
local After = C_Timer.After
local GetTime = GetTime
local max = math.max
local min = math.min
local print = print
local tostring = tostring
local GetPhysicalScreenSize = GetPhysicalScreenSize
local GetScreenHeight = GetScreenHeight

_G["DejaVu"] = DejaVu_Core
DejaVu_Core.DEBUG = true             -- 是否开启调试模式
DejaVu_Core.Enable = true            -- 是否开启插件
DejaVu_Core.VERSION = "12.0.5.67165" -- 插件版本
DejaVu_Core.RangedRange = 40         -- 默认的远程检测范围
DejaVu_Core.MeleeRange = 5           -- 默认的近战检测范围
DejaVu_Core.BadgeTitleTable = {}     -- 脚标提示表（key格式: icon_r_g_b, value格式: {icon=图标路径或ID, color=脚标颜色, title=提示文本}）
-- /dump DejaVu.BadgeTitleTable

local function logging(msg)
    print("|cFFFFBB66[" .. addonName .. "]|r" .. tostring(msg))
end



local function GetUIScaleFactor(pixelValue)
    local physicalHeight = select(2, GetPhysicalScreenSize())
    local UI_scale = UIParent:GetScale()
    return pixelValue * 768 / physicalHeight / UI_scale
end


DejaVu_Core.Logging = logging
DejaVu_Core.GetUIScaleFactor = GetUIScaleFactor




DejaVu_Core.BurstTime = GetTime() + 60

DejaVu_Core.InBurst = function()
    return DejaVu_Core.BurstTime > GetTime()
end

DejaVu_Core.BurstRemaining = function()
    return min(60.0, max(0, DejaVu_Core.BurstTime - GetTime()))
end

SLASH_BURST1 = "/burst"
SlashCmdList["BURST"] = function(msg)
    local delaySeconds = tonumber(msg)
    if delaySeconds then
        DejaVu_Core.BurstTime = GetTime() + delaySeconds
    end
end

After(0, function()
    SetCVar("useUiScale", 0)
    -- C_UI.Reload()
end)
SetCVar("secretChallengeModeRestrictionsForced", 0)
SetCVar("secretCombatRestrictionsForced", 0)
SetCVar("secretEncounterRestrictionsForced", 0)
SetCVar("secretMapRestrictionsForced", 0)
SetCVar("secretPvPMatchRestrictionsForced", 0)
SetCVar("secretAuraDataRestrictionsForced", 0)
SetCVar("scriptErrors", 1);
SetCVar("doNotFlashLowHealthWarning", 1);
SetCVar("lossOfControl", 0);
SetCVar("cameraIndirectVisibility", 1);
SetCVar("cameraIndirectOffset", 10);
SetCVar("SpellQueueWindow", 400);
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
