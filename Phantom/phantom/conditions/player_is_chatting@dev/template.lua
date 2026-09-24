--[[
original: ../conditions/player_is_chatting@dev/template.lua
uuid: {{uuid}}
plugin: player_is_chatting@dev
摘要：玩家是否具有键盘输入焦点。
描述：
    任意输入框获得焦点即为真，包含搜索框；保留聊天通知和1 秒兜底轮询。
    参数校验和配对解码见 condition.py；本实例使用冻结坐标，不继承旧项目分类色。
修改记录：
2026-09-15：事件统一延至下一帧刷新；兜底轮询统一为 1 秒并使用 UPDATE_INTERVAL。
2026-09-15：按已确认计划新增玩家条件插件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After                             -- 事件后延至下一帧刷新
local random = math.random                              -- 为本实例轮询生成随机错峰
local CreateFrame = CreateFrame                         -- 创建本实例事件或显示框架
local insert = table.insert                             -- 注册 UI 初始化回调
local GetCurrentKeyBoardFocus = GetCurrentKeyBoardFocus -- 获取键盘输入焦点
local EventRegistry = EventRegistry                     -- 监听聊天框焦点通知

--[[
用途与签名：frame = GetCurrentKeyBoardFocus()；返回输入焦点框体或 nil。EventRegistry:RegisterCallback(event, callback, owner) 注册聊天焦点通知。
业务限制：任意输入框获得焦点即为真，包含搜索框；保留聊天通知和1 秒兜底轮询。
核验日期：2026-09-15；本地 @wow-ui-source，12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：本地源码 Interface/AddOns/ 下：
    Blizzard_Game/Mainline/EventImplementation.lua
    Blizzard_ChatFrameBase/Shared/ChatFrameEditBox.lua
Wiki 查询入口（本次未能获取在线说明；以下链接不作为已核验网页证据）：
    https://warcraft.wiki.gg/wiki/API_GetCurrentKeyBoardFocus
]]

--[[  variable reference  ]]
local Cell = addonTable.Cell               -- 黑色底板及单元格显示接口
local UIInitFuncs = addonTable.UIInitFuncs -- 共享布局就绪后初始化本实例

--[[  logical code  ]]
local UPDATE_INTERVAL = 1   -- 事件之外的兜底刷新间隔
local POSITION_X = {{x1}} -- 本实例冻结的横向位置
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local UNIT_TOKEN = "player" -- 本版本固定玩家单位

local cell
local eventFrame = CreateFrame("Frame")

local function update()
    if not cell then return end -- UI 初始化之前不访问显示对象
    cell:setCellBoolean(GetCurrentKeyBoardFocus() ~= nil)
end

local function initialize()
    cell = Cell:New({ x = POSITION_X, y = POSITION_Y }) -- 黑底等待事件或错峰首次刷新
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时同步本实例状态
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)

if EventRegistry then
    EventRegistry:RegisterCallback("ChatFrame.OnEditBoxFocusGained", function()
                                       After(0, function() update() end)
                                   end, eventFrame)
    EventRegistry:RegisterCallback("ChatFrame.OnEditBoxFocusLost", function()
                                       After(0, function() update() end)
                                   end, eventFrame)
    EventRegistry:RegisterCallback("ChatFrame.OnEditBoxShow", function()
                                       After(0, function() update() end)
                                   end, eventFrame)
    EventRegistry:RegisterCallback("ChatFrame.OnEditBoxHide", function()
                                       After(0, function() update() end)
                                   end, eventFrame)
end

local fastTimeElapsed = -random() -- 每个实例独立随机错峰
eventFrame:SetScript("OnUpdate", function(_, elapsed)
    fastTimeElapsed = fastTimeElapsed + elapsed
    if fastTimeElapsed > UPDATE_INTERVAL then
        fastTimeElapsed = fastTimeElapsed - UPDATE_INTERVAL
        update()
    end
end)

insert(UIInitFuncs, initialize)
