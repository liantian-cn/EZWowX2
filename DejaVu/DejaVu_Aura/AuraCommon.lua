local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local pairs = pairs
local wipe = wipe

-- WoW 官方 API
local GetUnitAuraInstanceIDs = C_UnitAuras.GetUnitAuraInstanceIDs                 -- 读取单位 aura 实例 ID 列表
local GetAuraDataByAuraInstanceID = C_UnitAuras.GetAuraDataByAuraInstanceID       -- 读取 aura 数据
local GetAuraDuration = C_UnitAuras.GetAuraDuration                               -- 读取 aura 剩余时长对象
local GetAuraApplicationDisplayCount = C_UnitAuras.GetAuraApplicationDisplayCount -- 读取 aura 层数字符串
local DoesAuraHaveExpirationTime = C_UnitAuras.DoesAuraHaveExpirationTime         -- 判断 aura 是否会自然结束
local GetAuraDispelTypeColor = C_UnitAuras.GetAuraDispelTypeColor                 -- 按曲线映射 aura 类型颜色
local CreateColorCurve = C_CurveUtil.CreateColorCurve
local EvaluateColorFromBoolean = C_CurveUtil.EvaluateColorFromBoolean             -- 把布尔值映射成颜色
local UnitExists = UnitExists                                                     -- 本地化单位存在判断
local UnitCanAttack = UnitCanAttack                                               -- 本地化敌对判断

-- DejaVu Core
local DejaVu = _G["DejaVu"]
local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell
local BadgeCell = DejaVu.BadgeCell
local CharCell = DejaVu.CharCell


local remainingCurve = CreateColorCurve()
remainingCurve:SetType(Enum.LuaCurveType.Linear)
remainingCurve:AddPoint(0.0, COLOR.C0)
remainingCurve:AddPoint(5.0, COLOR.C100)
remainingCurve:AddPoint(30.0, COLOR.C150)
remainingCurve:AddPoint(155.0, COLOR.C200)
remainingCurve:AddPoint(375.0, COLOR.C255)

local debuffOnFriendlyCurve = CreateColorCurve()
debuffOnFriendlyCurve:AddPoint(0, COLOR.SPELL_TYPE.DEBUFF_ON_FRIENDLY)
debuffOnFriendlyCurve:AddPoint(1, COLOR.SPELL_TYPE.MAGIC)
debuffOnFriendlyCurve:AddPoint(2, COLOR.SPELL_TYPE.CURSE)
debuffOnFriendlyCurve:AddPoint(3, COLOR.SPELL_TYPE.DISEASE)
debuffOnFriendlyCurve:AddPoint(4, COLOR.SPELL_TYPE.POISON)
debuffOnFriendlyCurve:AddPoint(9, COLOR.SPELL_TYPE.ENRAGE)
debuffOnFriendlyCurve:AddPoint(11, COLOR.SPELL_TYPE.BLEED)

local function InitCells(maxAuraCount, baseX, baseY)
    local cells = {}
    for i = 1, maxAuraCount do
        local x = baseX - 2 + 2 * i -- 计算当前槽位 x 坐标
        local y = baseY             -- 当前槽位 y 坐标

        -- x:baseX - 2 + 2 * i y:baseY
        -- 用途：aura 图标
        -- 更新函数：drawCell、refreshAll
        local iconCell = BadgeCell:New(x, y)

        -- x:baseX - 2 + 2 * i y:baseY + 2
        -- 用途：aura 剩余时间颜色
        -- 更新函数：drawCell、refreshAll、updateRemaining、updateRemainingAll
        local remainingCell = Cell:New(x, y + 2)

        -- x:baseX - 1 + 2 * i y:baseY + 2
        -- 用途：aura 类型颜色
        -- 更新函数：drawCell、refreshAll
        local spellTypeCell = Cell:New(x + 1, y + 2)

        -- x:baseX - 2 + 2 * i y:baseY + 3
        -- 用途：aura 层数字符串
        -- 更新函数：drawCell、refreshAll、updateRemaining、updateRemainingAll
        local countCell = CharCell:New(x, y + 3)

        cells[i] = {
            icon = iconCell,
            remaining = remainingCell,
            spellType = spellTypeCell,
            count = countCell,
            instanceID = nil,
        }
    end
    return cells
end

local function clearCell(cell)
    cell.icon:clearCell()
    cell.remaining:clearCell()
    cell.spellType:clearCell()
    cell.count:clearCell()
    cell.instanceID = nil
end

