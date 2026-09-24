--[[
original: ../conditions/spell_overlay@dev/template.lua
uuid: {{uuid}}
plugin: spell_overlay@dev
摘要：在分配的第二行 Cell 中以黑白显示技能高亮状态。

描述：
    从候选 ID 中选择首个出现在玩家法术书中的技能，创建 Cell 后立即刷新。
    独立事件框架监听高亮显示、隐藏和法术书变化，重新查询选中技能的高亮状态。
    高亮布尔值直接交给颜色 API，true 显示白色；false 或无匹配技能时显示黑色。

修改记录：
2026-09-15：事件统一延至下一帧刷新。
2026-09-12：生成器条件模板 @1.0，参数校验与解码见同目录 condition.py。
2026-09-11：按解码开发前的 Lua 示例需求新增技能高亮 Cell。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After -- 事件后延至下一帧刷新

local CreateFrame = CreateFrame                                       -- 创建独立事件框架
local IsSpellInSpellBook = C_SpellBook.IsSpellInSpellBook             -- 查询候选技能是否在玩家法术书中
local IsSpellOverlayed = C_SpellActivationOverlay.IsSpellOverlayed    -- 查询选中技能是否高亮
local EvaluateColorFromBoolean = C_CurveUtil.EvaluateColorFromBoolean -- 将潜在秘密布尔值转为颜色
local ipairs = ipairs                                                 -- 按顺序遍历候选技能 ID
local insert = table.insert                                           -- 注册 UI 初始化函数

--[[
C_SpellBook.IsSpellInSpellBook：查询技能是否应出现在法术书中。
来源：https://warcraft.wiki.gg/wiki/API_C_SpellBook.IsSpellInSpellBook
签名：isInSpellBook = C_SpellBook.IsSpellInSpellBook(spellID, spellBank, includeOverrides)
参数：spellID 为技能 ID；spellBank 默认 Player；includeOverrides 默认 true。
返回值：非秘密 boolean；可能包含天赋光环授予的替代技能，不等同于严格的已学会状态。
限制标记：SecretArguments = "AllowedWhenUntainted"。

C_SpellActivationOverlay.IsSpellOverlayed：查询技能是否具有触发高亮边框。
来源：https://warcraft.wiki.gg/wiki/API_C_SpellActivationOverlay.IsSpellOverlayed
签名：isSpellOverlayed = C_SpellActivationOverlay.IsSpellOverlayed(spellID)
参数：spellID 为 number 技能 ID。返回值：boolean，不是颜色对象。
限制标记：SecretArguments = "AllowedWhenUntainted"；本例按潜在秘密值处理返回结果，不进行分支。

C_CurveUtil.EvaluateColorFromBoolean：把潜在秘密布尔值转为颜色。
来源：https://warcraft.wiki.gg/wiki/API_C_CurveUtil.EvaluateColorFromBoolean
签名：color = C_CurveUtil.EvaluateColorFromBoolean(boolean, valueIfTrue, valueIfFalse)
参数：boolean 为待映射值；后两个参数为 colorRGBA，本例依次传入白色和黑色。
返回值：带 ColorMixin 的 colorRGBA，直接传给 Cell:setCell。
限制标记：SecretArguments = "AllowedWhenTainted"。

核验日期：2026-09-12；本地 @wow-ui-source 版本：12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
API 定义：Interface/AddOns/Blizzard_APIDocumentationGenerated/ 下的
    SpellBookDocumentation.lua、SpellActivationOverlayDocumentation.lua、CurveUtilDocumentation.lua。
Wiki 在线访问返回 403；说明依据用户提供的 Wiki 内容与本地源码，不声称已获取最新网页。
]]

--[[  variable reference  ]]

local Cell = addonTable.Cell               -- 复用普通 Cell 的构造和颜色接口
local COLOR = addonTable.COLOR             -- 共享黑白颜色
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸和背景就绪后创建 Cell

--[[  logical code  ]]

-- 条件实例参数与位置由 Python 生成器填入。
local SPELL_IDS = { {{spell_ids}} }      -- 按优先顺序排列的候选技能 ID
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local POSITION_X = {{x1}} -- 本实例冻结的横向位置

local overlayCell                       -- 等待 UI 初始化创建的高亮 Cell
local selectedSpellID                   -- 当前选中的首个法术书技能 ID
local eventFrame = CreateFrame("Frame") -- 本例独立的高亮与法术书事件框架

local function SelectSpell()
    selectedSpellID = nil                   -- 清除旧选择，允许全部候选移出法术书
    for _, spellID in ipairs(SPELL_IDS) do
        if IsSpellInSpellBook(spellID) then -- 法术书查询返回非秘密布尔值
            selectedSpellID = spellID
            return                          -- 首个匹配优先
        end
    end
end

local function update()
    if not overlayCell then -- 初始化前的事件不访问尚未创建的 Cell
        return
    end

    if not selectedSpellID then -- 没有任何匹配技能时显示黑色
        overlayCell:setCell(COLOR.BLACK)
        return
    end

    local isOverlayed = IsSpellOverlayed(selectedSpellID) -- 不读取事件中的技能 ID，也不对高亮结果分支
    local color = EvaluateColorFromBoolean(isOverlayed, COLOR.WHITE, COLOR.BLACK)
    overlayCell:setCell(color)                            -- 直接渲染颜色对象
end

local function InitializeOverlayCell()
    overlayCell = Cell:New({ x = POSITION_X, y = POSITION_Y })
    SelectSpell()        -- 初始化时读取当前法术书
    update() -- 立即补齐已有高亮状态
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")              -- 首次进入世界时刷新当前状态
eventFrame:RegisterEvent("SPELL_ACTIVATION_OVERLAY_GLOW_SHOW") -- 高亮出现时重新查询
eventFrame:RegisterEvent("SPELL_ACTIVATION_OVERLAY_GLOW_HIDE") -- 高亮消失时重新查询
eventFrame:RegisterEvent("SPELLS_CHANGED")                     -- 法术书变化时重新选择并刷新
eventFrame:SetScript("OnEvent", function(_, event)
    After(0, function()
        if event == "SPELLS_CHANGED" then                          -- 只比较事件名称，不检查事件负载
            SelectSpell()
        end
        update()
    end)
end)
insert(UIInitFuncs, InitializeOverlayCell) -- 沿用共享布局、计数和缩放
