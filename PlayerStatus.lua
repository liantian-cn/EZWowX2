local addonName, addonTable = ...

-- 初始化玩家状态框架
-- 为玩家创建生命值和能量值显示节点
-- 通过颜色渐变表示生命值和能量值的百分比，使用正向曲线（从黑到白）
local function InitializePlayerStatusFrame()
    local node_size = addonTable.nodeSize
    local curve = addonTable.curve

    do
        local player_hp_frame = CreateFrame("Frame", addonName .. "HPFrame", addonTable.PlayerStatusFrame)
        player_hp_frame:SetPoint("TOPLEFT", addonTable.PlayerStatusFrame, "TOPLEFT", 0, 0)
        player_hp_frame:SetFrameLevel(addonTable.PlayerStatusFrame:GetFrameLevel() + 1)
        player_hp_frame:SetSize(node_size, node_size)
        player_hp_frame:Show()

        local player_hp_texture = player_hp_frame:CreateTexture(nil, "BACKGROUND")
        player_hp_texture:SetAllPoints(player_hp_frame)
        player_hp_texture:SetColorTexture(0, 0, 0, 1)
        player_hp_texture:Show()

        local function UpdateHPTexture()
            -- 更新玩家生命值节点的纹理颜色
            -- 根据玩家的生命值百分比，使用正向曲线计算颜色
            -- 生命值越低，颜色越接近黑色；生命值满时，颜色接近白色
            local usePredicted = true
            local color = UnitHealthPercent("player", usePredicted, curve)
            player_hp_texture:SetColorTexture(color.r, color.g, color.b, 1)
        end

        table.insert(addonTable.UpdateFuncs, UpdateHPTexture)
    end

    do
        local player_power_frame = CreateFrame("Frame", addonName .. "PowerFrame", addonTable.PlayerStatusFrame)
        player_power_frame:SetPoint("TOPLEFT", addonTable.PlayerStatusFrame, "TOPLEFT", 0, -1 * node_size)
        player_power_frame:SetFrameLevel(addonTable.PlayerStatusFrame:GetFrameLevel() + 1)
        player_power_frame:SetSize(node_size, node_size)
        player_power_frame:Show()

        local player_power_texture = player_power_frame:CreateTexture(nil, "BACKGROUND")
        player_power_texture:SetAllPoints(player_power_frame)
        player_power_texture:SetColorTexture(0, 0, 0, 1)
        player_power_texture:Show()
        local powerType, _ = UnitPowerType("player")

        local function UpdatePowerTexture()
            -- 更新玩家能量值节点的纹理颜色
            -- 根据玩家的能量值百分比，使用正向曲线计算颜色
            -- 能量值越低，颜色越接近黑色；能量值满时，颜色接近白色
            local usePredicted = true
            local color = UnitPowerPercent("player", powerType, usePredicted, curve)
            player_power_texture:SetColorTexture(color.r, color.g, color.b, 1)
        end
        table.insert(addonTable.UpdateFuncs, UpdatePowerTexture)
    end
end
table.insert(addonTable.FrameInitFuncs, InitializePlayerStatusFrame)
