--[[
original: examples\04_player_buff.lua
uuid: {{uuid}}
index: 4
摘要：在第二行第 4 个 Cell 中通过 AuraContainer 显示玩家指定增益是否存在。

描述：
    使用 CellBackplate 创建固定黑色背板，并在其下挂接覆盖整个 Cell 的玩家增益容器。
    一个固定 Aura slot 接受任一候选技能 ID，以不透明白色贴图填满按钮。
    AuraContainer 管理按钮显示，增益消失时露出黑色底板；本例不添加事件或轮询刷新。

修改记录：
2026-09-20：直接使用 CellBackplate 提供固定黑底与行宽登记。
2026-09-11：按解码开发前的 Lua 示例需求新增玩家增益 Cell。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local CreateFrame = CreateFrame -- 创建使用官方模板的 AuraContainer
local ipairs = ipairs -- 将候选技能 ID 列表转换为过滤映射
local insert = table.insert -- 注册 UI 初始化函数

--[[
CustomAuraContainerTemplate：由引擎和官方容器管理光环筛选及按钮显示。
构造：container = CreateFrame("AuraContainer", nil, cell.Frame, "CustomAuraContainerTemplate")
签名：container:SetUnit(unitToken)
参数：unitToken 为单位标识，本例固定 "player"；不消费返回值。
签名：auraFrame = container:AddAuraSlot(slotKey, filterString, options)
参数：slotKey 为容器内唯一的非空字符串，本例保留 {{uuid}}；filterString 为 "HELPFUL"；
    options.candidateFilters.includeSpellIDs 为 {[spellID] = true} 映射，接受任一匹配 ID。
    options.initializeFrame(frame) 在按钮创建后、访问限制应用前执行，只用于静态外观初始化。
返回值：slot 对应的 AuraButton，本例不保存或读取该返回值。
限制：固定 slot 不参与动态布局，需要在初始化回调中手动锚定。
    本地源码允许对玩家的 HELPFUL 光环使用身份候选过滤；不把此结论推广到其他单位或减益。
    不读取 AuraData、按钮可见性或访问限制来推断增益，不自行挂接刷新脚本。

核验日期：2026-09-11；本地 @wow-ui-source 版本：12.1.0.69587。
源码 revision：288f40d5cee5089223758d5810cb906ad34d4018。
本例契约依据 Interface/AddOns/Blizzard_AuraContainer/ 下的
    Blizzard_CustomAuraContainer.lua、Blizzard_AuraContainerShared.lua、
    Blizzard_AuraContainerFrameProviders.lua、Blizzard_AuraContainerUtil.lua。
]]

--[[  variable reference  ]]

local CellBackplate = addonTable.CellBackplate -- 直接使用固定黑色背板
local COLOR = addonTable.COLOR -- 共享黑白颜色
local SIZE = addonTable.SIZE -- 初始化时读取已换算的 Cell 尺寸
local FrameLevel = addonTable.FrameLevel -- Cell 底板、光环容器及按钮的共享层级
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸和背景就绪后创建背板

--[[  logical code  ]]

-- 技能名称：枯萎凋零；类型：RotationsCell。名称和类型仅作说明，以下参数供未来插件替换。
local SPELL_IDS = { 188298, 188290 } -- 任一对应增益存在时显示白色
local POSITION_Y = 2 -- 第二行，RotationsCell 对应的行
local POSITION_X = 4 -- 本行第 4 个 Cell
local AURA_BORDER_FULL_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_full.tga" -- 覆盖满的白色贴图

local function CreateSpellIDMap(spellIDs)
    local includeSpellIDs = {} -- 只在构造阶段创建一次候选过滤映射
    for _, spellID in ipairs(spellIDs) do
        includeSpellIDs[spellID] = true
    end
    return includeSpellIDs
end

local function InitializeAuraButton(auraButton, container)
    auraButton:SetSize(SIZE.CELL, SIZE.CELL) -- 按钮填满一个 Cell
    auraButton:SetPoint("TOPLEFT", container, "TOPLEFT") -- 固定 slot 与容器左上角重合
    auraButton:SetFrameLevel(FrameLevel.AuraButton) -- 白色内容位于黑色底板和容器上方

    auraButton.ActiveOverlay = auraButton:CreateTexture(nil, "OVERLAY") -- 初始化阶段创建静态覆盖纹理
    auraButton.ActiveOverlay:SetAllPoints(auraButton)
    auraButton.ActiveOverlay:SetTexture(AURA_BORDER_FULL_TEXTURE)
    auraButton.ActiveOverlay:SetVertexColor(COLOR.WHITE:GetRGBA()) -- 使用正确的 ColorMixin 方法名
end

local function InitializePlayerBuffCell()
    local cell = CellBackplate:New({ x = POSITION_X, y = POSITION_Y }) -- 背板提供不透明黑底
    local container = CreateFrame("AuraContainer", nil, cell.Frame, "CustomAuraContainerTemplate")
    container:SetAllPoints(cell.Frame) -- 无偏移填满背板，直接沿用内容矩形尺寸
    container:SetFrameLevel(FrameLevel.AuraContainer)
    container:SetUnit("player") -- 仅显示玩家身上的增益
    container:AddAuraSlot("{{uuid}}", "HELPFUL", {
        candidateFilters = {
            includeSpellIDs = CreateSpellIDMap(SPELL_IDS), -- 由容器筛选任一候选技能
        },
        initializeFrame = function(frame)
            InitializeAuraButton(frame, container) -- 仅初始化静态外观，显示状态由容器管理
        end,
    })
end

insert(UIInitFuncs, InitializePlayerBuffCell) -- 沿用共享布局、计数和缩放
