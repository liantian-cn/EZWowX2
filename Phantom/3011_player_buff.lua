-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存

-- 插件级变量定义/引用
local CreateAuraSlotContainer = addonTable.CreateAuraSlotContainer
local PLAYER_BUFF_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_BUFF

-- 本地变量定义
local insert = table.insert

-- 代码部分
addonTable.PLAYER_BUFF_LIST = {
    { description = "爪子", spellIDs = { 1126, 1128 } },
    { description = "萌芽", spellIDs = { 155777 } },
    { description = "回春", spellIDs = { 778, 774 } },
    { description = "愈合", spellIDs = { 8936, 8938 } },
    { description = "野性成长", spellIDs = { 48438 } },
}

insert(addonTable.PLAYER_BUFF_LIST, {
    description = "生命绽放",
    spellIDs = { 33763 },
})

insert(addonTable.PLAYER_BUFF_LIST, {
    description = "清晰预兆",
    spellIDs = { 16870, 16872 },
})

insert(addonTable.PLAYER_BUFF_LIST, {
    description = "树皮术",
    spellIDs = { 22812 },
})

insert(addonTable.PLAYER_BUFF_LIST, {
    description = "自然迅捷",
    spellIDs = { 132158 },
})

--[[
简述：      玩家Buff信息
分类：      玩家Buff信息
分类索引：  1-9，由PLAYER_BUFF_LIST顺序确定
位置：      从视觉第3行、零基X偏移11（视觉第12列）开始，向右延伸，共9个宽3高4的固定AuraSlot

说明

通过受管AuraSlotContainer显示由玩家施放且位于PLAYER_BUFF_LIST中的增益效果。
每项description仅用于提高维护时的可读性，不参与Aura过滤。
]]

local function InitFrame()
    CreateAuraSlotContainer({
        x = 11,
        y = 3,
        unitToken = "player",
        filterString = "PLAYER|HELPFUL",
        classification = PLAYER_BUFF_CLASSIFICATION,
        slots = addonTable.PLAYER_BUFF_LIST,
    })
end

insert(addonTable.FrameInitFuncs, InitFrame)
