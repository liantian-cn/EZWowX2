local addonName, addonTable = ...
local log                   = addonTable.logging



-- 初始化技能充能冷却时间显示框架
-- 为配置的充能型技能创建冷却时间显示节点，每个节点显示一个技能的充能状态
-- 通过颜色渐变表示充能进度，使用反向曲线（从白到黑）
local function InitializeChargeCDFrame()
    local node_size = addonTable.nodeSize
    local curve = addonTable.curve_reverse

    local MaxFrame = math.min(addonTable.SPELL_CHARGE_MAX, #addonTable.SpellChargeCD)

    for i = 1, MaxFrame do
        local SpellID = addonTable.SpellChargeCD[i]
        local iconID, _ = C_Spell.GetSpellTexture(SpellID)

        local iconFrame = CreateFrame("Frame", addonName .. "SpellChargeCDIconFrame" .. tostring(SpellID), addonTable.PlayerChargeFrame)
        iconFrame:SetPoint("TOPLEFT", addonTable.PlayerChargeFrame, "TOPLEFT", (i - 1) * node_size, 0)
        iconFrame:SetFrameLevel(addonTable.PlayerChargeFrame:GetFrameLevel() + 1)
        iconFrame:SetSize(node_size, node_size)
        iconFrame:Show()

        local iconTexture = iconFrame:CreateTexture(nil, "BACKGROUND")
        iconTexture:SetAllPoints(iconFrame)
        iconTexture:SetTexture(iconID)
        iconTexture:Show()


        local chargeFrame = CreateFrame("Frame", addonName .. "ChargeCDFrame" .. tostring(SpellID),
            addonTable.PlayerChargeFrame)
        chargeFrame:SetPoint("TOPLEFT", addonTable.PlayerChargeFrame, "TOPLEFT", (i - 1) * node_size, -1 * node_size)
        chargeFrame:SetFrameLevel(addonTable.PlayerChargeFrame:GetFrameLevel() + 1)
        chargeFrame:SetSize(node_size, node_size)
        chargeFrame:Show()

        local chargeFrameTexture = chargeFrame:CreateTexture(nil, "BACKGROUND")
        chargeFrameTexture:SetAllPoints(chargeFrame)
        chargeFrameTexture:SetColorTexture(0, 0, 0, 1)
        chargeFrameTexture:Show()

        local function UpdateNodeTexture()
            -- 更新技能充能节点的纹理颜色
            -- 根据技能的剩余充能时间百分比，使用反向曲线计算颜色
            -- 充能时间越长，颜色越接近黑色；充能完成时，颜色接近白色
            local duration = C_Spell.GetSpellChargeDuration(SpellID)
            local result = duration:EvaluateRemainingPercent(curve)
            chargeFrameTexture:SetColorTexture(result.r, result.g, result.b, 1)
        end
        addonTable.UpdateFuncs[#addonTable.UpdateFuncs + 1] = UpdateNodeTexture
    end
    log("PlayerChargeCDFrame created")
end
table.insert(addonTable.FrameInitFuncs, InitializeChargeCDFrame)
