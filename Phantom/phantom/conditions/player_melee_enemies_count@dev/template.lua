--[[
original: ../conditions/player_melee_enemies_count@dev/template.lua
uuid: {{uuid}}
plugin: player_melee_enemies_count@dev
摘要：玩家近战范围敌人数量。
描述：
    有效技能才扫描 nameplate1–40 中存在、可攻击、非死亡且符合战斗选项的单位。
    秘密或 nil 距离结果不计数，只报告可观察单位；灰度 count/40，Python 四舍五入至 0–40。
    参数校验和配对解码见 condition.py；本实例使用冻结坐标，不继承旧项目分类色。
修改记录：
2026-09-18：新增 combat_only、技能有效性和非死亡筛选。
2026-09-15：事件统一延至下一帧刷新；兜底轮询统一为 1 秒并使用 UPDATE_INTERVAL。
2026-09-15：按已确认计划新增玩家条件插件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After                   -- 事件后延至下一帧刷新
local random = math.random                    -- 为本实例轮询生成随机错峰
local CreateFrame = CreateFrame               -- 创建本实例事件或显示框架
local insert = table.insert                   -- 注册 UI 初始化回调
local IsSpellInRange = C_Spell.IsSpellInRange -- 查询技能对单位的距离状态
local DoesSpellExist = C_Spell.DoesSpellExist -- 无效技能直接显示零
local issecretvalue = issecretvalue           -- 在普通比较前辨别秘密值
local UnitExists = UnitExists                 -- 查询候选单位存在性
local UnitCanAttack = UnitCanAttack           -- 判断候选单位是否可攻击
local UnitIsDeadOrGhost = UnitIsDeadOrGhost -- 排除死亡或灵魂单位
local UnitAffectingCombat = UnitAffectingCombat -- 可选战斗状态筛选

--[[
用途与签名：inRange = C_Spell.IsSpellInRange(spellID, unitToken)；返回 bool 或 nil，可能秘密。UnitExists(unit)、UnitCanAttack("player", unit) 返回存在及可攻击布尔值。
DoesSpellExist(spellID) 验证技能；UnitIsDeadOrGhost(unit) 排除死亡，combat_only 时要求 UnitAffectingCombat(unit)。
业务限制：扫描 nameplate1–40；秘密或 nil 距离结果不计数。灰度 count/40，Python 四舍五入至 0–40。
核验日期：2026-09-15；本地 @wow-ui-source，12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：本地源码 Interface/AddOns/ 下：
    Blizzard_APIDocumentationGenerated/SpellDocumentation.lua
    Blizzard_APIDocumentationGenerated/UnitDocumentation.lua
Wiki 查询入口（本次未能获取在线说明；以下链接不作为已核验网页证据）：
    https://warcraft.wiki.gg/wiki/API_C_Spell.IsSpellInRange
    https://warcraft.wiki.gg/wiki/API_UnitExists
    https://warcraft.wiki.gg/wiki/API_UnitCanAttack
]]

--[[  variable reference  ]]
local Cell = addonTable.Cell               -- 黑色底板及单元格显示接口
local UIInitFuncs = addonTable.UIInitFuncs -- 共享布局就绪后初始化本实例

--[[  logical code  ]]
local UPDATE_INTERVAL = 1     -- 事件之外的兜底刷新间隔
local POSITION_X = {{x1}} -- 本实例冻结的横向位置
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local UNIT_TOKEN = "player"   -- 本版本固定玩家单位
local SPELL_ID = {{spell_id}} -- 用于判定近战范围的技能
local COMBAT_ONLY = {{combat_only}} -- 仅统计战斗中的候选单位
local NAMEPLATE_LIMIT = 40    -- 只统计这组姓名板

local cell
local eventFrame = CreateFrame("Frame")

local function update()
    if not cell then return end -- UI 初始化之前不访问显示对象
    if not DoesSpellExist(SPELL_ID) then
        cell:setCellRGBA(0, 0, 0)
        return
    end
    local count = 0
    for index = 1, NAMEPLATE_LIMIT do
        local unit = "nameplate" .. index
        if UnitExists(unit)
            and UnitCanAttack(UNIT_TOKEN, unit)
            and not UnitIsDeadOrGhost(unit)
            and (not COMBAT_ONLY or UnitAffectingCombat(unit))
        then
            local inRange = IsSpellInRange(SPELL_ID, unit)
            if not issecretvalue(inRange) and inRange == true then
                count = count + 1
            end
        end
    end
    local value = count / NAMEPLATE_LIMIT
    cell:setCellRGBA(value, value, value)
end

local function initialize()
    cell = Cell:New({ x = POSITION_X, y = POSITION_Y }) -- 黑底等待事件或错峰首次刷新
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时同步本实例状态
eventFrame:RegisterEvent("NAME_PLATE_UNIT_ADDED")
eventFrame:RegisterEvent("NAME_PLATE_UNIT_REMOVED")
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)

local fastTimeElapsed = -random() -- 每个实例独立随机错峰
eventFrame:SetScript("OnUpdate", function(_, elapsed)
    fastTimeElapsed = fastTimeElapsed + elapsed
    if fastTimeElapsed > UPDATE_INTERVAL then
        fastTimeElapsed = fastTimeElapsed - UPDATE_INTERVAL
        update()
    end
end)

insert(UIInitFuncs, initialize)
