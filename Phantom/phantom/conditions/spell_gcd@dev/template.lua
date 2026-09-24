--[[
original: ../conditions/spell_gcd@dev/template.lua
uuid: {{uuid}}
plugin: spell_gcd@dev
摘要：在分配的第二行 Cell 中用分段灰度显示技能剩余冷却。

描述：
    固定读取公共冷却 61304，ignoreGCD=false；不检查玩家是否学会，不接受参数。
    通过 UIInitFuncs 创建普通 Cell，初始保持黑色，使用独立随机错峰的 0.1 秒轮询刷新。
    将剩余冷却交给颜色曲线，越接近就绪越亮；没有 duration 对象时显示黑色。

修改记录：
2026-09-15：统一 0.1 秒轮询写法并使用 UPDATE_INTERVAL。
2026-09-12：生成器条件模板 @1.0，参数校验与解码见同目录 condition.py。
2026-09-11：按解码开发前的 Lua 示例需求新增技能冷却 Cell。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]
local random = math.random -- 为本实例轮询生成随机错峰

local CreateFrame = CreateFrame                                   -- 创建独立事件与轮询框架
local CreateColor = CreateColor                                   -- 创建灰度曲线的颜色节点
local CreateColorCurve = C_CurveUtil.CreateColorCurve             -- 创建剩余冷却颜色曲线
local Linear = Enum.LuaCurveType.Linear                           -- 在相邻节点间线性插值
local GetSpellCooldownDuration = C_Spell.GetSpellCooldownDuration -- 获取可直接用于颜色求值的冷却对象
local insert = table.insert                                       -- 注册 UI 初始化函数

--[[
C_Spell.GetSpellCooldownDuration：返回技能当前冷却的 duration 对象。
来源：https://warcraft.wiki.gg/wiki/API_C_Spell.GetSpellCooldownDuration
签名：duration = C_Spell.GetSpellCooldownDuration(spellIdentifier, ignoreGCD)
参数：spellIdentifier 为技能标识，本例使用 ID；ignoreGCD 为 boolean，API 默认 false，本插件固定 false。
返回值：LuaDurationObject；源码标记 MayReturnNothing，没有对象时本例显示黑色。
限制标记：SecretArguments = "AllowedWhenTainted"。

DurationObject:EvaluateRemainingDuration：按剩余秒数对给定曲线求值。
来源：https://warcraft.wiki.gg/wiki/API_DurationObject.EvaluateRemainingDuration
签名：result = duration:EvaluateRemainingDuration(curve, modifier)
参数：curve 为 LuaCurveObjectBase，本例使用颜色曲线；modifier 默认 RealTime。
返回值：LuaCurveEvaluatedResult；本例为颜色对象，直接交给 Cell:setCell。
    输入是剩余秒数，不是百分比；本例始终传入曲线，不在 Lua 中读取或比较冷却数值。
限制标记：SecretWhenCurveSecret；SecretArguments = "AllowedWhenUntainted"。

核验日期：2026-09-12；本地 @wow-ui-source 版本：12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
API 定义：Interface/AddOns/Blizzard_APIDocumentationGenerated/ 下的
    SpellBookDocumentation.lua、SpellDocumentation.lua、LuaDurationObjectAPIDocumentation.lua。
Wiki 在线访问返回 403；说明依据用户提供的 Wiki 内容与本地源码，不声称已获取最新网页。
]]

--[[  variable reference  ]]

local Cell = addonTable.Cell               -- 复用普通 Cell 的构造和颜色接口
local COLOR = addonTable.COLOR             -- 共享黑色兜底颜色
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸和背景就绪后创建 Cell

--[[  logical code  ]]
local UPDATE_INTERVAL = 0.1 -- 刷新间隔，严格超过后每帧最多刷新一次

local GCD_SPELL_ID = 61304 -- 固定公共冷却查询，不参与候选筛选
-- 条件实例参数与位置由 Python 生成器填入。
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local POSITION_X = {{x1}} -- 本实例冻结的横向位置
local IGNORE_GCD = false                                    -- 固定包含公共冷却，不作为插件入参

local C0 = CreateColor(255 / 255, 255 / 255, 255 / 255, 1) -- 就绪时纯白
local C1 = CreateColor(155 / 255, 155 / 255, 155 / 255, 1) -- 剩余 5 秒
local C2 = CreateColor(105 / 255, 105 / 255, 105 / 255, 1) -- 剩余 30 秒
local C3 = CreateColor(55 / 255, 55 / 255, 55 / 255, 1)    -- 剩余 155 秒
local C4 = CreateColor(0 / 255, 0 / 255, 0 / 255, 1)       -- 剩余 375 秒

local remainingCurve = CreateColorCurve()                  -- 不等距节点构成整体非线性的灰度变化
remainingCurve:SetType(Linear)
remainingCurve:AddPoint(0.0, C0)
remainingCurve:AddPoint(5.0, C1)
remainingCurve:AddPoint(30.0, C2)
remainingCurve:AddPoint(155.0, C3)
remainingCurve:AddPoint(375.0, C4)

local cooldownCell                      -- 等待 UI 初始化创建的冷却 Cell
local eventFrame = CreateFrame("Frame") -- 本例独立的事件与轮询框架

local function update()
    if not cooldownCell then -- 初始化前的轮询不访问尚未创建的 Cell
        return
    end

    local remaining = GetSpellCooldownDuration(GCD_SPELL_ID, IGNORE_GCD)
    if not remaining then -- API 可以没有返回对象，此时不视为就绪
        cooldownCell:setCell(COLOR.BLACK)
        return
    end

    cooldownCell:setCell(remaining:EvaluateRemainingDuration(remainingCurve)) -- 引擎求值后直接渲染颜色
end

local function InitializeCooldownCell()
    cooldownCell = Cell:New({ x = POSITION_X, y = POSITION_Y }) -- 保持默认黑色，等待错峰首次刷新
end

local fastTimeElapsed = -random() -- 每个实例独立随机错峰
eventFrame:SetScript("OnUpdate", function(_, elapsed)
    fastTimeElapsed = fastTimeElapsed + elapsed
    if fastTimeElapsed > UPDATE_INTERVAL then
        fastTimeElapsed = fastTimeElapsed - UPDATE_INTERVAL
        update()
    end
end)
insert(UIInitFuncs, InitializeCooldownCell) -- 沿用共享布局、计数和缩放
