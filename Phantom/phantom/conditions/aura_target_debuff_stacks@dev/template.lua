--[[
original: ../conditions/aura_target_debuff_stacks@dev/template.lua
uuid: {{uuid}}
摘要：不可辅助目标的减益层数比例。
描述：ValueBarBackplate 提供固定背板，官方单槽首匹配层数条覆盖内容；无光环露出黑底。
修改记录：
2026-09-20：直接使用 ValueBarBackplate，槽内条静态设置 AuraContent，不再创建默认填充。
2026-09-18：按冻结约定新增。
2026-09-18：按用户确认固定为 PLAYER|HARMFUL 来源过滤。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建容器与条
local After = C_Timer.After -- 延后事件刷新
local UnitExists = UnitExists -- 排除无目标
local UnitCanAssist = UnitCanAssist -- 按光环身份规则分类
local ipairs = ipairs -- 遍历配置 ID
local insert = table.insert -- 注册初始化
--[[
SetApplicationBar(statusBar, { maxApplications }) 绑定官方层数显示，无返回值。
StatusBar 必须为 AuraButton 子级；官方持有秘密层数并更新填充，插件不读取或比较。
AddAuraSlot(key, "PLAYER|HARMFUL", options) 通过 candidateFilters.includeSpellIDs 集合首匹配。
PLAYER 包含玩家宠物／载具；2026-09-18 核验同 revision 的 Blizzard_FrameXMLUtil/AuraUtil.lua。
UnitCanAssist("player", "target", true, true) 为真时隐藏减益容器，不读取槽可见性。
沿用冻结 12.1.0.69587 契约；2026-09-18 查阅 Blizzard_CustomAuraButton.lua、
Blizzard_CustomAuraContainer.lua、Blizzard_AuraContainerUtil.lua，未重核 build 差异；历史 revision：
a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
用户指定版本来源：https://warcraft.wiki.gg/wiki/API:AuraButton_SetApplicationBar?oldid=6858640
本次未获取页面；按冻结约定仅传 maxApplications，不启用新版 minApplications 等选项。
]]
--[[  variable reference  ]]
local ValueBarBackplate = addonTable.ValueBarBackplate -- 定位、红色分隔与固定黑底
local SIZE = addonTable.SIZE -- 像素尺寸
local COLOR = addonTable.COLOR -- 黑白配色
local FrameLevel = addonTable.FrameLevel -- 显示层级
local UIInitFuncs = addonTable.UIInitFuncs -- 延迟初始化
--[[  logical code  ]]
local POSITION_X = {{x1}}
local WIDTH = {{width1}}
local AURA_IDS = { {{aura_ids}} }
local MAX_APPLICATIONS = {{max_value}}
local UNIT_TOKEN = "target"
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"
local container
local eventFrame = CreateFrame("Frame")
local function update()
    if not container then return end
    container:SetShown(UnitExists(UNIT_TOKEN) and not UnitCanAssist("player", UNIT_TOKEN, true, true))
    container:UpdateAllAuras()
end
local function initialize()
    local backing = ValueBarBackplate:New(POSITION_X, WIDTH)
    container = CreateFrame("AuraContainer", nil, backing.Frame, "CustomAuraContainerTemplate")
    container:SetAllPoints(backing.Frame)
    container:SetFrameLevel(FrameLevel.AuraContainer)
    container:SetUnit(UNIT_TOKEN)
    local includeSpellIDs = {}
    for _, spellID in ipairs(AURA_IDS) do includeSpellIDs[spellID] = true end
    container:AddAuraSlot("aura", "PLAYER|HARMFUL", { -- 官方 PLAYER 包含玩家宠物／载具
        candidateFilters = { includeSpellIDs = includeSpellIDs },
        initializeFrame = function(frame)
            frame:SetSize(WIDTH * SIZE.CELL, SIZE.CELL)
            frame:SetPoint("TOPLEFT", container, "TOPLEFT")
            frame:SetFrameLevel(FrameLevel.AuraButton)
            local bar = CreateFrame("StatusBar", nil, frame)
            bar:SetFrameLevel(FrameLevel.AuraContent) -- 初始化时固定槽位内容层级
            bar:SetAllPoints(frame)
            bar:SetOrientation("HORIZONTAL")
            bar:SetStatusBarTexture(WHITE_TEXTURE)
            bar:SetStatusBarColor(COLOR.WHITE:GetRGBA())
            local background = bar:CreateTexture(nil, "BACKGROUND")
            background:SetAllPoints(bar)
            background:SetColorTexture(COLOR.BLACK:GetRGBA())
            frame:SetApplicationBar(bar, { maxApplications = MAX_APPLICATIONS })
        end,
    })
    update()
end
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
eventFrame:RegisterEvent("PLAYER_TARGET_CHANGED")
eventFrame:RegisterUnitEvent("UNIT_FACTION", "player", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_FLAGS", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function() After(0, update) end)
insert(UIInitFuncs, initialize)
