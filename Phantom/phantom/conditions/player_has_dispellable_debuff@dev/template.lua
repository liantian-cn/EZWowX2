--[[
original: ../conditions/player_has_dispellable_debuff@dev/template.lua
uuid: {{uuid}}
plugin: player_has_dispellable_debuff@dev
摘要：玩家是否有指定类型可驱散减益。
描述：
    同时要求玩家可驱散与类型匹配；空表或全 false 匹配不到任何减益。不读取秘密 AuraData。
    参数校验和配对解码见 condition.py；本实例使用冻结坐标，不继承旧项目分类色。
修改记录：
2026-09-20：直接使用 CellBackplate 提供固定黑底与行宽登记。
2026-09-15：事件统一延至下一帧刷新。
2026-09-15：按已确认计划新增玩家条件插件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After     -- 事件后延至下一帧刷新
local CreateFrame = CreateFrame -- 创建本实例事件或显示框架
local insert = table.insert     -- 注册 UI 初始化回调

--[[
用途与签名：AuraContainer:AddAuraSlot(key, "HARMFUL|RAID_PLAYER_DISPELLABLE", options)；options.candidateFilters.includeDispelTypes 为类型布尔映射，容器管理显示；UpdateAllAuras() 请求刷新。
业务限制：同时要求玩家可驱散与类型匹配；空表或全 false 匹配不到任何减益。不读取秘密 AuraData。
核验日期：2026-09-15；本地 @wow-ui-source，12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：本地源码 Interface/AddOns/ 下：
    Blizzard_AuraContainer/Blizzard_CustomAuraContainer.lua
    Blizzard_AuraContainer/Blizzard_AuraContainer.lua
    Blizzard_AuraContainer/Blizzard_ManagedAuraContainer.lua
    Blizzard_AuraContainer/Blizzard_AuraContainerUtil.lua
辅助签名：container:SetUnit("player") 无返回值；container:UpdateAllAuras() 无返回值。
初始化回调只设置静态框体/纹理；不访问后续受限制的 AuraButton 状态。
Wiki 对该容器的说明未获取；此处以指定 revision 的官方实现为准。

]]

--[[  variable reference  ]]
local CellBackplate = addonTable.CellBackplate -- 固定黑色背板
local COLOR = addonTable.COLOR             -- 本项目共享黑白及施法颜色
local SIZE = addonTable.SIZE               -- 共享 Cell 尺寸
local FrameLevel = addonTable.FrameLevel   -- 共享底板和光环显示层级
local UIInitFuncs = addonTable.UIInitFuncs -- 共享布局就绪后初始化本实例

--[[  logical code  ]]
local POSITION_X = {{x1}}             -- 本实例冻结的横向位置
local POSITION_Y = {{y1}}             -- 本实例冻结的 Cell 行
local UNIT_TOKEN = "player"               -- 本版本固定玩家单位
local SLOT_KEY = "aura"                   -- 容器独立，因此固定键不会跨实例冲突
local AURA_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_full.tga"
local DISPEL_TYPES = { {{dispel_types}} } -- 空表也保留，表示全部排除
local AURA_FILTER = "HARMFUL|RAID_PLAYER_DISPELLABLE"

local container
local eventFrame = CreateFrame("Frame")

local function update()
    if container then container:UpdateAllAuras() end -- 官方公开刷新入口，不检查受管数据
end

local function initialize()
    local backing = CellBackplate:New({ x = POSITION_X, y = POSITION_Y })
    container = CreateFrame("AuraContainer", nil, backing.Frame, "CustomAuraContainerTemplate")
    container:SetAllPoints(backing.Frame)
    container:SetFrameLevel(FrameLevel.AuraContainer)
    container:SetUnit(UNIT_TOKEN)
    container:AddAuraSlot(SLOT_KEY, AURA_FILTER, {
        candidateFilters = { includeDispelTypes = DISPEL_TYPES },
        initializeFrame = function(frame)
            frame:SetSize(SIZE.CELL, SIZE.CELL)
            frame:SetPoint("TOPLEFT", container, "TOPLEFT")
            frame:SetFrameLevel(FrameLevel.AuraButton)
            frame.ActiveOverlay = frame:CreateTexture(nil, "OVERLAY")
            frame.ActiveOverlay:SetAllPoints(frame)
            frame.ActiveOverlay:SetTexture(AURA_TEXTURE)
            frame.ActiveOverlay:SetVertexColor(COLOR.WHITE:GetRGBA()) -- 静态白色覆盖，显示由容器负责
        end,
    })
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD") -- 进入世界时同步本实例状态
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)
insert(UIInitFuncs, initialize)
