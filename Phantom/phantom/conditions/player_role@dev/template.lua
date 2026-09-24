--[[
original: ../conditions/player_role@dev/template.lua
uuid: {{uuid}}
plugin: player_role@dev
摘要：玩家职责。
描述：
    NONE/TANK/HEALER/DAMAGER 对应灰度字节 0/85/170/255；秘密职责显示 NONE。
    参数校验和配对解码见 condition.py；本实例使用冻结坐标，不继承旧项目分类色。
修改记录：
2026-09-15：事件统一延至下一帧刷新；兜底轮询统一为 1 秒并使用 UPDATE_INTERVAL。
2026-09-15：按已确认计划新增玩家条件插件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After                           -- 事件后延至下一帧刷新
local random = math.random                            -- 为本实例轮询生成随机错峰
local CreateFrame = CreateFrame                       -- 创建本实例事件或显示框架
local insert = table.insert                           -- 注册 UI 初始化回调
local UnitGroupRolesAssigned = UnitGroupRolesAssigned -- 查询玩家职责
local issecretvalue = issecretvalue                   -- 在普通比较前辨别秘密值

--[[
用途与签名：role = UnitGroupRolesAssigned("player")；返回职责字符串，单位身份受限时可能秘密。
业务限制：NONE/TANK/HEALER/DAMAGER 对应灰度字节 0/85/170/255；秘密职责显示 NONE。
核验日期：2026-09-15；本地 @wow-ui-source，12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：本地源码 Interface/AddOns/ 下：
    Blizzard_APIDocumentationGenerated/UnitDocumentation.lua
Wiki 查询入口（本次未能获取在线说明；以下链接不作为已核验网页证据）：
    https://warcraft.wiki.gg/wiki/API_UnitGroupRolesAssigned
]]

--[[  variable reference  ]]
local Cell = addonTable.Cell               -- 黑色底板及单元格显示接口
local UIInitFuncs = addonTable.UIInitFuncs -- 共享布局就绪后初始化本实例

--[[  logical code  ]]
local UPDATE_INTERVAL = 1   -- 事件之外的兜底刷新间隔
local POSITION_X = {{x1}} -- 本实例冻结的横向位置
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local UNIT_TOKEN = "player" -- 本版本固定玩家单位
local ROLE_TANK = 85 / 255
local ROLE_HEALER = 170 / 255
local ROLE_DAMAGER = 1

local cell
local eventFrame = CreateFrame("Frame")

local function update()
    if not cell then return end -- UI 初始化之前不访问显示对象
    local role = UnitGroupRolesAssigned(UNIT_TOKEN)
    local value = 0
    if not issecretvalue(role) then -- 只有普通职责字符串可以比较
        if role == "TANK" then
            value = ROLE_TANK
        elseif role == "HEALER" then
            value = ROLE_HEALER
        elseif role == "DAMAGER" then
            value = ROLE_DAMAGER
        end
    end
    cell:setCellRGBA(value, value, value)
end

local function initialize()
    cell = Cell:New({ x = POSITION_X, y = POSITION_Y }) -- 黑底等待事件或错峰首次刷新
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时同步本实例状态
eventFrame:RegisterEvent("PLAYER_ROLES_ASSIGNED")
eventFrame:RegisterEvent("ROLE_CHANGED_INFORM")
eventFrame:RegisterEvent("GROUP_ROSTER_UPDATE")
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
