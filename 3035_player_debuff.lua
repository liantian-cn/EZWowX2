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
        -- filterString = "HARMFUL|RAID|!PLAYER",
        filterString = "HARMFUL|RAID",
        classification = PLAYER_DEBUFF_CLASSIFICATION,
        maxFrameCount = 4,
        candidateFilters = {
            -- maxDuration = 120,
        },
    })
end

insert(addonTable.FrameInitFuncs, InitFrame)

-- | Token | 含义 |
-- | --- | --- |
-- | `HELPFUL` | helpful aura。 |
-- | `HARMFUL` | harmful aura。 |
-- | `RAID` | 满足团队框架过滤条件的 Aura。 |
-- | `INCLUDE_NAME_PLATE_ONLY` | 包含标记为仅姓名板显示的 Aura。 |
-- | `PLAYER` | 由玩家施放。 |
-- | `CANCELABLE` | 玩家可取消。 |
-- | `MAW` | Maw 相关 Aura。 |
-- | `EXTERNAL_DEFENSIVE` | 外部防御效果。 |
-- | `CROWD_CONTROL` | 控制效果。 |
-- | `RAID_IN_COMBAT` | 战斗中应在团队框架显示的 Aura。 |
-- | `RAID_PLAYER_DISPELLABLE` | 玩家当前可驱散的 Aura。 |
-- | `BIG_DEFENSIVE` | 大型防御效果。 |
