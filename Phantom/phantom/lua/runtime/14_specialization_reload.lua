--[[
original: runtime\14_specialization_reload.lua
uuid: e9d6b95d-4b53-4baa-a6c9-481ed0dcde18
runtime_index: 14
摘要：玩家实际切换专精后提示手动重载界面。

描述：
    以本次 UI 生命周期的初始有效专精为基准，仅在真实变化后显示一次标准弹窗。
    弹窗只有重载确认按钮，不允许取消、关闭或超时；确认后直接调用 ReloadUI。
    登录与重载后的同专精事件不弹窗，弹窗被其他弹窗挤掉后不重试。

修改记录：
2026-09-19：新增专精变化后的单次重载确认。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

--[[
C_SpecializationInfo.GetSpecialization() 返回玩家当前专精索引；尚未就绪时允许 nil。
本文件不传可选的 isInspect、isPet、specGroupIndex，读取玩家自身索引作为生命周期基准。
ACTIVE_PLAYER_SPECIALIZATION_CHANGED 不带参数，收到事件后重新查询；初始化事件不能视为变化。
Wiki：https://warcraft.wiki.gg/wiki/API_C_SpecializationInfo.GetSpecialization

ReloadUI() 无参数、无返回值，是 C_UI.Reload() 的包装，需要用户硬件事件。
仅从标准弹窗确认按钮的 OnAccept 调用，不由事件或计时器自动调用。
Wiki：https://warcraft.wiki.gg/wiki/API:C_UI.Reload

2026-09-19 沿用任务已核验的 wow-ui-source ptr 12.1.0.69587，
revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58：
SpecializationInfoDocumentation.lua、UIDocumentation.lua 及 GameDialogDefs.lua 698–709。
上述为源码核验，不代表实机验证。
]]
local GetSpecialization = C_SpecializationInfo.GetSpecialization -- 查询玩家实际专精
local CreateFrame = CreateFrame                               -- 创建独立事件框体
local StaticPopupDialogs = StaticPopupDialogs                 -- 注册标准确认弹窗
local StaticPopup_Show = StaticPopup_Show                     -- 仅尝试显示一次弹窗
local ReloadUI = ReloadUI                                     -- 用户确认后重载界面

--[[  variable reference  ]]

-- 本文件独立记录专精基准，不引用其他运行时状态。

--[[  logical code  ]]

local baselineSpecialization = GetSpecialization() -- 文件加载时记录本次 UI 的专精基准
local prompted = false                            -- 本次 UI 生命周期至多提示一次
local popupName = addonName .. "_SPECIALIZATION_RELOAD" -- 按插件名隔离标准弹窗定义

StaticPopupDialogs[popupName] = {
    text = "专精已切换，请重载界面以加载对应循环。",
    button1 = "重载界面",
    OnAccept = function()
        ReloadUI() -- 保持用户点击到重载调用的直接路径
    end,
    timeout = 0,          -- 标准弹窗的零值表示不超时
    hideOnEscape = false, -- Lua 中数字零为真，必须使用 false
    closeButton = false,  -- 不显示右上角关闭按钮
    whileDead = true,     -- 死亡状态仍可确认重载
}

local eventFrame = CreateFrame("Frame") -- 只监听玩家实际专精变化事件
eventFrame:RegisterEvent("ACTIVE_PLAYER_SPECIALIZATION_CHANGED")
eventFrame:SetScript("OnEvent", function()
    local specialization = GetSpecialization() -- 事件没有 payload，重新读取当前索引
    if specialization == nil then
        return -- 初始化尚未就绪，不丢弃已有基准
    end
    if baselineSpecialization == nil then
        baselineSpecialization = specialization -- 首个有效索引仅用于初始化
        return
    end
    if specialization ~= baselineSpecialization and not prompted then
        prompted = true -- 在显示前标记，重复事件或弹窗被挤掉都不重试
        StaticPopup_Show(popupName)
    end
end)
