--[[
original: ../conditions/item_cooldown_ready@dev/template.lua
uuid: {{uuid}}
摘要：指定物品的库存与冷却就绪状态。
描述：只查询本实例 item_id，非银行库存大于零、有效启用冷却已结束时显示白色。
      不增加可用性或资源检查；普通返回无效或 API 异常时表示未确认就绪。
修改记录：2026-09-19：新增通用单物品冷却就绪条件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建事件框架
local After = C_Timer.After -- 事件下一帧刷新
local GetItemCount = C_Item.GetItemCount -- 查询非银行库存数量
local GetItemCooldown = C_Item.GetItemCooldown -- 查询冷却起点、总长和启用状态
local GetTime = GetTime -- 当前游戏时间，与冷却起点使用相同时间基准
local type = type -- 校验普通返回类型
local pcall = pcall -- API 异常归为未确认就绪
local huge = math.huge -- 拒绝无穷数值
local random = math.random -- 轮询随机错峰
local insert = table.insert -- 注册共享布局初始化
--[[
count = C_Item.GetItemCount(itemInfo, includeBank, includeUses, includeReagentBank, includeAccountBank)。
本实例 itemInfo 为配置的公开正整数 ID，其余四项均 false，不计银行或物品使用次数。
start, duration, enabled = C_Item.GetItemCooldown(itemInfo) 返回 number、number、bool。
仅 count > 0、enabled 为 true 且有效冷却没有剩余时间时就绪；不调用 IsUsableItem。
两个 API 的 SecretArguments = "AllowedWhenUntainted" 是参数秘密性元数据，不是返回值标记。
当前定义未标记秘密返回；本插件仅使用静态公开 ID 的已核验普通返回路径，不检测或转换秘密返回。
普通类型、有限非负数值检查和 pcall 仅处理该路径中的无效数据及 API 异常。
核验：2026-09-19，12.1.0.69587，revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
源码：Interface/AddOns/Blizzard_APIDocumentationGenerated/ItemDocumentation.lua:412-445。
Wiki（2026-09-19 获取）：
https://warcraft.wiki.gg/wiki/API:C_Item.GetItemCooldown?oldid=6853498
https://warcraft.wiki.gg/wiki/API:C_Item.GetItemCount?oldid=6811783
]]

--[[  variable reference  ]]
local Cell = addonTable.Cell -- 严格黑白显示
local UIInitFuncs = addonTable.UIInitFuncs -- 共享布局初始化队列

--[[  logical code  ]]
local POSITION_X = {{x1}}
local POSITION_Y = {{y1}}
local ITEM_ID = {{item_id}} -- 本实例唯一的公开物品 ID
local UPDATE_INTERVAL = 1 -- 事件之外的低频兜底
local cell
local eventFrame = CreateFrame("Frame")

local function isNonNegativeNumber(value)
    return type(value) == "number" and value == value and value >= 0 and value < huge
end

local function isReady()
    local count = GetItemCount(ITEM_ID, false, false, false, false)
    if not isNonNegativeNumber(count) or count <= 0 then return false end
    local start, duration, enabled = GetItemCooldown(ITEM_ID)
    if type(enabled) ~= "boolean" or not enabled then return false end
    if not isNonNegativeNumber(start) or not isNonNegativeNumber(duration) then return false end
    local now = GetTime()
    if not isNonNegativeNumber(now) then return false end
    return duration == 0 or start + duration <= now -- 不对剩余秒数舍入
end

local function update()
    if not cell then return end
    local ok, ready = pcall(isReady)
    cell:setCellBoolean(ok and ready) -- 异常时也覆盖旧的就绪像素
end

local function initialize()
    cell = Cell:New({ x = POSITION_X, y = POSITION_Y })
    update()
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
eventFrame:RegisterEvent("BAG_UPDATE")
eventFrame:RegisterEvent("BAG_UPDATE_COOLDOWN")
eventFrame:RegisterEvent("SPELL_UPDATE_COOLDOWN")
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
