--[[
original: ../conditions/player_cast_progress@dev/template.lua
uuid: {{uuid}}
plugin: player_cast_progress@dev
摘要：玩家施法或通道进度。
描述：
    CreateColorCurve 黑色 0、白色 1；直接渲染颜色。Python 返回 0–100，空闲为 0.0。
    参数校验和配对解码见 condition.py；本实例使用冻结坐标，不继承旧项目分类色。
修改记录：
2026-09-15：事件统一延至下一帧刷新；统一 0.1 秒轮询写法并使用 UPDATE_INTERVAL。
2026-09-15：按已确认计划新增玩家条件插件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After                           -- 事件后延至下一帧刷新
local random = math.random                            -- 为本实例轮询生成随机错峰
local CreateFrame = CreateFrame                       -- 创建本实例事件或显示框架
local insert = table.insert                           -- 注册 UI 初始化回调
local UnitCastingInfo = UnitCastingInfo               -- 使用普通施法的非秘密哨兵及图标
local UnitChannelInfo = UnitChannelInfo               -- 使用通道的非秘密蓄力哨兵及图标
local UnitCastingDuration = UnitCastingDuration       -- 获取施法持续时间对象
local UnitChannelDuration = UnitChannelDuration       -- 获取通道持续时间对象
local issecretvalue = issecretvalue                   -- 在普通比较前辨别秘密值
local CreateColorCurve = C_CurveUtil.CreateColorCurve -- 创建黑白进度颜色曲线
local Linear = Enum.LuaCurveType.Linear               -- 按经过比例线性插值

--[[
用途与签名：UnitCastingInfo("player") 第 11 项 delayTimeMs、UnitChannelInfo("player") 第 9 项 isEmpowered 是 NeverSecret 状态哨兵；UnitCastingDuration/UnitChannelDuration("player") 返回 duration 或无值。color = duration:EvaluateElapsedPercent(curve) 接受颜色曲线并返回可能秘密的颜色。
曲线创建：curve = C_CurveUtil.CreateColorCurve()；无参数，返回 LuaColorCurveObject；SetType(Linear)、AddPoint(0, BLACK)、AddPoint(1, WHITE) 定义经过比例到颜色的映射。
限制标记：UnitCastingDuration 为 SecretReturns；施法/通道信息受 SecretWhenUnitSpellCastRestricted 限制；只比较 NeverSecret 哨兵。
业务限制：CreateColorCurve 黑色 0、白色 1；直接渲染颜色。Python 返回 0–100，空闲为 0.0。
核验日期：2026-09-15；本地 @wow-ui-source，12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：本地源码 Interface/AddOns/ 下：
    Blizzard_APIDocumentationGenerated/UnitDocumentation.lua
    Blizzard_APIDocumentationGenerated/LuaDurationObjectAPIDocumentation.lua
    Blizzard_APIDocumentationGenerated/CurveUtilDocumentation.lua
Wiki 查询入口（本次未能获取在线说明；以下链接不作为已核验网页证据）：
    https://warcraft.wiki.gg/wiki/API_UnitCastingInfo
    https://warcraft.wiki.gg/wiki/API_UnitChannelInfo
    https://warcraft.wiki.gg/wiki/API_UnitCastingDuration
    https://warcraft.wiki.gg/wiki/API_UnitChannelDuration
    https://warcraft.wiki.gg/wiki/API_C_CurveUtil.CreateColorCurve
]]

--[[  variable reference  ]]
local Cell = addonTable.Cell               -- 黑色底板及单元格显示接口
local COLOR = addonTable.COLOR             -- 本项目共享黑白及施法颜色
local UIInitFuncs = addonTable.UIInitFuncs -- 共享布局就绪后初始化本实例

--[[  logical code  ]]
local UPDATE_INTERVAL = 0.1 -- 施法进度轮询间隔
local POSITION_X = {{x1}} -- 本实例冻结的横向位置
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local UNIT_TOKEN = "player" -- 本版本固定玩家单位
local PROGRESS_MIN = 0
local PROGRESS_MAX = 1

local display
local eventFrame = CreateFrame("Frame")
local progressMode
local progressCurve = CreateColorCurve()
progressCurve:SetType(Linear)
progressCurve:AddPoint(PROGRESS_MIN, COLOR.BLACK)
progressCurve:AddPoint(PROGRESS_MAX, COLOR.WHITE)

local function updateProgress()
    if not display then return end
    local duration
    if progressMode == "casting" then
        duration = UnitCastingDuration(UNIT_TOKEN)
    elseif progressMode == "channeling" then
        duration = UnitChannelDuration(UNIT_TOKEN)
    else
        display:clearCell()
        return
    end
    if not issecretvalue(duration) and duration == nil then
        display:clearCell()
        return
    end
    display:setCell(duration:EvaluateElapsedPercent(progressCurve)) -- 不解包秘密进度用于运算
end

local function update()
    if not display then return end
    local _, _, _, _, _, _, _, _, _, _, castDelayTimeMs = UnitCastingInfo(UNIT_TOKEN)
    if castDelayTimeMs ~= nil then -- NeverSecret 哨兵，不比较施法名称或纹理
        progressMode = "casting"
        updateProgress()
        return
    end
    local _, _, _, _, _, _, _, _, isEmpowered = UnitChannelInfo(UNIT_TOKEN)
    if isEmpowered ~= nil then -- false 也是有效的普通通道哨兵
        progressMode = "channeling"
        updateProgress()
        return
    end
    progressMode = nil
    display:clearCell()
end

local function initialize()
    display = Cell:New({ x = POSITION_X, y = POSITION_Y })
    -- 进度默认黑色，等待事件或错峰刷新；先查询状态由世界事件同步。
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时同步本实例状态
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED_QUIET", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_DELAYED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_UPDATE", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_START", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_STOP", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTIBLE", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_NOT_INTERRUPTIBLE", UNIT_TOKEN)
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
