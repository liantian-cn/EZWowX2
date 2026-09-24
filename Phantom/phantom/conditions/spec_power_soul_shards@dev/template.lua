--[[
original: ../conditions/spec_power_soul_shards@dev/template.lua
uuid: {{uuid}}
摘要：按配置显示玩家整碎片或原始灵魂碎片片段。
描述：整碎片使用 Cell，秘密值、越界或非整数直接报错；小数模式直接传递原始片段给 ValueBar。
修改记录：2026-09-18：新增整灵魂碎片条件。
2026-09-19：新增构造时固定的小数模式、ValueBar 显示及玩家高频资源事件刷新。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local After = C_Timer.After -- 下一帧刷新
local CreateFrame = CreateFrame -- 独立事件框架
local UnitPower = UnitPower -- 按固定模式读取整碎片或原始片段
local POWER_TYPE = Enum.PowerType.SoulShards -- 固定灵魂碎片
local issecretvalue = issecretvalue -- 整碎片直接编码前检查秘密值
local type = type -- 整碎片模式校验数值类型
local error = error -- 违反直接值契约即报错
local insert = table.insert -- 注册初始化
--[[
UnitPower(unitToken, powerType, unmodified) 返回非 nil number。
固定 player、SoulShards；API 标记 SecretWhenUnitPowerRestricted、SecretArguments=AllowedWhenUntainted。
false 保留整碎片直接整数契约，若返回 secret 则先硬 error。
true 返回原始片段，范围固定 0..50；每 10 片段为一整碎片，只将结果直接传给 ValueBar:setValue。
其底层 StatusBar:SetValue(value, interpolation=Immediate) 接受 secret，AllowedWhenTainted；
Lua 不对原始片段做算术、比较、转数、计数或分支。片段格点恢复由 Python 像素解码完成。
2026-09-19 核验本地 12.1.0.69587，revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58：
@wow-ui-source/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua、
SimpleStatusBarAPIDocumentation.lua；Blizzard_UnitFrame/Mainline/ShardBar.lua 使用 true 与 DisplayMod。
目标 12.1.0.69814 未游戏实测；不复制官方 UI 中对片段的算术。
https://warcraft.wiki.gg/wiki/API_UnitPower （2026-09-19 已读取，说明原始 0..50 及每 10 片段一碎片）。
]]
--[[  variable reference  ]]
local Cell = addonTable.Cell -- 普通像素格
local ValueBar = addonTable.ValueBar -- 支持秘密值的现有数值条
local UIInitFuncs = addonTable.UIInitFuncs -- UI 初始化队列
--[[  logical code  ]]
local UNIT_TOKEN = "player" -- 固定玩家
local POSITION_X = {{x1}} -- 冻结列
local FRACTIONAL = {{fractional}} -- 配置常量，不随资源或专精自动切换
local OUTPUT_DIMENSION = {{output_dimension}} -- 核心冻结的 Cell 行或 ValueBar 内容宽度
local MAX_ENCODED_POWER = 255 -- 单通道整数上限
local MAX_FRAGMENTS = 50 -- 小数模式的固定原始片段量程
local powerCell
local powerBar
local eventFrame = CreateFrame("Frame")
local function update()
    if FRACTIONAL then
        if not powerBar then return end -- 初始化前不读取资源
        powerBar:setValue(UnitPower(UNIT_TOKEN, POWER_TYPE, true)) -- 秘密值仅交给受支持显示消费者
        return
    end
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
if FRACTIONAL then
    eventFrame:RegisterUnitEvent("UNIT_POWER_FREQUENT", UNIT_TOKEN) -- 捕获单片段变化，不读取事件资源参数
end
eventFrame:RegisterUnitEvent("UNIT_MAXPOWER", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_DISPLAYPOWER", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)
insert(UIInitFuncs, function()
    if FRACTIONAL then
        powerBar = ValueBar:New(POSITION_X, OUTPUT_DIMENSION, false)
        powerBar:setMinMaxValues(0, MAX_FRAGMENTS)
    else
        powerCell = Cell:New({ x = POSITION_X, y = OUTPUT_DIMENSION })
    end
    update()
end)
