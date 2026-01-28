local addonName, addonTable = ...
local log                   = addonTable.logging
local fontFile, _, _        = GameFontNormal:GetFont()





addonTable.CreateAuraSequence = function(unit, filter, maxCount, name_prefix, parent, sortRule, sortDirection)
    local node_size = addonTable.nodeSize
    local curve = addonTable.curve_reverse
    local debuff_curve = addonTable.debuff_curve
    sortRule = sortRule or Enum.UnitAuraSortRule.Default
    sortDirection = sortDirection or Enum.UnitAuraSortDirection.Normal
    local iconTextures = {}
    local durationTextures = {}
    local dispelTextures = {}
    local countTextures = {}
    local DefensiveTextures = {}

    for i = 1, maxCount do
        local icon_frame = CreateFrame("Frame", addonName .. name_prefix .. "IconFrame" .. i, parent)
        icon_frame:SetPoint("TOPLEFT", parent, "TOPLEFT", (i - 1) * node_size, 0)
        icon_frame:SetFrameLevel(parent:GetFrameLevel() + 1)
        icon_frame:SetSize(node_size, node_size)
        icon_frame:Show()

        local icon_texture = icon_frame:CreateTexture(nil, "BACKGROUND")
        icon_texture:SetAllPoints(icon_frame)
        icon_texture:SetColorTexture(0, 0, 0, 1)
        icon_texture:Show()
        table.insert(iconTextures, icon_texture)

        local container_frame = CreateFrame("Frame", addonName .. name_prefix .. "ContainerFrame" .. i, parent)
        container_frame:SetPoint("TOPLEFT", parent, "TOPLEFT", (i - 1) * node_size, -node_size)
        container_frame:SetFrameLevel(parent:GetFrameLevel() + 1)
        container_frame:SetSize(node_size, node_size)
        container_frame:Show()

        local duration_frame = CreateFrame("Frame", addonName .. name_prefix .. "DurationFrame" .. i, container_frame)
        duration_frame:SetPoint("BOTTOMRIGHT", container_frame, "CENTER", 0, 0)
        duration_frame:SetFrameLevel(container_frame:GetFrameLevel() + 1)
        duration_frame:SetSize(node_size / 2, node_size / 2)
        duration_frame:Show()

        local duration_texture = duration_frame:CreateTexture(nil, "BACKGROUND")
        duration_texture:SetAllPoints(duration_frame)
        duration_texture:SetColorTexture(0, 0, 0, 1)
        duration_texture:Show()
        table.insert(durationTextures, duration_texture)

        local dispel_frame = CreateFrame("Frame", addonName .. name_prefix .. "DispelFrame" .. i, container_frame)
        dispel_frame:SetPoint("BOTTOMLEFT", container_frame, "CENTER", 0, 0)
        dispel_frame:SetFrameLevel(container_frame:GetFrameLevel() + 1)
        dispel_frame:SetSize(node_size / 2, node_size / 2)
        dispel_frame:Show()

        local dispel_texture = dispel_frame:CreateTexture(nil, "BACKGROUND")
        dispel_texture:SetAllPoints(dispel_frame)
        dispel_texture:SetColorTexture(0, 0, 0, 1)
        dispel_texture:Show()
        table.insert(dispelTextures, dispel_texture)

        local count_frame = CreateFrame("Frame", addonName .. name_prefix .. "CountFrame" .. i, container_frame)
        count_frame:SetPoint("TOPRIGHT", container_frame, "CENTER", 0, 0)
        count_frame:SetFrameLevel(container_frame:GetFrameLevel() + 1)
        count_frame:SetSize(node_size / 2, node_size / 2)
        count_frame:Show()

        local count_string = count_frame:CreateFontString(nil, "ARTWORK", "GameFontNormal")
        count_string:SetAllPoints(count_frame)
        count_string:SetJustifyH("CENTER")
        count_string:SetJustifyV("MIDDLE")

        count_string:SetFontObject(GameFontHighlight)
        count_string:SetTextColor(1, 1, 1, 1)
        count_string:SetFont(fontFile, node_size / 2.5, "MONOCHROME")
        count_string:SetText("")
        count_string:Show()
        table.insert(countTextures, count_string)

        local defensive_frame = CreateFrame("Frame", addonName .. name_prefix .. "DefensiveFrame" .. i, container_frame)
        defensive_frame:SetPoint("TOPLEFT", container_frame, "CENTER", 0, 0)
        defensive_frame:SetFrameLevel(container_frame:GetFrameLevel() + 1)
        defensive_frame:SetSize(node_size / 2, node_size / 2)
        defensive_frame:Show()

        local defensive_texture = defensive_frame:CreateTexture(nil, "BACKGROUND")
        defensive_texture:SetAllPoints(defensive_frame)
        defensive_texture:SetColorTexture(0, 0, 0, 1)
        defensive_texture:Show()
        table.insert(DefensiveTextures, defensive_texture)
    end

    local function wipeTextures()
        for _, texture in ipairs(iconTextures) do
            texture:SetColorTexture(0, 0, 0, 1)
        end
        for _, texture in ipairs(durationTextures) do
            texture:SetColorTexture(0, 0, 0, 1)
        end
        for _, texture in ipairs(dispelTextures) do
            texture:SetColorTexture(0, 0, 0, 1)
        end
        for _, texture in ipairs(countTextures) do
            texture:SetText("")
        end
        for _, texture in ipairs(DefensiveTextures) do
            texture:SetColorTexture(0, 0, 0, 1)
        end
    end

    local function updateTexture()
        wipeTextures()
        if not UnitExists(unit) then
            return
        end
        local auraInstanceIDs = C_UnitAuras.GetUnitAuraInstanceIDs(unit, filter, maxCount, sortRule, sortDirection)
        for i = 1, #auraInstanceIDs do
            local auraInstanceID = auraInstanceIDs[i]
            local aura = C_UnitAuras.GetAuraDataByAuraInstanceID(unit, auraInstanceID)
            local duration = C_UnitAuras.GetAuraDuration(unit, auraInstanceID)
            local result = duration:EvaluateElapsedPercent(curve)
            local dispelTypeColor = C_UnitAuras.GetAuraDispelTypeColor(unit, auraInstanceID, debuff_curve)
            local count = C_UnitAuras.GetAuraApplicationDisplayCount(unit, auraInstanceID, 1, 9)
            local isBigDefensive = C_UnitAuras.AuraIsBigDefensive(aura.spellId)

            iconTextures[i]:SetTexture(aura.icon)
            durationTextures[i]:SetColorTexture(result.r, result.g, result.b, 1)
            dispelTextures[i]:SetColorTexture(dispelTypeColor:GetRGBA())
            countTextures[i]:SetText(count)
            DefensiveTextures[i]:SetColorTexture(C_CurveUtil.EvaluateColorFromBoolean(isBigDefensive, { r = 1, g = 1, b = 1, a = 1 }, { r = 0, g = 0, b = 0, a = 1 }):GetRGBA())
        end
    end
    table.insert(addonTable.UpdateFuncs, updateTexture)
end


local function InitializeAuraFrame()
    addonTable.CreateAuraSequence("target", "HARMFUL|PLAYER", addonTable.TARGET_DEBUFF_MAX, "TargetDebuff", addonTable.TargetDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    addonTable.CreateAuraSequence("player", "HARMFUL", addonTable.PLAYER_DEBUFF_MAX, "PlayerDebuff", addonTable.PlayerDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    addonTable.CreateAuraSequence("player", "HELPFUL|PLAYER", addonTable.PLAYER_BUFF_MAX, "PlayerBuff", addonTable.PlayerBuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
end
table.insert(addonTable.FrameInitFuncs, InitializeAuraFrame)
