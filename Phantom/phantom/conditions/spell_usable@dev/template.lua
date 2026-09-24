--[[
original: ../conditions/spell_usable@dev/template.lua
uuid: {{uuid}}
plugin: spell_usable@dev
摘要：在分配的第二行 Cell 中以黑白显示技能可用状态。

描述：
    从候选 ID 中选择首个出现在玩家法术书中的技能，在 SPELLS_CHANGED 时重新选择。
    创建 Cell 后保持黑色，独立随机错峰的 0.1 秒轮询查询技能可用性。
    将 isUsable 直接映射为白色或黑色；全部候选不匹配时显示黑色。

修改记录：
2026-09-15：事件统一延至下一帧刷新；统一 0.1 秒轮询写法并使用 UPDATE_INTERVAL。
2026-09-12：生成器条件模板 @1.0，参数校验与解码见同目录 condition.py。
2026-09-11：按解码开发前的 Lua 示例需求新增技能可用 Cell。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After -- 事件后延至下一帧刷新
local random = math.random -- 为本实例轮询生成随机错峰

local CreateFrame = CreateFrame                                       -- 创建独立事件与轮询框架
local IsSpellInSpellBook = C_SpellBook.IsSpellInSpellBook             -- 查询候选技能是否在玩家法术书中
local IsSpellUsable = C_Spell.IsSpellUsable                           -- 查询选中技能是否可用
local EvaluateColorFromBoolean = C_CurveUtil.EvaluateColorFromBoolean -- 将潜在秘密布尔值转为颜色
local ipairs = ipairs                                                 -- 按给定顺序选择候选技能
local insert = table.insert                                           -- 注册 UI 初始化函数

--[[
C_SpellBook.IsSpellInSpellBook：查询技能是否应出现在法术书中。
来源：https://warcraft.wiki.gg/wiki/API_C_SpellBook.IsSpellInSpellBook
签名：isInSpellBook = C_SpellBook.IsSpellInSpellBook(spellID, spellBank, includeOverrides)
参数：spellID 为技能 ID；spellBank 默认 Player；includeOverrides 默认 true。
返回值：非秘密 boolean；可能包含天赋光环授予的替代技能，不等同于严格的已学会状态。
限制标记：SecretArguments = "AllowedWhenUntainted"。

C_Spell.IsSpellUsable：查询技能是否满足可用条件。
来源：https://warcraft.wiki.gg/wiki/API_C_Spell.IsSpellUsable
签名：isUsable, insufficientPower = C_Spell.IsSpellUsable(spellIdentifier)
参数：spellIdentifier 为技能 ID、名称、带副标题的名称或链接，本例使用 ID。
返回值：isUsable 为技能是否可用的 boolean；insufficientPower 为是否因资源不足而不可用的 boolean。
    未学会、缺少资源或材料、触发条件不满足等都可能导致不可用。本例仅消费第一个返回值，
    不把资源不足独立编码，也不把这个结果扩展为冷却、距离等全部施法条件的综合判断。
限制标记：SecretArguments = "AllowedWhenTainted"；本例按潜在秘密值处理 isUsable，不进行分支。

C_CurveUtil.EvaluateColorFromBoolean：把潜在秘密布尔值转为颜色。
来源：https://warcraft.wiki.gg/wiki/API_C_CurveUtil.EvaluateColorFromBoolean
签名：color = C_CurveUtil.EvaluateColorFromBoolean(boolean, valueIfTrue, valueIfFalse)
参数：boolean 为待映射值；后两个参数为 colorRGBA，本例依次传入白色和黑色。
返回值：带 ColorMixin 的 colorRGBA，直接传给 Cell:setCell。
限制标记：SecretArguments = "AllowedWhenTainted"。

核验日期：2026-09-12；本地 @wow-ui-source 版本：12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
API 定义：Interface/AddOns/Blizzard_APIDocumentationGenerated/ 下的
    SpellBookDocumentation.lua、SpellDocumentation.lua、CurveUtilDocumentation.lua。
Wiki 在线访问返回 403；说明依据用户提供的 Wiki 内容与本地源码，不声称已获取最新网页。
]]

--[[  variable reference  ]]

local Cell = addonTable.Cell               -- 复用普通 Cell 的构造和颜色接口
local COLOR = addonTable.COLOR             -- 共享黑白颜色
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸和背景就绪后创建 Cell

--[[  logical code  ]]
local UPDATE_INTERVAL = 0.1 -- 刷新间隔，严格超过后每帧最多刷新一次

-- 条件实例参数与位置由 Python 生成器填入。
local SPELL_IDS = { {{spell_ids}} }      -- 按优先顺序排列的候选技能 ID
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local POSITION_X = {{x1}} -- 本实例冻结的横向位置

local usableCell                        -- 等待 UI 初始化创建的可用状态 Cell
local selectedSpellID                   -- 当前选中的首个法术书技能 ID
local eventFrame = CreateFrame("Frame") -- 本例独立的事件与轮询框架

local function SelectSpell()
    selectedSpellID = nil                   -- 清除旧选择，允许全部候选移出法术书
    for _, spellID in ipairs(SPELL_IDS) do
        if IsSpellInSpellBook(spellID) then -- 法术书查询返回非秘密布尔值
            selectedSpellID = spellID
            return                          -- 首个匹配优先，不合并其他候选的可用状态
        end
    end
end

local function update()
    if not usableCell then -- 初始化前的轮询不访问尚未创建的 Cell
        return
    end

    if not selectedSpellID then -- 没有任何匹配技能时显示黑色
        usableCell:setCell(COLOR.BLACK)
        return
    end

    local isUsable = IsSpellUsable(selectedSpellID) -- 仅取可用性，不单独处理 insufficientPower
    local color = EvaluateColorFromBoolean(isUsable, COLOR.WHITE, COLOR.BLACK)
    usableCell:setCell(color)                       -- 直接渲染颜色对象，不对可用性布尔值分支
end

local function InitializeUsableCell()
    usableCell = Cell:New({ x = POSITION_X, y = POSITION_Y }) -- 保持默认黑色，等待错峰首次刷新
    SelectSpell()                                             -- 初始化时读取当前法术书
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 首次进入世界时刷新当前状态
eventFrame:RegisterEvent("SPELLS_CHANGED")        -- 法术书变化时重新选择候选技能
eventFrame:SetScript("OnEvent", function()
    After(0, function()
        SelectSpell()
        update()
    end)
end)
local fastTimeElapsed = -random() -- 每个实例独立随机错峰
eventFrame:SetScript("OnUpdate", function(_, elapsed)
    fastTimeElapsed = fastTimeElapsed + elapsed
    if fastTimeElapsed > UPDATE_INTERVAL then
        fastTimeElapsed = fastTimeElapsed - UPDATE_INTERVAL
        update()
    end
end)
insert(UIInitFuncs, InitializeUsableCell) -- 沿用共享布局、计数和缩放
