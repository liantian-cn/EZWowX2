--[[
original: ../conditions/aura_target_debuff_duration_pct@dev/template.lua
uuid: {{uuid}}
摘要：不可辅助目标的减益剩余时长条百分比。
描述：ValueBarBackplate 固定内容宽度为 5 Cell，官方单槽首匹配时长条覆盖内容。
Python 只返回原生条比例的百分数，不换算绝对秒数；永久光环交官方处理，不保证满条。
修改记录：
2026-09-20：直接使用 ValueBarBackplate，槽内条静态设置 AuraContent，不再创建默认填充。
2026-09-20：新增独立百分比插件，沿用目标减益 duration 模板的显示门控、绑定与事件生命周期。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建容器与条
local After = C_Timer.After -- 延后事件刷新
local UnitExists = UnitExists -- 排除无目标
local UnitCanAssist = UnitCanAssist -- 按光环身份规则分类
local Immediate = Enum.StatusBarInterpolation.Immediate -- 即时更新
local RemainingTime = Enum.StatusBarTimerDirection.RemainingTime -- 剩余时间方向
local ipairs = ipairs -- 遍历配置 ID
local insert = table.insert -- 注册初始化
--[[
SetDurationBar(statusBar, { interpolation, direction }) 绑定官方时长显示，无返回值。
StatusBar 必须为 AuraButton 子级；官方持有秘密时长并更新填充，插件不读取或比较。
AddAuraSlot(key, "PLAYER|HARMFUL", options) 通过 candidateFilters.includeSpellIDs 集合首匹配。
PLAYER 包含玩家宠物／载具；UnitCanAssist("player", "target", true, true) 为真时隐藏容器。
目标不存在时同样隐藏容器；不读取槽可见性，不额外添加 UnitCanAttack 门控。
2026-09-20 沿用既有 12.1.0 (69587) API 基线，未新增 API 行为或重新进行游戏验收。
既有核验 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：Interface/AddOns/Blizzard_AuraContainer/Blizzard_CustomAuraButton.lua、
Blizzard_CustomAuraContainer.lua、Blizzard_AuraContainerUtil.lua，及 Blizzard_FrameXMLUtil/AuraUtil.lua。
Wiki：https://warcraft.wiki.gg/wiki/API:AuraButton_SetDurationBar；本次未获取页面。
条比例来自实际光环时长；Python 返回 ratio * 100，不保证永久光环的具体条表现。
]]
--[[  variable reference  ]]
local ValueBarBackplate = addonTable.ValueBarBackplate -- 定位、红色分隔与固定黑底
local SIZE = addonTable.SIZE -- 像素尺寸
local COLOR = addonTable.COLOR -- 黑白配色
local FrameLevel = addonTable.FrameLevel -- 显示层级
local UIInitFuncs = addonTable.UIInitFuncs -- 延迟初始化
--[[  logical code  ]]
local POSITION_X = {{x1}}
local WIDTH = {{width1}} -- 输出契约固定为 5，由冻结布局注入
local AURA_IDS = { {{aura_ids}} }
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
            frame:SetDurationBar(bar, { interpolation = Immediate, direction = RemainingTime })
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
