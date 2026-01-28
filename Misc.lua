local addonName, addonTable = ...
local LibRangeCheck         = LibStub:GetLibrary("LibRangeCheck-3.0", true)
local log                   = addonTable.logging


-- 初始化杂项状态显示框架
-- 创建多个状态指示器节点，用于显示各种游戏状态信息
-- 包括目标可攻击状态、战斗状态、强化状态、移动状态等
local function InitializeMiscFrame()
    local node_size = addonTable.nodeSize
    local curve_reverse = addonTable.curve_reverse
    local curve = addonTable.curve

    do
        local x = 0
        local y = 0
        local title = "TargetCanAttack"
        local nodeFrame = CreateFrame("Frame", addonName .. title .. "Frame", addonTable.MiscFrame)
        nodeFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        nodeFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        nodeFrame:SetSize(node_size, node_size)
        nodeFrame:Show()

        local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
        nodeTexture:SetAllPoints(nodeFrame)
        nodeTexture:SetColorTexture(0, 0, 0, 1)
        nodeTexture:Show()

        function UpdateNodeTexture()
            -- 更新目标可攻击状态指示器
            -- 如果目标存在且可以攻击，显示白色；否则显示黑色
            if UnitExists("target") and UnitCanAttack("target", "player") then
                nodeTexture:SetColorTexture(1, 1, 1, 1)
            else
                nodeTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateNodeTexture)
    end

    do
        local x = 1
        local y = 0
        local title = "TargetAffectingCombat"
        local nodeFrame = CreateFrame("Frame", addonName .. title .. "Frame", addonTable.MiscFrame)
        nodeFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        nodeFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        nodeFrame:SetSize(node_size, node_size)
        nodeFrame:Show()

        local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
        nodeTexture:SetAllPoints(nodeFrame)
        nodeTexture:SetColorTexture(0, 0, 0, 1)
        nodeTexture:Show()

        function UpdateNodeTexture()
            -- 更新目标战斗状态指示器
            -- 如果目标存在且处于战斗中，显示白色；否则显示黑色
            if UnitExists("target") and UnitAffectingCombat("target") then
                nodeTexture:SetColorTexture(1, 1, 1, 1)
            else
                nodeTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateNodeTexture)
    end

    do
        local x = 2
        local y = 0
        local title = "PlayerAffectingCombat"
        local nodeFrame = CreateFrame("Frame", addonName .. title .. "Frame", addonTable.MiscFrame)
        nodeFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        nodeFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        nodeFrame:SetSize(node_size, node_size)
        nodeFrame:Show()

        local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
        nodeTexture:SetAllPoints(nodeFrame)
        nodeTexture:SetColorTexture(0, 0, 0, 1)
        nodeTexture:Show()

        function UpdateNodeTexture()
            -- 更新玩家战斗状态指示器
            -- 如果玩家处于战斗中，显示白色；否则显示黑色
            if UnitAffectingCombat("player") then
                nodeTexture:SetColorTexture(1, 1, 1, 1)
            else
                nodeTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateNodeTexture)
    end

    do
        local x = 3
        local y = 0
        local title = "PlayerIsEmpowered"
        local nodeFrame = CreateFrame("Frame", addonName .. title .. "Frame", addonTable.MiscFrame)
        nodeFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        nodeFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        nodeFrame:SetSize(node_size, node_size)
        nodeFrame:Show()

        local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
        nodeTexture:SetAllPoints(nodeFrame)
        nodeTexture:SetColorTexture(0, 0, 0, 1)
        nodeTexture:Show()

        function UpdateNodeTexture()
            -- 更新玩家强化状态指示器
            -- 如果玩家正在引导强化技能，显示白色；否则显示黑色
            local _, _, _, _, _, _, _, _, isEmpowered, _, _ = UnitChannelInfo("player")
            if isEmpowered then
                nodeTexture:SetColorTexture(1, 1, 1, 1)
            else
                nodeTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateNodeTexture)
    end


    do
        local x = 4
        local y = 0
        local title = "TargetIsSelf"
        local nodeFrame = CreateFrame("Frame", addonName .. title .. "Frame", addonTable.MiscFrame)
        nodeFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        nodeFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        nodeFrame:SetSize(node_size, node_size)
        nodeFrame:Show()

        local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
        nodeTexture:SetAllPoints(nodeFrame)
        nodeTexture:SetColorTexture(0, 0, 0, 1)
        nodeTexture:Show()

        function UpdateNodeTexture()
            -- 更新目标是否为玩家自身指示器
            -- 如果目标存在且目标就是玩家自己，显示白色；否则显示黑色
            if UnitExists("target") and UnitIsUnit("target", "player") then
                nodeTexture:SetColorTexture(1, 1, 1, 1)
            else
                nodeTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateNodeTexture)
    end


    do
        local x = 5
        local y = 0
        local title = "SelfIsMoving"
        local nodeFrame = CreateFrame("Frame", addonName .. title .. "Frame", addonTable.MiscFrame)
        nodeFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        nodeFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        nodeFrame:SetSize(node_size, node_size)
        nodeFrame:Show()

        local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
        nodeTexture:SetAllPoints(nodeFrame)
        nodeTexture:SetColorTexture(0, 0, 0, 1)
        nodeTexture:Show()

        function UpdateNodeTexture()
            -- 更新玩家移动状态指示器
            -- 如果玩家正在移动，显示白色；否则显示黑色
            if GetUnitSpeed("player") > 0 then
                nodeTexture:SetColorTexture(1, 1, 1, 1)
            else
                nodeTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateNodeTexture)
    end

    do
        local x = 3
        local y = 1
        local title = "TargetIsAlive"
        local nodeFrame = CreateFrame("Frame", addonName .. title .. "Frame", addonTable.MiscFrame)
        nodeFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        nodeFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        nodeFrame:SetSize(node_size, node_size)
        nodeFrame:Show()

        local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
        nodeTexture:SetAllPoints(nodeFrame)
        nodeTexture:SetColorTexture(0, 0, 0, 1)
        nodeTexture:Show()

        function UpdateNodeTexture()
            if UnitExists("target") and (not UnitIsDeadOrGhost("target")) then
                nodeTexture:SetColorTexture(1, 1, 1, 1)
            else
                nodeTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateNodeTexture)
    end

    do
        local x = 4
        local y = 1
        local title = "TargetHealth"
        local nodeFrame = CreateFrame("Frame", addonName .. title .. "Frame", addonTable.MiscFrame)
        nodeFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        nodeFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        nodeFrame:SetSize(node_size, node_size)
        nodeFrame:Show()

        local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
        nodeTexture:SetAllPoints(nodeFrame)
        nodeTexture:SetColorTexture(0, 0, 0, 1)
        nodeTexture:Show()

        function UpdateNodeTexture()
            if UnitExists("target") then
                local color = UnitHealthPercent("target", usePredicted, curve)
                nodeTexture:SetColorTexture(color.r, color.g, color.b, 1)
            else
                nodeTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateNodeTexture)
    end

    do
        local x = 3
        local y = 2
        local title = "TargetInRange"
        local nodeFrame = CreateFrame("Frame", addonName .. title .. "Frame", addonTable.MiscFrame)
        nodeFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        nodeFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        nodeFrame:SetSize(node_size, node_size)
        nodeFrame:Show()

        local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
        nodeTexture:SetAllPoints(nodeFrame)
        nodeTexture:SetColorTexture(0, 0, 0, 1)
        nodeTexture:Show()

        function UpdateNodeTexture()
            if UnitExists("target") then
                local _, maxRange = LibRangeCheck:GetRange("target")
                if maxRange and (maxRange <= addonTable.RangeCheck) then
                    nodeTexture:SetColorTexture(1, 1, 1, 1)
                else
                    nodeTexture:SetColorTexture(0, 0, 0, 1)
                end
            else
                nodeTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateNodeTexture)
    end

    do
        local x = 5
        local y = 1
        local title = "SelfInVehicle"
        local nodeFrame = CreateFrame("Frame", addonName .. title .. "Frame", addonTable.MiscFrame)
        nodeFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        nodeFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        nodeFrame:SetSize(node_size, node_size)
        nodeFrame:Show()

        local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
        nodeTexture:SetAllPoints(nodeFrame)
        nodeTexture:SetColorTexture(0, 0, 0, 1)
        nodeTexture:Show()

        function UpdateNodeTexture()
            -- 更新玩家载具状态指示器
            -- 如果玩家在载具中或已坐骑，显示白色；否则显示黑色
            if UnitInVehicle("player") or IsMounted() then
                nodeTexture:SetColorTexture(1, 1, 1, 1)
            else
                nodeTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateNodeTexture)
    end

    do
        local x = 0
        local y = 1
        local targetCastingFrame = CreateFrame("Frame", addonName .. "TargetCastingFrame", addonTable.MiscFrame)
        targetCastingFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        targetCastingFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        targetCastingFrame:SetSize(node_size, node_size)
        targetCastingFrame:Show()

        local targetCastingTexture = targetCastingFrame:CreateTexture(nil, "BACKGROUND")
        targetCastingTexture:SetAllPoints(targetCastingFrame)
        targetCastingTexture:SetColorTexture(0, 0, 0, 1)
        targetCastingTexture:Show()

        x = 1

        local targetCastingDurationFrame = CreateFrame("Frame", addonName .. "TargetCastingDurationFrame", addonTable.MiscFrame)
        targetCastingDurationFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        targetCastingDurationFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        targetCastingDurationFrame:SetSize(node_size, node_size)
        targetCastingDurationFrame:Show()

        local targetCastingDurationTexture = targetCastingDurationFrame:CreateTexture(nil, "BACKGROUND")
        targetCastingDurationTexture:SetAllPoints(targetCastingDurationFrame)
        targetCastingDurationTexture:SetColorTexture(0, 0, 0, 1)
        targetCastingDurationTexture:Show()

        x = 2

        local targetCastingInterruptibleFrame = CreateFrame("Frame", addonName .. "TargetCastingInterruptibleFrame", addonTable.MiscFrame)
        targetCastingInterruptibleFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        targetCastingInterruptibleFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        targetCastingInterruptibleFrame:SetSize(node_size, node_size)
        targetCastingInterruptibleFrame:Show()

        local targetCastingInterruptibleTexture = targetCastingInterruptibleFrame:CreateTexture(nil, "BACKGROUND")
        targetCastingInterruptibleTexture:SetAllPoints(targetCastingInterruptibleFrame)
        targetCastingInterruptibleTexture:SetColorTexture(0, 0, 0, 1)
        targetCastingInterruptibleTexture:Show()

        function UpdateTexture()
            -- 更新目标施法状态指示器
            -- 如果目标存在且正在施法，显示施法图标；否则显示黑色
            if UnitExists("target") then
                local _, _, textureID, _, _, _, _, notInterruptible, _, _ = UnitCastingInfo("target")
                if textureID then
                    targetCastingTexture:SetTexture(textureID)
                    targetCastingInterruptibleTexture:SetColorTexture(C_CurveUtil.EvaluateColorFromBoolean(notInterruptible, { r = 0, g = 0, b = 0, a = 1 }, { r = 1, g = 1, b = 1, a = 1 }):GetRGBA())
                    local duration = UnitCastingDuration("target")
                    local result = duration:EvaluateElapsedPercent(curve)
                    targetCastingDurationTexture:SetColorTexture(result.r, result.g, result.b, 1)
                else
                    targetCastingTexture:SetColorTexture(0, 0, 0, 1)
                    targetCastingDurationTexture:SetColorTexture(0, 0, 0, 1)
                    targetCastingInterruptibleTexture:SetColorTexture(0, 0, 0, 1)
                end
            else
                targetCastingTexture:SetColorTexture(0, 0, 0, 1)
                targetCastingDurationTexture:SetColorTexture(0, 0, 0, 1)
                targetCastingInterruptibleTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateTexture)
    end


    do
        local x = 0
        local y = 2
        local targetChannelFrame = CreateFrame("Frame", addonName .. "TargetChannelFrame", addonTable.MiscFrame)
        targetChannelFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        targetChannelFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        targetChannelFrame:SetSize(node_size, node_size)
        targetChannelFrame:Show()

        local targetChannelTexture = targetChannelFrame:CreateTexture(nil, "BACKGROUND")
        targetChannelTexture:SetAllPoints(targetChannelFrame)
        targetChannelTexture:SetColorTexture(0, 0, 0, 1)
        targetChannelTexture:Show()

        x = 1

        local targetChannelDurationFrame = CreateFrame("Frame", addonName .. "TargetChannelDurationFrame", addonTable.MiscFrame)
        targetChannelDurationFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        targetChannelDurationFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        targetChannelDurationFrame:SetSize(node_size, node_size)
        targetChannelDurationFrame:Show()

        local targetChannelDurationTexture = targetChannelDurationFrame:CreateTexture(nil, "BACKGROUND")
        targetChannelDurationTexture:SetAllPoints(targetChannelDurationFrame)
        targetChannelDurationTexture:SetColorTexture(0, 0, 0, 1)
        targetChannelDurationTexture:Show()

        x = 2

        local targetChannelInterruptibleFrame = CreateFrame("Frame", addonName .. "TargetChannelInterruptibleFrame", addonTable.MiscFrame)
        targetChannelInterruptibleFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size, -y * node_size)
        targetChannelInterruptibleFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
        targetChannelInterruptibleFrame:SetSize(node_size, node_size)
        targetChannelInterruptibleFrame:Show()

        local targetChannelInterruptibleTexture = targetChannelInterruptibleFrame:CreateTexture(nil, "BACKGROUND")
        targetChannelInterruptibleTexture:SetAllPoints(targetChannelInterruptibleFrame)
        targetChannelInterruptibleTexture:SetColorTexture(0, 0, 0, 1)
        targetChannelInterruptibleTexture:Show()

        function UpdateTexture()
            if UnitExists("target") then
                local _, _, textureID, _, _, _, notInterruptible = UnitChannelInfo("target")
                if textureID then
                    targetChannelTexture:SetTexture(textureID)
                    targetChannelInterruptibleTexture:SetColorTexture(C_CurveUtil.EvaluateColorFromBoolean(notInterruptible, { r = 0, g = 0, b = 0, a = 1 }, { r = 1, g = 1, b = 1, a = 1 }):GetRGBA())
                    local duration = UnitChannelDuration("target")
                    local result = duration:EvaluateElapsedPercent(curve)
                    targetChannelDurationTexture:SetColorTexture(result.r, result.g, result.b, 1)
                else
                    targetChannelTexture:SetColorTexture(0, 0, 0, 1)
                    targetChannelDurationTexture:SetColorTexture(0, 0, 0, 1)
                    targetChannelInterruptibleTexture:SetColorTexture(0, 0, 0, 1)
                end
            else
                targetChannelTexture:SetColorTexture(0, 0, 0, 1)
                targetChannelDurationTexture:SetColorTexture(0, 0, 0, 1)
                targetChannelInterruptibleTexture:SetColorTexture(0, 0, 0, 1)
            end
        end

        table.insert(addonTable.UpdateFuncs, UpdateTexture)
    end



    log("MiscFrame created")
end

table.insert(addonTable.FrameInitFuncs, InitializeMiscFrame)
