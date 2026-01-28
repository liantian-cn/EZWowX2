local addonName, addonTable = ...
local log                   = addonTable.logging

local function InitializeTestShowFrame()
    local node_size = addonTable.nodeSize

    local test_show_frame1 = CreateFrame("Frame", addonName .. "TestShowFrame1", addonTable.MainFrame)
    test_show_frame1:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 0, 0)
    test_show_frame1:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 2)
    test_show_frame1:SetSize(node_size, node_size)
    test_show_frame1:Show()

    local test_show_frame1_texture = test_show_frame1:CreateTexture(nil, "BACKGROUND")
    test_show_frame1_texture:SetAllPoints(test_show_frame1)
    test_show_frame1_texture:SetColorTexture(0, 0, 0, 1)
    test_show_frame1_texture:Show()

    local test_show_frame2 = CreateFrame("Frame", addonName .. "TestShowFrame2", addonTable.MainFrame)
    test_show_frame2:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 2 * node_size, 0)
    test_show_frame2:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 2)
    test_show_frame2:SetSize(node_size, node_size)
    test_show_frame2:Show()

    local test_show_frame2_texture = test_show_frame2:CreateTexture(nil, "BACKGROUND")
    test_show_frame2_texture:SetAllPoints(test_show_frame2)
    test_show_frame2_texture:SetColorTexture(0, 0, 0, 1)
    test_show_frame2_texture:Show()

    local test_show_frame3 = CreateFrame("Frame", addonName .. "TestShowFrame3", addonTable.MainFrame)
    test_show_frame3:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 0, -2 * node_size)
    test_show_frame3:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 2)
    test_show_frame3:SetSize(node_size, node_size)
    test_show_frame3:Show()

    local test_show_frame3_texture = test_show_frame3:CreateTexture(nil, "BACKGROUND")
    test_show_frame3_texture:SetAllPoints(test_show_frame3)
    test_show_frame3_texture:SetColorTexture(0, 0, 0, 1)
    test_show_frame3_texture:Show()

    SLASH_ADDONTESTSHOW1 = "/spellicon"
    SLASH_ADDONTESTSHOW2 = "/si"
    SlashCmdList["ADDONTESTSHOW"] = function(msg)
        local spellID = tonumber(msg)
        if not spellID then
            log("Invalid spellID")
            return
        end
        local iconID, originalIconID = C_Spell.GetSpellTexture(spellID)
        if not iconID then
            log("Invalid spellID")
            return
        end
        test_show_frame1_texture:SetTexture(iconID)
        test_show_frame2_texture:SetTexture(iconID)
        test_show_frame3_texture:SetTexture(iconID)
        local spellLink = C_Spell.GetSpellLink(spellID)
        log(spellLink)
        C_Timer.After(3, function()
            -- print("Hello")
            test_show_frame1_texture:SetColorTexture(0, 0, 0, 1)
            test_show_frame2_texture:SetColorTexture(0, 0, 0, 1)
            test_show_frame3_texture:SetColorTexture(0, 0, 0, 1)
        end)
    end
end


table.insert(addonTable.FrameInitFuncs, InitializeTestShowFrame)
