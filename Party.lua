local addonName, addonTable = ...
local log                   = addonTable.logging

local LibRangeCheck         = LibStub:GetLibrary("LibRangeCheck-3.0", true)

local roleColor             = {
    TANK = C_ClassColor.GetClassColor("WARRIOR"),
    HEALER = C_ClassColor.GetClassColor("PRIEST"),
    DAMAGER = C_ClassColor.GetClassColor("MAGE"),
    NONE = { 0, 0, 0 }
}


local function InitializePartyFrame()
    local node_size = addonTable.nodeSize
    local curve_reverse = addonTable.curve_reverse
    local curve = addonTable.curve
    for i = 1, 4 do
        local UnitKey = string.format("%s%d", "party", i)
        local buffFrameParent = addonTable["PartyFrame" .. UnitKey .. "BuffFrame"]
        local debuffFrameParent = addonTable["PartyFrame" .. UnitKey .. "DebuffFrame"]
        local statusFrameParent = addonTable["PartyFrame" .. UnitKey .. "StatusFrame"]

        local hp_frame = CreateFrame("Frame", addonName .. UnitKey .. "HPFrame", statusFrameParent)
        hp_frame:SetPoint("TOPLEFT", statusFrameParent, "TOPLEFT", 0, 0)
        hp_frame:SetFrameLevel(statusFrameParent:GetFrameLevel() + 1)
        hp_frame:SetSize(node_size, node_size)
        hp_frame:Show()

        local hp_texture = hp_frame:CreateTexture(nil, "BACKGROUND")
        hp_texture:SetAllPoints(hp_frame)
        hp_texture:SetColorTexture(0, 0, 0, 1)
        hp_texture:Show()

        local role_frame = CreateFrame("Frame", addonName .. UnitKey .. "RoleFrame", statusFrameParent)
        role_frame:SetPoint("TOPLEFT", statusFrameParent, "TOPLEFT", 0, -node_size)
        role_frame:SetFrameLevel(statusFrameParent:GetFrameLevel() + 1)
        role_frame:SetSize(node_size, node_size)
        role_frame:Show()

        local role_texture = role_frame:CreateTexture(nil, "BACKGROUND")
        role_texture:SetAllPoints(role_frame)
        role_texture:SetColorTexture(0, 0, 0, 1)
        role_texture:Show()

        local range_frame = CreateFrame("Frame", addonName .. UnitKey .. "RangeFrame", statusFrameParent)
        range_frame:SetPoint("TOPLEFT", statusFrameParent, "TOPLEFT", 0, -2 * node_size)
        range_frame:SetFrameLevel(statusFrameParent:GetFrameLevel() + 1)
        range_frame:SetSize(node_size, node_size)
        range_frame:Show()

        local range_texture = range_frame:CreateTexture(nil, "BACKGROUND")
        range_texture:SetAllPoints(range_frame)
        range_texture:SetColorTexture(0, 0, 0, 1)
        range_texture:Show()

        local class_frame = CreateFrame("Frame", addonName .. UnitKey .. "ClassFrame", statusFrameParent)
        class_frame:SetPoint("TOPLEFT", statusFrameParent, "TOPLEFT", 0, -3 * node_size)
        class_frame:SetFrameLevel(statusFrameParent:GetFrameLevel() + 1)
        class_frame:SetSize(node_size, node_size)
        class_frame:Show()

        local class_texture = class_frame:CreateTexture(nil, "BACKGROUND")
        class_texture:SetAllPoints(class_frame)
        class_texture:SetColorTexture(0, 0, 0, 1)
        class_texture:Show()


        addonTable.CreateAuraSequence(UnitKey, "HELPFUL", addonTable.PARTY_AURA_MAX, UnitKey .. "BuffFrame", buffFrameParent, Enum.UnitAuraSortRule.Default, Enum.UnitAuraSortDirection.Normal)
        addonTable.CreateAuraSequence(UnitKey, "HARMFUL", addonTable.PARTY_AURA_MAX, UnitKey .. "DebuffFrame", debuffFrameParent, Enum.UnitAuraSortRule.Default, Enum.UnitAuraSortDirection.Normal)


        function UpdatePartyFrame()
            local usePredicted = true
            if UnitExists(UnitKey) then
                local color = UnitHealthPercent(UnitKey, usePredicted, curve)
                hp_texture:SetColorTexture(color.r, color.g, color.b, 1)

                local role = UnitGroupRolesAssigned(UnitKey)
                role_texture:SetColorTexture(roleColor[role].r, roleColor[role].g, roleColor[role].b, 1)

                local _, maxRange = LibRangeCheck:GetRange(UnitKey)
                if maxRange and (maxRange <= addonTable.RangeCheck) then
                    range_texture:SetColorTexture(1, 1, 1, 1)
                else
                    range_texture:SetColorTexture(0, 0, 0, 1)
                end



                local _, classFilename, _ = UnitClass(UnitKey)
                local CLASS_COLOR = C_ClassColor.GetClassColor(classFilename)
                class_texture:SetColorTexture(CLASS_COLOR.r, CLASS_COLOR.g, CLASS_COLOR.b, 1)
            else
                hp_texture:SetColorTexture(0, 0, 0, 1)
                role_texture:SetColorTexture(0, 0, 0, 1)
                range_texture:SetColorTexture(0, 0, 0, 1)
                class_texture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdatePartyFrame)
    end
    log("PartyFrame created")
end

table.insert(addonTable.FrameInitFuncs, InitializePartyFrame)