local function CreateAuraController(options)
    local unitKey = options.unitKey
    local auraFilter = options.auraFilter
    local maxAuraCount = options.maxAuraCount
    local baseX = options.baseX
    local baseY = options.baseY
    local sortRule = options.sortRule
    local sortDirection = options.sortDirection
    local colorMode = options.colorMode

    local cells = InitCells(maxAuraCount, baseX, baseY)
    local instanceIDMap = {}
    local isEnemy = true

    local function getSpellTypeColor(instanceID)
        if isEnemy then
            return COLOR.SPELL_TYPE.DEBUFF_ON_ENEMY
        end
        if colorMode == "Helpful" then
            return COLOR.SPELL_TYPE.BUFF_ON_FRIENDLY
        end
        if colorMode == "Harmful" then
            return GetAuraDispelTypeColor(unitKey, instanceID, debuffOnFriendlyCurve)
        end

        return GetAuraDispelTypeColor(unitKey, instanceID, debuffOnFriendlyCurve)
    end

    -- 说明：把指定 aura 的图标、剩余时间、类型和层数写入单个槽位。
    -- 依赖事件更新：addAura、removeAura、refreshAll 等结构刷新流程调用。
    -- 依赖定时刷新：无。
    local function drawCell(cell, instanceID)
        local aura = GetAuraDataByAuraInstanceID(unitKey, instanceID) -- 取当前 aura 数据
        if aura == nil then
            clearCell(cell)
            return false
        end
        cell.instanceID = instanceID

        local remaining = GetAuraDuration(unitKey, instanceID)                  -- 剩余时间对象
        local count = GetAuraApplicationDisplayCount(unitKey, instanceID, 1, 9) -- 取层数字符串
        local spellTypeColor = getSpellTypeColor(instanceID)                    -- 本次 aura 的边框 / 类型颜色

        cell.icon:setCell(aura.icon, spellTypeColor, aura.name)
        cell.remaining:setCell(
            EvaluateColorFromBoolean(
                DoesAuraHaveExpirationTime(unitKey, instanceID),
                remaining:EvaluateRemainingDuration(remainingCurve),
                COLOR.WHITE
            ))
        cell.spellType:setCell(spellTypeColor)
        cell.count:setCell(count)
        return true
    end

    local function findFirstEmptyCellIndex()
        for i = 1, maxAuraCount do
            if cells[i].instanceID == nil then
                return i
            end
        end
    end

    local function compactCellsFrom(startIndex)
        local writeIndex = startIndex
        local readIndex = startIndex + 1

        while writeIndex <= maxAuraCount do
            while readIndex <= maxAuraCount and cells[readIndex].instanceID == nil do
                readIndex = readIndex + 1
            end

            if readIndex > maxAuraCount then
                for i = writeIndex, maxAuraCount do
                    clearCell(cells[i])
                end
                return
            end

            local nextInstanceID = cells[readIndex].instanceID
            instanceIDMap[nextInstanceID] = writeIndex

            if not drawCell(cells[writeIndex], nextInstanceID) then
                instanceIDMap[nextInstanceID] = nil
                clearCell(cells[writeIndex])
            end

            writeIndex = writeIndex + 1
            readIndex = readIndex + 1
        end
    end

    local function removeAura(instanceID)
        local index = instanceIDMap[instanceID]
        if index == nil then
            return
        end

        instanceIDMap[instanceID] = nil
        compactCellsFrom(index)
    end

    local function addAura(instanceID)
        if instanceID == nil then
            return
        end

        local index = instanceIDMap[instanceID]
        if index ~= nil then
            drawCell(cells[index], instanceID)
            return
        end

        index = findFirstEmptyCellIndex()
        if index == nil then
            return
        end

        instanceIDMap[instanceID] = index
        if not drawCell(cells[index], instanceID) then
            instanceIDMap[instanceID] = nil
            clearCell(cells[index])
        end
    end

    -- 说明：按当前单位的 aura 列表全量重建所有显示槽位和实例映射。
    -- 依赖事件更新：UNIT_AURA、目标切换、单位变化等结构刷新事件。
    -- 依赖定时刷新：MouseoverHarmful.lua 的 0.5 秒轮询补刷。
    local function refreshAll()
        wipe(instanceIDMap)

        if not UnitExists(unitKey) then -- 单位不存在时直接清空
            for i = 1, maxAuraCount do
                clearCell(cells[i])
            end
            return
        end
        isEnemy = UnitCanAttack("player", unitKey) -- 判断目标是否为敌对

        local auraInstanceIDs = GetUnitAuraInstanceIDs(unitKey, auraFilter, maxAuraCount, sortRule, sortDirection) or {}
        for i = 1, maxAuraCount do
            local cell = cells[i]
            local instanceID = auraInstanceIDs[i]
            if instanceID == nil then
                clearCell(cell)
            else
                if drawCell(cell, instanceID) then
                    instanceIDMap[instanceID] = i
                end
            end
        end
    end

    -- 说明：只更新指定 aura 的剩余时间颜色和层数，不重排槽位。
    -- 依赖事件更新：UNIT_AURA 的 updatedAuraInstanceIDs 精细更新。
    -- 依赖定时刷新：PlayerHelpful.lua 和 PlayerHarmful.lua 的 0.1 秒轮询。
    local function updateRemaining(instanceID)
        local index = instanceIDMap[instanceID]
        if index == nil then
            return
        end
        local cell = cells[index]
        local remaining = GetAuraDuration(unitKey, instanceID) -- 剩余时间对象
        if remaining then
            cell.remaining:setCell(
                EvaluateColorFromBoolean(
                    DoesAuraHaveExpirationTime(unitKey, instanceID),
                    remaining:EvaluateRemainingDuration(remainingCurve),
                    COLOR.WHITE
                ))
        else
            cell.remaining:setCell(COLOR.WHITE)
        end

        local count = GetAuraApplicationDisplayCount(unitKey, instanceID, 1, 9) -- 取层数字符串
        cell.count:setCell(count)
    end

    -- 说明：遍历当前所有已映射 aura，批量更新时间颜色和层数。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：PlayerHelpful.lua 和 PlayerHarmful.lua 的 0.1 秒轮询。
    local function updateRemainingAll()
        for instanceID in pairs(instanceIDMap) do
            updateRemaining(instanceID)
        end
    end

    return {
        addAura = addAura,
        refreshAll = refreshAll,
        removeAura = removeAura,
        updateRemaining = updateRemaining,
        updateRemainingAll = updateRemainingAll,
    }
end

addonTable.CreateAuraController = CreateAuraController
_G["DejaVu_Aura"] = addonTable
