-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存

-- 插件级变量定义/引用
local CreateAuraGroupContainer = addonTable.CreateAuraGroupContainer
local PLAYER_DEBUFF_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_DEBUFF

-- 本地变量定义
local insert = table.insert

-- 代码部分

--[[
简述：      玩家Debuff信息
分类：      玩家Debuff信息
分类索引：  动态，最多4个
位置：      从35列3行开始，向右延伸，最多4个宽3高4的AuraGroup

说明

通过AuraGroupContainer显示位于玩家身上、满足团队框架过滤条件、
且非玩家自行施放的有害效果。
maxDuration = 120 排除持续时间超过120秒的Aura，同时隐式排除永久Aura。
]]

local function InitFrame()
    CreateAuraGroupContainer({
        x = 35,
        y = 3,
        unitToken = "player",
        filterString = "HARMFUL|RAID|!PLAYER",
        classification = PLAYER_DEBUFF_CLASSIFICATION,
        maxFrameCount = 4,
        candidateFilters = {
            maxDuration = 120,
        },
    })
end

insert(addonTable.FrameInitFuncs, InitFrame)
