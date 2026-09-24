--[[
original: runtime\01_addon.lua
uuid: 20d63786-5c32-4c07-8c5f-c8f0420844a8
runtime_index: 1
摘要：初始化插件基础参数、公共日志与像素换算函数，并延迟执行 UI 初始化。



描述：
    - 作为首个运行时文件，公开调试开关、版本和显示缩放参数。
    - 提供带插件名前缀的日志输出，以及按屏幕物理高度和 UIParent 缩放换算尺寸的函数。
    - 建立跨文件共用的 UI 初始化回调表，并通过零秒定时器延后按注册顺序调用。
    - 加载时写入界面、Secret 限制、镜头、同步和图像相关的客户端 CVar 配置。


修改记录：
2026-09-06：liantian-cn初始化创建。

]]


--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local After = C_Timer.After                         -- 延迟调用 UI 初始化回调
local print = print                                 -- 向聊天窗口输出日志
local tostring = tostring                           -- 将日志内容转换为字符串
local GetPhysicalScreenSize = GetPhysicalScreenSize -- 获取屏幕物理像素宽高

local select = select                               -- 提取屏幕尺寸返回值中的高度
local ipairs = ipairs                               -- 按顺序遍历 UI 初始化回调表
local SetCVar = SetCVar                             -- 写入客户端配置变量
local UIParent = UIParent                           -- 读取游戏根界面当前的缩放比例

--[[  variable reference  ]]

-- 本文件建立共享基础接口，无需缓存其他文件提供的引用。

--[[  logical code  ]]

addonTable.DEBUG = false                                        -- 是否开启调试模式
addonTable.VERSION = "12.1.0.68209"                             -- 插件版本

addonTable.logging = function(msg)                              -- 提供不受调试开关控制的公共日志
    print("|cFFFFBB66[" .. addonName .. "]|r" .. tostring(msg)) -- 添加彩色插件名前缀并输出消息
end

addonTable.debug = function(msg)                                    -- 提供受调试开关控制的公共日志
    if addonTable.DEBUG then                                        -- 每次输出时读取共享调试开关
        print("|cFFFFBB66[" .. addonName .. "]|r" .. tostring(msg)) -- 添加彩色插件名前缀并输出消息
    end
end


-- 缩放
if addonTable.DEBUG then -- 按调试开关选择显示倍率
    addonTable.SCALE = 8 -- 调试时放大显示以便观察像素布局
else
    addonTable.SCALE = 1 -- 常规显示使用原始尺寸
end

--[[  UI设计
尺寸换算沿用官方 PixelUtil 的 768 / physicalHeight 系数，并抵消 UIParent 当前缩放。
UI 初始化通过 After(0) 延后执行；此处不保证具体帧序号，也不监听后续缩放变化。
]]

addonTable.GetUIScaleFactor = function(pixelValue)            -- 将目标物理像素尺寸换算为 UI 尺寸
    local physicalHeight = select(2, GetPhysicalScreenSize()) -- 取物理屏幕高度作为换算基准
    local UI_scale = UIParent:GetScale()                      -- 每次换算时读取根界面的当前缩放
    return pixelValue * 768 / physicalHeight / UI_scale       -- 抵消物理高度差异和父级缩放
end


addonTable.UIInitFuncs = {}                          -- UI初始化函数表

After(0, function()                                  -- 延后执行，供其他运行时文件先注册 UI 初始化函数
    for _, func in ipairs(addonTable.UIInitFuncs) do -- 执行时读取共享表并按注册顺序遍历
        func()                                       -- 创建该回调负责的界面组件
    end
end)



SetCVar("useUiScale", 0)                            -- 关闭自定义 UI 缩放开关
SetCVar("secretChallengeModeRestrictionsForced", 1) -- 写入挑战模式 Secret 限制强制开关
SetCVar("secretCombatRestrictionsForced", 1)        -- 写入战斗 Secret 限制强制开关
SetCVar("secretEncounterRestrictionsForced", 1)     -- 写入首领战 Secret 限制强制开关
SetCVar("secretMapRestrictionsForced", 1)           -- 写入地图 Secret 限制强制开关
SetCVar("secretPvPMatchRestrictionsForced", 1)      -- 写入 PvP 比赛 Secret 限制强制开关
SetCVar("secretAuraDataRestrictionsForced", 1)      -- 写入光环数据 Secret 限制强制开关
SetCVar("scriptErrors", 1);                         -- 开启 Lua 错误显示
SetCVar("doNotFlashLowHealthWarning", 1);           -- 关闭低生命值闪烁警告
SetCVar("lossOfControl", 0);                        -- 关闭失去控制效果提示
SetCVar("cameraIndirectVisibility", 1);             -- 写入镜头间接可见性配置
SetCVar("cameraIndirectOffset", 10);                -- 写入镜头间接偏移量
SetCVar("targetNearestDistance", 5)                 -- 写入最近目标的距离配置
SetCVar("cameraDistanceMaxZoomFactor", 2.6)         -- 写入镜头最大拉远倍率
SetCVar("CameraReduceUnexpectedMovement", 1)        -- 开启减少意外镜头移动选项
SetCVar("synchronizeSettings", 1)                   -- 写入设置同步开关
SetCVar("synchronizeConfig", 1)                     -- 写入配置同步开关
SetCVar("synchronizeBindings", 1)                   -- 写入按键绑定同步开关
SetCVar("synchronizeMacros", 1)                     -- 写入宏同步开关
SetCVar("LowLatencyMode", 0)                        --低延迟模式 0:关闭 1:内置 2:NVIDIA Reflex 3:NVIDIA Reflex + Boost 4:Intel XeLL
SetCVar("ffxAntiAliasingMode", 0)                   --基于图像的技术 0:无 1:FXAA低 2:FXAA高 3:CMAA 4:CMAA2
SetCVar("MSAAQuality", 0)                           --多重采样技术 0:无 1:色彩 2x / 景深 2x 2:色彩 4x / 景深 4x 3:色彩 8x / 景深 8x
SetCVar("Contrast", 50)                             --对比度 minValue, maxValue, step = 0, 100, 1
SetCVar("Brightness", 50)                           --亮度 minValue, maxValue, step = 0, 100, 1
SetCVar("Gamma", 1)                                 --伽马值 minValue, maxValue, step = .3, 2.8, .1
