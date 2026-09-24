--[[
original: ../conditions/spec_power_essence@dev/template.lua
uuid: {{uuid}}
摘要：显示玩家精华整数。
描述：固定 Essence，普通整数除以 255；秘密值、越界或非整数直接报错。
修改记录：2026-09-18：新增次要资源条件。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local After = C_Timer.After -- 下一帧刷新
local CreateFrame = CreateFrame -- 独立事件框架
local UnitPower = UnitPower -- 读取非原始单位资源
local POWER_TYPE = Enum.PowerType.Essence -- 固定精华
local issecretvalue = issecretvalue -- 必须先检查秘密值
local type = type -- 校验数值类型
local error = error -- 违反直接值契约即报错
local insert = table.insert -- 注册初始化
--[[
UnitPower(unitToken, powerType, unmodified) 返回非 nil number。
固定 player、Essence、false；API 标记 SecretWhenUnitPowerRestricted。
按冻结约定读取次要资源；若返回 secret，先硬 error，绝不比较、缩放或清黑兜底。
来源：@wow-ui-source/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua。
2026-09-18：按 todo_list2.md 已确认目标版本约定核对签名，不重新复核 build 差异。
https://warcraft.wiki.gg/wiki/API_UnitPower （本次未读取 Wiki 页面）。
]]
--[[  variable reference  ]]
local Cell = addonTable.Cell -- 普通像素格
local UIInitFuncs = addonTable.UIInitFuncs -- UI 初始化队列
--[[  logical code  ]]
local UNIT_TOKEN = "player" -- 固定玩家
local POSITION_X = {{x1}} -- 冻结列
local POSITION_Y = {{y1}} -- 冻结行
local MAX_ENCODED_POWER = 255 -- 单通道整数上限
local powerCell
local eventFrame = CreateFrame("Frame")
local function update()
    if not powerCell then return end -- 初始化前不读取资源
    local power = UnitPower(UNIT_TOKEN, POWER_TYPE, false)
    if issecretvalue(power) then
        error("次要资源返回秘密值")
    end
    if type(power) ~= "number" or power < 0 or power > MAX_ENCODED_POWER or power % 1 ~= 0 then
        error("次要资源必须为 0..255 整数")
    end
    local mean = power / MAX_ENCODED_POWER
    powerCell:setCellRGBA(mean, mean, mean)
end
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
eventFrame:RegisterUnitEvent("UNIT_POWER_UPDATE", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_MAXPOWER", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_DISPLAYPOWER", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)
insert(UIInitFuncs, function()
    powerCell = Cell:New({ x = POSITION_X, y = POSITION_Y })
    update()
end)
