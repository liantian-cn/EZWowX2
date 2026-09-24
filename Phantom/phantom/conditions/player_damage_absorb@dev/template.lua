--[[
original: ../conditions/player_damage_absorb@dev/template.lua
uuid: {{uuid}}
plugin: player_damage_absorb@dev
摘要：玩家伤害吸收量是否超过阈值。
描述：
    白色 StatusBar 覆盖黑底；整数吸收量不超过 N 为黑色，至少 N+1 为白色，Lua 不比较或计算吸收值。
    参数校验和配对解码见 condition.py；本实例使用冻结坐标，不继承旧项目分类色。
修改记录：
2026-09-20：直接使用 CellBackplate，吸收条使用静态 Content 层级。
2026-09-15：事件统一延至下一帧刷新。
2026-09-15：按已确认计划新增玩家条件插件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After                     -- 事件后延至下一帧刷新
local CreateFrame = CreateFrame                 -- 创建本实例事件或显示框架
local insert = table.insert                     -- 注册 UI 初始化回调
local UnitGetTotalAbsorbs = UnitGetTotalAbsorbs -- 获取秘密伤害吸收量

--[[
用途与签名：value = UnitGetTotalAbsorbs("player")；返回秘密数值，直接送入 StatusBar:SetValue(value)。SetMinMaxValues(N, N+1) 固定阈值显示范围。
业务限制：白色 StatusBar 覆盖黑底；整数吸收量不超过 N 为黑色，至少 N+1 为白色，Lua 不比较或计算吸收值。
核验日期：2026-09-15；本地 @wow-ui-source，12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：本地源码 Interface/AddOns/ 下：
    Blizzard_APIDocumentationGenerated/UnitDocumentation.lua
Wiki 查询入口（本次未能获取在线说明；以下链接不作为已核验网页证据）：
    https://warcraft.wiki.gg/wiki/API_UnitGetTotalAbsorbs
]]

--[[  variable reference  ]]
local CellBackplate = addonTable.CellBackplate -- 固定黑色背板
local COLOR = addonTable.COLOR             -- 本项目共享黑白及施法颜色
local FrameLevel = addonTable.FrameLevel   -- 共享底板和光环显示层级
local UIInitFuncs = addonTable.UIInitFuncs -- 共享布局就绪后初始化本实例

--[[  logical code  ]]
local POSITION_X = {{x1}}   -- 本实例冻结的横向位置
local POSITION_Y = {{y1}}   -- 本实例冻结的 Cell 行
local UNIT_TOKEN = "player"     -- 本版本固定玩家单位
local THRESHOLD = {{threshold}} -- N 与 N+1 都可精确表示
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"

local absorbBar
local eventFrame = CreateFrame("Frame")

local function update()
    if not absorbBar then return end
    absorbBar:SetValue(UnitGetTotalAbsorbs(UNIT_TOKEN)) -- 秘密值直接渲染，禁止 Lua 阈值比较
end

local function initialize()
    local backing = CellBackplate:New({ x = POSITION_X, y = POSITION_Y }) -- 登记第二行占位并提供黑底
    absorbBar = CreateFrame("StatusBar", nil, backing.Frame)
    absorbBar:SetAllPoints(backing.Frame)
    absorbBar:SetFrameLevel(FrameLevel.Content)
    absorbBar:SetStatusBarTexture(WHITE_TEXTURE)
    absorbBar:SetStatusBarColor(COLOR.WHITE:GetRGBA())
    absorbBar:SetMinMaxValues(THRESHOLD, THRESHOLD + 1)
    update()
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时同步本实例状态
eventFrame:RegisterUnitEvent("UNIT_ABSORB_AMOUNT_CHANGED", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)
insert(UIInitFuncs, initialize)
