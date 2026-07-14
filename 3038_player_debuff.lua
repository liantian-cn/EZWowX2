-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local Debuff = AuraUtil.AuraUpdateChangedType.Debuff
local UnitFrameDebuff = AuraContainerSortMethod.UnitFrameDebuff

-- 插件级变量定义/引用
local CreateAuraGroupContainer = addonTable.CreateAuraGroupContainer
local PLAYER_DEBUFF_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_DEBUFF

-- 本地变量定义
local insert = table.insert

-- 代码部分

--[[
简述：      玩家Debuff信息
分类：      玩家Debuff信息
分类索引：  动态，最多5组
位置：      从视觉第3行、零基X偏移38（视觉第39列）开始，向右延伸，最多5个宽3高4的AuraGroup

说明

通过AuraGroupContainer显示位于玩家身上、经AuraUtil.ProcessAura处理后的官方主减益Debuff子集。
该组有意排除Dispel分类。
]]

local function InitFrame()
    CreateAuraGroupContainer({
        x = 38,
        y = 3,
        unitToken = "player",
        filterString = "HARMFUL",
        classification = PLAYER_DEBUFF_CLASSIFICATION,
        maxFrameCount = 5,
        processAuraOptions = {
            ignoreBuffs = true,
            ignoreDispelDebuffs = true,
        },
        candidateFilters = {
            processedAuraType = Debuff,
        },
        sortMethod = UnitFrameDebuff,
    })
end

insert(addonTable.FrameInitFuncs, InitFrame)
