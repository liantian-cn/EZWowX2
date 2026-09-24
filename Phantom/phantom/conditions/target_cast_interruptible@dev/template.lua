--[[
original: ../conditions/target_cast_interruptible@dev/template.lua
uuid: {{uuid}}
摘要：目标当前施法或引导是否可中断。
描述：存在前置；秘密布尔直接交给颜色消费者，不在 Lua 中分支或取反。
修改记录：2026-09-18：按已确认契约新增。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建事件框架
local After = C_Timer.After -- 事件下一帧刷新
local insert = table.insert -- 注册初始化
local random = math.random -- 独立错峰
local UnitExists = UnitExists -- 普通单位存在前置
local UnitCastingInfo = UnitCastingInfo -- 本条件业务状态
local EvaluateColorFromBoolean = C_CurveUtil.EvaluateColorFromBoolean -- 安全颜色消费者
local UnitChannelInfo = UnitChannelInfo -- 引导第9项 NeverSecret 哨兵
local issecretvalue = issecretvalue -- 仅对普通 nil 作不可用判断
--[[
UnitCastingInfo(unit) 第8项、UnitChannelInfo(unit) 第7项为 notInterruptible（可能秘密、可 nil）。
第11项 delayTimeMs／第9项 isEmpowered 为 NeverSecret 状态哨兵，后者 false 也有效。
普通 nil 保守清黑；秘密布尔直接 EvaluateColorFromBoolean(value, BLACK, WHITE)，不在 Lua 中反转。
施法信息标记 SecretWhenUnitSpellCastRestricted，单位参数为 UnitTokenPvPRestrictedForAddOns。
核验：2026-09-18，12.1.0.69587，revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua、CurveUtilDocumentation.lua。
Wiki：https://warcraft.wiki.gg/wiki/API_UnitCastingInfo （2026-09-18 获取；网页版本不替代目标 build 源码）。
]]
--[[  variable reference  ]]
local Cell = addonTable.Cell -- 黑白像素消费者
local COLOR = addonTable.COLOR -- 颜色常量
local UIInitFuncs = addonTable.UIInitFuncs -- 布局完成后构造
--[[  logical code  ]]
local POSITION_X = {{x1}}
local POSITION_Y = {{y1}}
local UNIT_TOKEN = "target"
local UPDATE_INTERVAL = 1 -- 低频状态兜底
local display
local eventFrame = CreateFrame("Frame")
local function update()
    if not display then return end
    if not UnitExists(UNIT_TOKEN) then display:clearCell(); return end
    local _, _, _, _, _, _, _, blocked, _, _, delayTimeMs = UnitCastingInfo(UNIT_TOKEN)
    if delayTimeMs == nil then
        local _, _, _, _, _, _, channelBlocked, _, isEmpowered = UnitChannelInfo(UNIT_TOKEN)
        if isEmpowered == nil then display:clearCell(); return end
        blocked = channelBlocked
    end
    if not issecretvalue(blocked) and blocked == nil then display:clearCell(); return end
    display:setCell(EvaluateColorFromBoolean(blocked, COLOR.BLACK, COLOR.WHITE))
end
local function initialize()
    display = Cell:New({ x = POSITION_X, y = POSITION_Y })
    update()
end
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
eventFrame:RegisterEvent("PLAYER_TARGET_CHANGED")
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED_QUIET", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_DELAYED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_UPDATE", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTIBLE", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_NOT_INTERRUPTIBLE", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function() After(0, update) end)
local fastTimeElapsed = -random()
eventFrame:SetScript("OnUpdate", function(_, elapsed)
    fastTimeElapsed = fastTimeElapsed + elapsed
    if fastTimeElapsed > UPDATE_INTERVAL then
        fastTimeElapsed = fastTimeElapsed - UPDATE_INTERVAL
        update()
    end
end)
insert(UIInitFuncs, initialize)
