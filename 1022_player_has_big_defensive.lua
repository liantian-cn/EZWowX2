-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame = CreateFrame
local BigDefensive = AuraContainerSortMethod.BigDefensive
local Normal = AuraContainerSortDirection.Normal

-- 插件级变量定义/引用
local Cell = addonTable.Cell
local PLAYER_STATUS = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS

-- 本地变量定义
local insert = table.insert
local CELL_INDEX = 22
local CELL_POSITION_X = 22
local CELL_POSITION_Y = 1
local AURA_BORDER_FULL_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_full.tga"

-- 代码部分

--[[
简述：      玩家拥有大型防御效果
分类：      玩家状态
分类索引：  22
位置：      1行22列

说明

通过 AuraSlot 显示最高优先级的大型防御效果。外部施放优先，其次选择到期更晚的效果。
AuraButton 的不透明 ActiveOverlay 覆盖图标，使该 Cell 仅编码 Aura 是否存在。
]]

local function InitializeAuraButton(auraButton, size)
    auraButton:SetSize(size.CELL, size.CELL)

    auraButton.Icon = auraButton:CreateTexture(nil, "BACKGROUND")
    auraButton.Icon:SetAllPoints(auraButton)
    auraButton:SetIcon(auraButton.Icon)

    auraButton.ActiveOverlay = auraButton:CreateTexture(nil, "OVERLAY")
    auraButton.ActiveOverlay:SetAllPoints(auraButton)
    auraButton.ActiveOverlay:SetTexture(AURA_BORDER_FULL_TEXTURE)
    auraButton.ActiveOverlay:SetVertexColor(PLAYER_STATUS / 255, CELL_INDEX / 255, 1, 1)
end

local function InitFrame()
    local size = addonTable.SIZE
    local parent = addonTable.MartixFrame
    local cell = Cell:New({
        x = CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = PLAYER_STATUS,
        index = CELL_INDEX,
        default_value = 0,
    })
    local container = CreateFrame("AuraContainer", nil, parent, "CustomAuraContainerTemplate")

    cell.Frame:SetFrameLevel(parent:GetFrameLevel() + 5)

    container:SetPoint(
        "TOPLEFT",
        parent,
        "TOPLEFT",
        CELL_POSITION_X * size.CELL,
        -(CELL_POSITION_Y - 1) * size.CELL
    )
    container:SetFrameLevel(parent:GetFrameLevel() + 10)
    container:SetSize(size.CELL, size.CELL)
    container:SetUnit("player")

    local auraButton = container:AddAuraSlot("big_defensive", "HELPFUL|BIG_DEFENSIVE", {
        sortMethod = BigDefensive,
        sortDirection = Normal,
        initializeFrame = function(frame)
            InitializeAuraButton(frame, size)
        end,
    })
    auraButton:SetPoint("TOPLEFT", container, "TOPLEFT")
    auraButton:SetFrameLevel(parent:GetFrameLevel() + 10)
end

insert(addonTable.FrameInitFuncs, InitFrame)
