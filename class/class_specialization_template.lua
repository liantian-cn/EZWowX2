-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local GetSpecialization     = GetSpecialization


--[[
简述：     XX职业  XX专精定义文件


]]



-- 开始代码
local currentSpec = GetSpecialization()

if UnitClassBase("player") ~= "DRUID" then return end -- 如果不是德鲁伊职业，则不加载该文件
if currentSpec ~= 4 then return end                   -- 如果不是恢复专精，则不加载该文件


--[[
技能冷却表
说明：
- 第一个固定是公共冷却，spellId 固定为 61304
- index从1开始，必须连续。

]]

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    -- [2] = { spellId = 999999, description = "技能A" },
    -- [3] = { spellId = 888888, description = "技能B" },
}

--[[
充能技能表
说明：
- index从1开始，必须连续。
- minValue是充能技能的最小值，maxValue是充能技能的最大值。用于图像展示。
- 当差值小于16时，获得最好的精度，但也无所谓啦。
]]

addonTable.SPEC.ChargeList = {
    [1] = { spellId = 999999, description = "技能A", minValue = 0, maxValue = 2 },
}

--[[
玩家增益监控表。
说明：
- index从1开始，必须连续。
- 这里可以添加超过10个槽位，但实际运行中，超过10个的会被抛弃。
- 有些buff，在不同天赋下有不同的ID，这里可以兼容。
]]

addonTable.SPEC.PlayerBuff = {
    [1] = { description = "爪子", spellIDs = { 1126, 1128 } },
    [2] = { description = "萌芽", spellIDs = { 155777 } },
    [3] = { description = "回春", spellIDs = { 778, 774 } },
    [4] = { description = "愈合", spellIDs = { 8936, 8938 } },
    [5] = { description = "野性成长", spellIDs = { 48438 } },
    [6] = { description = "生命绽放", spellIDs = { 33763 } },
    [7] = { description = "清晰预兆", spellIDs = { 16870, 16872 } },
}

--[[
目标减益监控表。
说明：
- index从1开始，必须连续。
- 这里可以添加超过9个槽位，但实际运行中，超过9个的会被抛弃。
- 有些buff，在不同天赋下有不同的ID，这里可以兼容。
]]

addonTable.SPEC.TargetDebuff = {
    [1] = { description = "月火数", spellIDs = { 8921 } },
}
