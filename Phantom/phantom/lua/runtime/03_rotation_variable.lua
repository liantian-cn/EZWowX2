--[[
original: runtime\03_rotation_variable.lua
uuid: becdc27d-385d-4d99-b757-50c9bc5ff327
runtime_index: 3
摘要：
    初始化插件启用、爆发和延迟状态，并提供共享查询与聊天命令。


描述：
    - 默认启用插件，并在本文件加载时将共享爆发截止时间设为当前时间的 60 秒后。
    - 根据共享截止时间查询是否仍处于爆发期，并将剩余秒数限制在 0 至 60 秒之间。
    - 延迟默认关闭，查询最新截止时间，剩余秒数仅限制下限为 0。
    - 使用插件名前两位的小写聊天命令，独立控制启用状态、延迟和爆发截止时间。
    - 合法命令静默执行；空输入或无效参数输出中文帮助，不改变共享状态。


修改记录：
2026-09-06：liantian-cn初始化创建。
2026-09-09：按已确认需求新增 Delay 查询与插件名派生的聊天命令。

]]


--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

--[[
GetTime()：无参数，返回系统运行秒数 number，用于计算截止时间与剩余时间。
时间值按渲染帧更新，不能作为帧内高精度计时器。
https://warcraft.wiki.gg/wiki/API_GetTime
聊天命令通过 SlashCmdList[key] = handler 和 _G["SLASH_" .. key .. "1"] = "/前缀" 注册。
handler(message, editBox) 接收参数文本和聊天输入框；本文件只读取 message，无返回值。
命令共用全局名称空间，系统命令优先；同前缀插件可能冲突。
https://warcraft.wiki.gg/wiki/Creating_a_slash_command
2026-09-09 核验：@wow-ui-source revision 288f40d5cee5089223758d5810cb906ad34d4018，
SystemTimeDocumentation.lua 与 Blizzard_ChatFrameBase/Shared/SlashCommandsRegistry.lua。
]]
local GetTime = GetTime -- 获取当前计时值，用于计算爆发及延迟截止时间
local globals = _G -- 注册动态命名的聊天命令全局变量
local SlashCmdList = SlashCmdList -- 注册插件聊天命令处理函数
local lower = string.lower -- 统一命令前缀与命令词大小写
local sub = string.sub -- 读取插件名的前两位
local match = string.match -- 分离命令词与可选参数
local tonumber = tonumber -- 解析正负整数或小数秒数，不附加时长限制
local print = print -- 将命令帮助输出到聊天窗口
local max = math.max -- 取较大值，将爆发剩余秒数下限限制为 0
local min = math.min -- 取较小值，将爆发剩余秒数上限限制为 60

--[[  variable reference  ]]



--[[  logical code  ]]


addonTable.ENABLE = true -- 是否开启插件


addonTable.BurstTime = GetTime() + 60 -- 初始化共享爆发截止时间，默认从加载时起持续 60 秒
addonTable.InBurst = function() -- 供其他文件查询当前是否处于爆发期
    return addonTable.BurstTime > GetTime() -- 截止时间晚于当前时间时仍处于爆发期
end
addonTable.BurstRemaining = function() -- 供其他文件查询爆发剩余秒数
    return min(60.0, max(0, addonTable.BurstTime - GetTime())) -- 实时读取共享截止时间，将剩余秒数限制在 0 至 60 秒之间
end

addonTable.DelayTime = GetTime() -- 默认不延迟，截止时间等于当前时间
addonTable.Delaying = function() -- 供其他文件查询当前是否正在延迟
    return addonTable.DelayTime > GetTime() -- 截止时间到达时立即结束延迟
end
addonTable.DelayRemaining = function() -- 供其他文件查询实际延迟剩余秒数
    return max(0, addonTable.DelayTime - GetTime()) -- 仅限制下限，不截断长延迟
end

local commandPrefix = "/" .. lower(sub(addonName, 1, 2)) -- 从实际插件名派生命令前缀
local commandKey = addonName .. "_ROTATION_CONTROL" -- 使用完整插件名区分内部注册标识

local function PrintCommandHelp()
    print(addonName .. " 命令帮助：")
    print(commandPrefix .. " disable：关闭插件；enable：开启插件；toggle：切换开启/关闭。")
    print(commandPrefix .. " delay [NN]：延迟 NN 秒，省略时为 0.4 秒。")
    print(commandPrefix .. " burst [NN]：爆发 NN 秒，省略时为 15 秒。")
    print("NN 支持正负数与小数，不限制位数或时长；每次从当前时间重新计时。")
    print("示例：" .. commandPrefix .. " delay 0.4；" .. commandPrefix .. " burst 99999（99999 秒）；"
        .. commandPrefix .. " delay -1（关闭延迟）；" .. commandPrefix .. " burst -1（关闭爆发）。")
end

local function HandleRotationCommand(message)
    local command, arguments = match(message, "^%s*(%S*)%s*(.-)%s*$") -- 去除首尾空白并拆出命令词
    command = lower(command) -- 命令词不区分大小写

    if command == "disable" or command == "enable" or command == "toggle" then
        if arguments ~= "" then -- 开关命令不接受额外参数
            PrintCommandHelp()
            return
        end
        if command == "toggle" then
            addonTable.ENABLE = not addonTable.ENABLE -- 只反转启用状态
        else
            addonTable.ENABLE = command == "enable" -- 明确开启或关闭
        end
    elseif command == "delay" or command == "burst" then
        local duration -- 本次命令要求的持续秒数
        if arguments == "" then
            duration = command == "delay" and 0.4 or 15 -- 省略数字时使用各自默认时长
        elseif not match(arguments, "%s") then -- 只允许一个数字参数
            duration = tonumber(arguments)
        end
        if not duration then -- 无效数字或多余参数不得修改截止时间
            PrintCommandHelp()
            return
        end
        if command == "delay" then
            addonTable.DelayTime = GetTime() + duration -- 替换延迟截止时间，负数立即结束
        else
            addonTable.BurstTime = GetTime() + duration -- 替换爆发截止时间，不改变延迟状态
        end
    else
        PrintCommandHelp() -- 空命令、help 和未知命令统一显示帮助
    end
end

globals["SLASH_" .. commandKey .. "1"] = commandPrefix -- 向聊天系统公开实际命令前缀
SlashCmdList[commandKey] = HandleRotationCommand -- 注册命令处理入口
