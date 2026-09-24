--[[
original: ../conditions/player_trinket_ready@dev/template.lua
uuid: {{uuid}}
plugin: player_trinket_ready@dev
摘要：玩家饰品是否准备就绪。
描述：
    所选位置有物品、enabled 为真、duration 为零、usable 为真且 noMana 为假；不另查数量。
    参数校验和配对解码见 condition.py；本实例使用冻结坐标，不继承旧项目分类色。
修改记录：
2026-09-15：事件统一延至下一帧刷新；兜底轮询统一为 1 秒并使用 UPDATE_INTERVAL。
2026-09-15：按已确认计划新增玩家条件插件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After                    -- 事件后延至下一帧刷新
local random = math.random                     -- 为本实例轮询生成随机错峰
local CreateFrame = CreateFrame                -- 创建本实例事件或显示框架
local insert = table.insert                    -- 注册 UI 初始化回调
local GetItemCooldown = C_Item.GetItemCooldown -- 查询物品冷却状态
local IsUsableItem = C_Item.IsUsableItem       -- 查询物品可用性及资源限制
local GetInventoryItemID = GetInventoryItemID  -- 获取所选装备位置的物品

--[[
用途与签名：itemID = GetInventoryItemID("player", slotID)；返回物品 ID 或 nil。start, duration, enabled = C_Item.GetItemCooldown(itemID)；usable, noMana = C_Item.IsUsableItem(itemID)。
业务限制：所选位置有物品、enabled 为真、duration 为零、usable 为真且 noMana 为假；不另查数量。
核验日期：2026-09-15；本地 @wow-ui-source，12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：本地源码 Interface/AddOns/ 下：
    Blizzard_APIDocumentationGenerated/ItemDocumentation.lua
    Blizzard_FrameXML/Mainline/EquipmentManager.lua
Wiki 查询入口（本次未能获取在线说明；以下链接不作为已核验网页证据）：
    https://warcraft.wiki.gg/wiki/API_C_Item.GetItemCooldown
    https://warcraft.wiki.gg/wiki/API_C_Item.IsUsableItem
    https://warcraft.wiki.gg/wiki/API_GetInventoryItemID
]]

--[[  variable reference  ]]
local Cell = addonTable.Cell               -- 黑色底板及单元格显示接口
local UIInitFuncs = addonTable.UIInitFuncs -- 共享布局就绪后初始化本实例

--[[  logical code  ]]
local UPDATE_INTERVAL = 1   -- 事件之外的兜底刷新间隔
local POSITION_X = {{x1}} -- 本实例冻结的横向位置
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local UNIT_TOKEN = "player" -- 本版本固定玩家单位
local SLOT_ID = {{slot_id}} -- 仅查询该饰品位置

local cell
local eventFrame = CreateFrame("Frame")

local function update()
    if not cell then return end -- UI 初始化之前不访问显示对象
    local itemID = GetInventoryItemID(UNIT_TOKEN, SLOT_ID)
    if itemID == nil then
        cell:clearCell()
        return
    end
    local _, duration, enabled = GetItemCooldown(itemID)
    local usable, noMana = IsUsableItem(itemID)
    cell:setCellBoolean(enabled and duration == 0 and usable and not noMana)
end

local function initialize()
    cell = Cell:New({ x = POSITION_X, y = POSITION_Y }) -- 黑底等待事件或错峰首次刷新
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时同步本实例状态
eventFrame:RegisterEvent("PLAYER_EQUIPMENT_CHANGED")
eventFrame:RegisterEvent("BAG_UPDATE_COOLDOWN")
eventFrame:RegisterEvent("SPELL_UPDATE_COOLDOWN")
eventFrame:SetScript("OnEvent", function(_, event, equipmentSlot)
    After(0, function()
        if event == "PLAYER_EQUIPMENT_CHANGED" and equipmentSlot ~= SLOT_ID then return end
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

insert(UIInitFuncs, initialize)
