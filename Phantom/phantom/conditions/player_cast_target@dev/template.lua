--[[
original: ../conditions/player_cast_target@dev/template.lua
uuid: {{uuid}}
plugin: player_cast_target@dev
摘要：玩家施法目标。
描述：
    匹配 player、party1–4、raid1–40；秘密目标暂留旧值，成功/停止/失败与每秒兜底清空，长施法可能提前清空。编码 0 未知、1 玩家、2–5 队员、6–45 团员，各乘 5。
    参数校验和配对解码见 condition.py；本实例使用冻结坐标，不继承旧项目分类色。
修改记录：
2026-09-15：事件统一延至下一帧刷新；兜底轮询统一为 1 秒并使用 UPDATE_INTERVAL。
2026-09-15：按已确认计划新增玩家条件插件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After         -- 事件后延至下一帧刷新
local random = math.random          -- 为本实例轮询生成随机错峰
local CreateFrame = CreateFrame     -- 创建本实例事件或显示框架
local insert = table.insert         -- 注册 UI 初始化回调
local UnitName = UnitName           -- 查询目标候选单位名称
local UnitExists = UnitExists       -- 查询候选单位存在性
local issecretvalue = issecretvalue -- 在普通比较前辨别秘密值

--[[
用途与签名：UNIT_SPELLCAST_SENT(unit, targetName, castGUID, spellID) 提供可能秘密的目标名；UnitName(unit) 返回可能秘密的单位名。UnitExists(unit) 检查候选单位。
业务限制：匹配 player、party1–4、raid1–40；秘密目标暂留旧值，成功/停止/失败与每秒兜底清空，长施法可能提前清空。编码 0 未知、1 玩家、2–5 队员、6–45 团员，各乘 5。
核验日期：2026-09-15；本地 @wow-ui-source，12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：本地源码 Interface/AddOns/ 下：
    Blizzard_APIDocumentationGenerated/UnitDocumentation.lua
Wiki 查询入口（本次未能获取在线说明；以下链接不作为已核验网页证据）：
    https://warcraft.wiki.gg/wiki/API_UnitName
    https://warcraft.wiki.gg/wiki/API_UnitExists
]]

--[[  variable reference  ]]
local Cell = addonTable.Cell               -- 黑色底板及单元格显示接口
local UIInitFuncs = addonTable.UIInitFuncs -- 共享布局就绪后初始化本实例

--[[  logical code  ]]
local UPDATE_INTERVAL = 1   -- 事件之外的兜底刷新间隔
local POSITION_X = {{x1}} -- 本实例冻结的横向位置
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local UNIT_TOKEN = "player" -- 本版本固定玩家单位
local TARGET_STEP = 5       -- 每个目标编码占五个灰度字节
local PARTY_LIMIT = 4
local RAID_LIMIT = 40
local RAID_CODE_OFFSET = 5

local cell
local eventFrame = CreateFrame("Frame")

local function update()
    if cell then cell:clearCell() end
end

local function setTarget(code)
    local value = code * TARGET_STEP / 255
    cell:setCellRGBA(value, value, value)
end

local function matches(unit, targetName)
    if not UnitExists(unit) then return false end
    local unitName = UnitName(unit)
    return not issecretvalue(unitName) and unitName ~= nil and unitName == targetName
end

local function setCastTarget(targetName)
    if not cell or issecretvalue(targetName) then return end -- 秘密目标保留上次值直到清理
    if targetName == nil then
        update(); return
    end
    if matches(UNIT_TOKEN, targetName) then
        setTarget(1); return
    end
    for index = 1, PARTY_LIMIT do
        if matches("party" .. index, targetName) then
            setTarget(index + 1); return
        end
    end
    for index = 1, RAID_LIMIT do
        if matches("raid" .. index, targetName) then
            setTarget(index + RAID_CODE_OFFSET); return
        end
    end
    update()
end

local function initialize()
    cell = Cell:New({ x = POSITION_X, y = POSITION_Y }) -- 黑色表示没有可报告目标
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时同步本实例状态
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SENT", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED_QUIET", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function(_, event, _, targetName)
    After(0, function()
        if event == "UNIT_SPELLCAST_SENT" then
            setCastTarget(targetName)
        else
            update()
        end
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
