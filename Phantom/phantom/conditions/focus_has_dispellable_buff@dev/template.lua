--[[
original: ../conditions/focus_has_dispellable_buff@dev/template.lua
uuid: {{uuid}}
摘要：敌人焦点的指定增益存在状态。
描述：单 AuraSlot 按驱散类型首匹配；白色覆盖黑底，不读取光环数据或显示状态。
修改记录：
2026-09-20：直接使用 CellBackplate 提供固定黑底与行宽登记。
2026-09-18：按冻结约定新增。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建容器与事件框架
local After = C_Timer.After -- 事件延后下一帧
local UnitExists = UnitExists -- 排除无单位
local UnitIsEnemy = UnitIsEnemy -- 按光环身份规则分类
local insert = table.insert -- 注册初始化
--[[
2026-09-18 核验本地 12.1.0.69587 源码；未运行实际客户端。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：Interface/AddOns/Blizzard_AuraContainer/Blizzard_CustomAuraContainer.lua、Blizzard_AuraContainerUtil.lua；
Interface/AddOns/Blizzard_FrameXMLUtil/AuraUtil.lua 的 Player、RaidPlayerDispellable 注释。
AddAuraSlot(key, filter, options) 创建官方首匹配槽；candidateFilters.includeDispelTypes 为类型布尔映射，空表或全 false 不匹配。
RAID_PLAYER_DISPELLABLE 表示团队有人能驱散；Enrage 的实际 dispelName 键无本地证据，游戏待验。
UnitIsEnemy("player", unit) 返回敌对关系布尔值，只有敌人侧显示增益，不等同于 UnitCanAttack。
初始化回调仅布置静态纹理，秘密光环筛选及槽显示由官方管理。
Wiki：https://warcraft.wiki.gg/wiki/API_UnitIsEnemy；2026-09-18 已获取页面；AuraContainer 筛选说明来自目标 build 源码。
]]
--[[  variable reference  ]]
local CellBackplate = addonTable.CellBackplate -- 固定黑色背板
local SIZE = addonTable.SIZE -- 固定像素尺寸
local COLOR = addonTable.COLOR -- 黑白颜色
local FrameLevel = addonTable.FrameLevel -- 显示层级
local UIInitFuncs = addonTable.UIInitFuncs -- 延迟初始化
--[[  logical code  ]]
local POSITION_X = {{x1}}
local POSITION_Y = {{y1}}
local DISPEL_TYPES = { {{dispel_types}} }
local UNIT_TOKEN = "focus"
local AURA_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_full.tga"
local container
local eventFrame = CreateFrame("Frame")
local function update()
    if not container then return end
    container:SetShown(UnitExists(UNIT_TOKEN) and UnitIsEnemy("player", UNIT_TOKEN))
    container:UpdateAllAuras()
end
local function initialize()
    local backing = CellBackplate:New({ x = POSITION_X, y = POSITION_Y })
    container = CreateFrame("AuraContainer", nil, backing.Frame, "CustomAuraContainerTemplate")
    container:SetAllPoints(backing.Frame)
    container:SetFrameLevel(FrameLevel.AuraContainer)
    container:SetUnit(UNIT_TOKEN)
    container:AddAuraSlot("aura", "HELPFUL|RAID_PLAYER_DISPELLABLE", {
        candidateFilters = { includeDispelTypes = DISPEL_TYPES },
        initializeFrame = function(frame)
            frame:SetSize(SIZE.CELL, SIZE.CELL)
            frame:SetPoint("TOPLEFT", container, "TOPLEFT")
            frame:SetFrameLevel(FrameLevel.AuraButton)
            frame.ActiveOverlay = frame:CreateTexture(nil, "OVERLAY")
            frame.ActiveOverlay:SetAllPoints(frame)
            frame.ActiveOverlay:SetTexture(AURA_TEXTURE)
            frame.ActiveOverlay:SetVertexColor(COLOR.WHITE:GetRGBA())
        end,
    })
    update()
end
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
eventFrame:RegisterEvent("PLAYER_FOCUS_CHANGED")
eventFrame:RegisterUnitEvent("UNIT_FACTION", "player", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_FLAGS", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function() After(0, update) end)
insert(UIInitFuncs, initialize)
