local addonName, addonTable = ...
local log                   = addonTable.logging



-- 初始化技能冷却时间显示框架
-- 为配置的技能创建冷却时间显示节点，每个节点显示一个技能的冷却状态
-- 通过颜色渐变表示冷却进度，使用反向曲线（从白到黑）
local function InitializeSpellCDFrame()
    local node_size = addonTable.nodeSize
    local curve = addonTable.curve_reverse

    local MaxFrame = math.min(addonTable.SPELL_CD_MAX, #addonTable.SpellCD)

    for i = 1, MaxFrame do
        local SpellID = addonTable.SpellCD[i]
        local iconID, _ = C_Spell.GetSpellTexture(SpellID)
        local iconFrame = CreateFrame("Frame", addonName .. "SpellCDIconFrame" .. tostring(SpellID), addonTable.PlayerSpellCDFrame)
        iconFrame:SetPoint("TOPLEFT", addonTable.PlayerSpellCDFrame, "TOPLEFT", (i - 1) * node_size, 0)
        iconFrame:SetFrameLevel(addonTable.PlayerSpellCDFrame:GetFrameLevel() + 1)
        iconFrame:SetSize(node_size, node_size)
        iconFrame:Show()

        local iconTexture = iconFrame:CreateTexture(nil, "BACKGROUND")
        iconTexture:SetAllPoints(iconFrame)
        iconTexture:SetTexture(iconID)
        iconTexture:Show()



        local cooldownFrame = CreateFrame("Frame", addonName .. "CDFrame" .. tostring(SpellID), addonTable.PlayerSpellCDFrame)

        cooldownFrame:SetPoint("TOPLEFT", addonTable.PlayerSpellCDFrame, "TOPLEFT", (i - 1) * node_size, -1 * node_size)
        cooldownFrame:SetFrameLevel(addonTable.PlayerSpellCDFrame:GetFrameLevel() + 1)
        cooldownFrame:SetSize(node_size, node_size)
        cooldownFrame:Show()

        local cooldownFrameTexture = cooldownFrame:CreateTexture(nil, "BACKGROUND")
        cooldownFrameTexture:SetAllPoints(cooldownFrame)
        cooldownFrameTexture:SetColorTexture(0, 0, 0, 1)
        cooldownFrameTexture:Show()

        local function UpdateNodeTexture()
            -- 更新技能冷却节点的纹理颜色
            -- 根据技能的剩余冷却时间百分比，使用反向曲线计算颜色
            -- 冷却时间越长，颜色越接近黑色；冷却完成时，颜色接近白色
            local duration = C_Spell.GetSpellCooldownDuration(SpellID)
            local result = duration:EvaluateRemainingPercent(curve)
            cooldownFrameTexture:SetColorTexture(result.r, result.g, result.b, 1)
        end
        addonTable.UpdateFuncs[#addonTable.UpdateFuncs + 1] = UpdateNodeTexture
    end
    log("PlayerSpellCDFrame created")
end
table.insert(addonTable.FrameInitFuncs, InitializeSpellCDFrame)
