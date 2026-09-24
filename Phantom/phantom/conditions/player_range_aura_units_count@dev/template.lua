--[[
original: ../conditions/player_range_aura_units_count@dev/template.lua
uuid: {{uuid}}
摘要：技能射程内指定减益的可观察敌人数。
描述：只扫描 nameplate1..40；初始化拒绝非 NeverSecret aura_id，接受中止剩余 UI 初始化。
    灰度 count/40，仅普通射程 true 且非秘密有害 Aura 可计数；事件加 1 秒兜底。
修改记录：2026-09-18：按冻结约定新增。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建事件框架
local After = C_Timer.After -- 延后一帧刷新
local random = math.random -- 随机错峰
local insert = table.insert -- 注册初始化
local error = error -- 配置不满足秘密限制时硬错误
local issecretvalue = issecretvalue -- 先检查秘密再做普通操作
local UnitExists = UnitExists -- 查询单位存在性
local UnitCanAttack = UnitCanAttack -- 只统计可攻击敌人
local UnitIsDeadOrGhost = UnitIsDeadOrGhost -- 排除死亡单位
local UnitAffectingCombat = UnitAffectingCombat -- 可选战斗筛选
local DoesSpellExist = C_Spell.DoesSpellExist -- 验证射程技能
local IsSpellInRange = C_Spell.IsSpellInRange -- 技能射程结果
local GetSpellAuraSecrecy = C_Secrets.GetSpellAuraSecrecy -- 检查光环秘密等级
local NeverSecret = Enum.SecrecyLevel.NeverSecret -- 允许直接查询的光环等级
local GetUnitAuraBySpellID = C_UnitAuras.GetUnitAuraBySpellID -- 查询指定光环
--[[
GetSpellAuraSecrecy(auraID) 返回 SecrecyLevel；初始化必须为 NeverSecret，否则硬 error。
GetUnitAuraBySpellID(unit, auraID) 返回 AuraData 或 nil，RequiresNonSecretAura，
SecretWhenUnitAuraRestricted；必须先检查结果是否秘密，再访问 isHarmful，秘密字段也不计数。
IsSpellInRange(spellID, unit) 返回可能秘密的 bool/nil；先检查 secret 再比较 true。
只统计普通可观察结果，不把秘密值用于比较、分支、索引或计数。
2026-09-18：按冻结版本约定查阅 @wow-ui-source 的 Interface/AddOns/
Blizzard_APIDocumentationGenerated/{UnitAuraDocumentation,SecretPredicateAPIDocumentation,
SpellDocumentation,UnitDocumentation}.lua；不重新核验已冻结的 build 差异。
Wiki 入口：https://warcraft.wiki.gg/wiki/API_C_UnitAuras.GetUnitAuraBySpellID （未取得在线说明）。
]]
--[[  variable reference  ]]
local Cell = addonTable.Cell -- 灰度显示消费者
local UIInitFuncs = addonTable.UIInitFuncs -- 布局初始化入口
--[[  logical code  ]]
local POSITION_X = {{x1}} -- 冻结横坐标
local POSITION_Y = {{y1}} -- 冻结行
local SPELL_ID = {{spell_id}} -- 射程技能
local AURA_ID = {{aura_id}} -- 减益技能
local COMBAT_ONLY = {{combat_only}} -- 是否仅计战斗单位
local NAMEPLATE_LIMIT = 40 -- 扫描与编码上限
local UPDATE_INTERVAL = 1 -- 事件之外的兜底轮询
local cell
local eventFrame = CreateFrame("Frame")
local function update()
    if not cell then return end
    local count = 0
    if DoesSpellExist(SPELL_ID) then
        for index = 1, NAMEPLATE_LIMIT do
            local unit = "nameplate" .. index
            if UnitExists(unit) and UnitCanAttack("player", unit)
                and not UnitIsDeadOrGhost(unit)
                and (not COMBAT_ONLY or UnitAffectingCombat(unit)) then
                local inRange = IsSpellInRange(SPELL_ID, unit)
                if not issecretvalue(inRange) and inRange == true then
                    local aura = GetUnitAuraBySpellID(unit, AURA_ID)
                    if not issecretvalue(aura) and aura ~= nil then
                        local harmful = aura.isHarmful
                        if not issecretvalue(harmful) and harmful == true then
                            count = count + 1
                        end
                    end
                end
            end
        end
    end
    local brightness = count / NAMEPLATE_LIMIT
    cell:setCellRGBA(brightness, brightness, brightness)
end
local function initialize()
    if GetSpellAuraSecrecy(AURA_ID) ~= NeverSecret then
        error("player_range_aura_units_count: aura_id 必须为 NeverSecret，配置值=" .. AURA_ID)
    end
    cell = Cell:New({ x = POSITION_X, y = POSITION_Y })
end
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
eventFrame:RegisterEvent("NAME_PLATE_UNIT_ADDED")
eventFrame:RegisterEvent("NAME_PLATE_UNIT_REMOVED")
eventFrame:RegisterEvent("UNIT_AURA")
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)
local fastTimeElapsed = -random() -- 独立错峰，保留余量且每帧最多刷新一次
eventFrame:SetScript("OnUpdate", function(_, elapsed)
    fastTimeElapsed = fastTimeElapsed + elapsed
    if fastTimeElapsed > UPDATE_INTERVAL then
        fastTimeElapsed = fastTimeElapsed - UPDATE_INTERVAL
        update()
    end
end)
insert(UIInitFuncs, initialize)
