--[[
original: ../conditions/player_is_empowering@dev/template.lua
uuid: {{uuid}}
plugin: player_is_empowering@dev
摘要：玩家是否正在蓄力。
描述：
    普通施法、普通通道及空闲为假，蓄力通道为真；不判断秘密名称或纹理。
    参数校验和配对解码见 condition.py；本实例使用冻结坐标，不继承旧项目分类色。
修改记录：
2026-09-15：事件统一延至下一帧刷新。
2026-09-15：按已确认计划新增玩家条件插件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After             -- 事件后延至下一帧刷新
local CreateFrame = CreateFrame         -- 创建本实例事件或显示框架
local insert = table.insert             -- 注册 UI 初始化回调
local UnitCastingInfo = UnitCastingInfo -- 使用普通施法的非秘密哨兵及图标
local UnitChannelInfo = UnitChannelInfo -- 使用通道的非秘密蓄力哨兵及图标

--[[
用途与签名：UnitCastingInfo("player") 第 11 项 delayTimeMs、UnitChannelInfo("player") 第 9 项 isEmpowered 是 NeverSecret；后者返回通道是否蓄力的布尔值，无通道时无值。
业务限制：普通施法、普通通道及空闲为假，蓄力通道为真；不判断秘密名称或纹理。
核验日期：2026-09-15；本地 @wow-ui-source，12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：本地源码 Interface/AddOns/ 下：
    Blizzard_APIDocumentationGenerated/UnitDocumentation.lua
Wiki 查询入口（本次未能获取在线说明；以下链接不作为已核验网页证据）：
    https://warcraft.wiki.gg/wiki/API_UnitCastingInfo
    https://warcraft.wiki.gg/wiki/API_UnitChannelInfo
]]

--[[  variable reference  ]]
local Cell = addonTable.Cell               -- 黑色底板及单元格显示接口
local UIInitFuncs = addonTable.UIInitFuncs -- 共享布局就绪后初始化本实例

--[[  logical code  ]]
local POSITION_X = {{x1}} -- 本实例冻结的横向位置
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local UNIT_TOKEN = "player" -- 本版本固定玩家单位

local display
local eventFrame = CreateFrame("Frame")

local function update()
    if not display then return end
    local _, _, _, _, _, _, _, _, _, _, castDelayTimeMs = UnitCastingInfo(UNIT_TOKEN)
    if castDelayTimeMs ~= nil then -- NeverSecret 哨兵，不比较施法名称或纹理
        display:setCellBoolean(false)
        return
    end
    local _, _, _, _, _, _, _, _, isEmpowered = UnitChannelInfo(UNIT_TOKEN)
    if isEmpowered ~= nil then -- false 也是有效的普通通道哨兵
        display:setCellBoolean(isEmpowered)
        return
    end
    display:clearCell()
end

local function initialize()
    display = Cell:New({ x = POSITION_X, y = POSITION_Y })
    update()
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时同步本实例状态
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED_QUIET", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_DELAYED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_UPDATE", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTIBLE", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_NOT_INTERRUPTIBLE", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)

insert(UIInitFuncs, initialize)
