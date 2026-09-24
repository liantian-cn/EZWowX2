--[[
original: ../conditions/focus_has_debuff@dev/template.lua
uuid: {{uuid}}
摘要：不可辅助焦点的指定减益存在状态。
描述：单 AuraSlot 多 ID 首匹配；白色覆盖黑底，不读取光环数据或显示状态。
修改记录：
2026-09-20：直接使用 CellBackplate 提供固定黑底与行宽登记。
2026-09-18：按冻结约定新增。
2026-09-18：按用户确认固定为 PLAYER|HARMFUL 来源过滤。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建容器与事件框架
local After = C_Timer.After -- 事件延后下一帧
local UnitExists = UnitExists -- 排除无单位
local UnitCanAssist = UnitCanAssist -- 按光环身份规则分类
local ipairs = ipairs -- 遍历静态配置
local insert = table.insert -- 注册初始化
--[[
沿用冻结计划已确认的 12.1.0.69587 契约；2026-09-18 查阅实现，未重核 build 差异。
历史 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：Blizzard_AuraContainer/Blizzard_CustomAuraContainer.lua、Blizzard_AuraContainerUtil.lua。
AddAuraSlot(key, filter, options) 创建官方首匹配槽；candidateFilters.includeSpellIDs 为 ID 集合。
固定 PLAYER|HARMFUL；PLAYER 包含玩家宠物／载具，2026-09-18 核验同 revision 的 Blizzard_FrameXMLUtil/AuraUtil.lua。
UnitCanAssist("player", unit, true, true) 忽略免疫和不可交互限制，不可辅助侧显示减益。
初始化回调仅布置静态纹理，秘密光环筛选及槽显示由官方管理。
Wiki：https://warcraft.wiki.gg/wiki/API_UnitCanAssist；本次未获取页面，说明来自冻结约定和源码。
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
local AURA_IDS = { {{aura_ids}} }
local UNIT_TOKEN = "focus"
local AURA_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_full.tga"
local container
local eventFrame = CreateFrame("Frame")
local function update()
    if not container then return end
    container:SetShown(UnitExists(UNIT_TOKEN) and not UnitCanAssist("player", UNIT_TOKEN, true, true))
    container:UpdateAllAuras()
end
local function initialize()
    local backing = CellBackplate:New({ x = POSITION_X, y = POSITION_Y })
    container = CreateFrame("AuraContainer", nil, backing.Frame, "CustomAuraContainerTemplate")
    container:SetAllPoints(backing.Frame)
    container:SetFrameLevel(FrameLevel.AuraContainer)
    container:SetUnit(UNIT_TOKEN)
    local includeSpellIDs = {}
    for _, spellID in ipairs(AURA_IDS) do includeSpellIDs[spellID] = true end
    container:AddAuraSlot("aura", "PLAYER|HARMFUL", { -- 官方 PLAYER 包含玩家宠物／载具
        candidateFilters = { includeSpellIDs = includeSpellIDs },
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
