--[[
original: ../conditions/aura_player_buff_duration@dev/template.lua
uuid: {{uuid}}
摘要：玩家增益剩余时间比例。
描述：ValueBarBackplate 提供固定背板，官方单槽首匹配时长条覆盖内容；永久光环交官方处理。
修改记录：
2026-09-20：直接使用 ValueBarBackplate，槽内条静态设置 AuraContent，不再创建默认填充。
2026-09-19：增加默认开启的 player_only 来源过滤，配置小数时长仅影响 Python 换算。
2026-09-18：按冻结约定新增。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建容器与条
local After = C_Timer.After -- 延后事件刷新
local Immediate = Enum.StatusBarInterpolation.Immediate -- 即时更新
local RemainingTime = Enum.StatusBarTimerDirection.RemainingTime -- 剩余时间方向
local ipairs = ipairs -- 遍历配置 ID
local insert = table.insert -- 注册初始化
--[[
SetDurationBar(statusBar, { interpolation, direction }) 绑定官方时长显示，无返回值。
StatusBar 必须为 AuraButton 子级；官方持有秘密时长并更新填充，插件不读取或比较。
AddAuraSlot(key, filter, options) 通过 candidateFilters.includeSpellIDs 集合首匹配。
player_only 默认 true 使用 HELPFUL|PLAYER，false 使用 HELPFUL；PLAYER 包括玩家、宠物和载具。
2026-09-19 核验同 revision 的 Blizzard_FrameXMLUtil/AuraUtil.lua 与 Blizzard_AuraContainerUtil.lua 来源筛选。
沿用冻结 12.1.0.69587 契约；2026-09-18 查阅 Blizzard_CustomAuraButton.lua、
Blizzard_CustomAuraContainer.lua，未重核 build 差异；历史 revision：
a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
Wiki：https://warcraft.wiki.gg/wiki/API:AuraButton_SetDurationBar；本次未获取页面。
条比例来自实际光环时长；Python 乘配置 duration，仅为估计而非固定绝对量程。
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
local AURA_FILTER = {{aura_filter}} -- 已验证的玩家来源筛选
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"
local container
local eventFrame = CreateFrame("Frame")
local function update()
    if container then container:UpdateAllAuras() end
end
local function initialize()
    local backing = ValueBarBackplate:New(POSITION_X, WIDTH)
    container = CreateFrame("AuraContainer", nil, backing.Frame, "CustomAuraContainerTemplate")
    container:SetAllPoints(backing.Frame)
    container:SetFrameLevel(FrameLevel.AuraContainer)
    container:SetUnit("player")
    local includeSpellIDs = {}
    for _, spellID in ipairs(AURA_IDS) do includeSpellIDs[spellID] = true end
    container:AddAuraSlot("aura", AURA_FILTER, {
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
eventFrame:SetScript("OnEvent", function() After(0, update) end)
insert(UIInitFuncs, initialize)
