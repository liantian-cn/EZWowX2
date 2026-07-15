-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame = CreateFrame

-- 插件级变量定义/引用
local Cell = addonTable.Cell
local TARGET_STATUS = addonTable.CELL_CLASSIFICATION.TARGET_STATUS

-- 本地变量定义
local insert = table.insert
local CELL_INDEX = 11
local CELL_POSITION_X = 51
local CELL_POSITION_Y = 1
local UNIT_TOKEN = "target"
local AURA_BORDER_FULL_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_full.tga"

-- 代码部分

--[[
简述：      目标拥有团队可驱散增益效果
分类：      目标状态
分类索引：  11
位置：      1行51列

说明

通过 AuraSlot 显示团队成员可驱散或偷取的目标增益效果。
AuraButton 仅包含固定的不透明 ActiveOverlay，使该 Cell 仅编码 Aura 是否存在。
]]

local function InitializeAuraButton(auraButton, size, container, parent)
    auraButton:SetSize(size.CELL, size.CELL)
    auraButton:SetPoint("TOPLEFT", container, "TOPLEFT")
    auraButton:SetFrameLevel(parent:GetFrameLevel() + 10)

    auraButton.ActiveOverlay = auraButton:CreateTexture(nil, "OVERLAY")
    auraButton.ActiveOverlay:SetAllPoints(auraButton)
    auraButton.ActiveOverlay:SetTexture(AURA_BORDER_FULL_TEXTURE)
    auraButton.ActiveOverlay:SetVertexColor(TARGET_STATUS / 255, CELL_INDEX / 255, 1, 1)
end

local function InitFrame()
    local size = addonTable.SIZE
    local parent = addonTable.MartixFrame
    local cell = Cell:New({
        x = CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = TARGET_STATUS,
        index = CELL_INDEX,
        default_value = 0,
    })
    local container = CreateFrame("AuraContainer", nil, parent, "CustomAuraContainerTemplate")
    local eventFrame = CreateFrame("Frame")

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
    container:SetUnit(UNIT_TOKEN)

    container:AddAuraSlot("dispellable_buff", "HELPFUL|RAID_PLAYER_DISPELLABLE", {
        initializeFrame = function(frame)
            InitializeAuraButton(frame, size, container, parent)
        end,
    })

    -- AuraContainer updates aura instances internally; fixed target-token identity and raid dispel capability need external invalidation.
    eventFrame:RegisterEvent("PLAYER_TARGET_CHANGED")
    eventFrame:RegisterEvent("GROUP_ROSTER_UPDATE")
    eventFrame:RegisterEvent("PLAYER_SPECIALIZATION_CHANGED")
    eventFrame:SetScript("OnEvent", function(self, event, unitTarget)
        if event == "PLAYER_SPECIALIZATION_CHANGED" and unitTarget ~= "player" then
            return
        end

        container:UpdateAllAuras()
    end)
end

insert(addonTable.FrameInitFuncs, InitFrame)
