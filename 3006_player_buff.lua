-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存

-- 插件级变量定义/引用
local CreateAuraContainer = addonTable.CreateAuraContainer

addonTable.PLAYER_BUFF_LIST = {
    [1126] = true,   -- 爪子
    [155777] = true, -- 萌芽
    [774] = true,    -- 回春
    [8936] = true,   -- 愈合
    [48438] = true,  -- 野性成长
    [33763] = true,  -- 生命绽放
    [16870] = true,  -- 清晰预兆
}

-- 本地变量定义
local insert = table.insert

-- 代码部分

--[[
简述：      玩家Buff信息
分类：      玩家Buff信息
分类索引：  无
位置：      从3行6列开始，向右延伸，总计10个 宽3高4的Aura实例

说明

通过受管AuraContainer显示由玩家施放且位于PLAYER_BUFF_LIST中的增益效果。

]]

local function InitFrame()
    CreateAuraContainer({
        x = 6,
        y = 3,
        maxFrameCount = 10,
        unitToken = "player",
        filterString = "PLAYER|HELPFUL",
        candidateFilters = {
            includeSpellIDs = addonTable.PLAYER_BUFF_LIST,
        },
    })
end

insert(addonTable.FrameInitFuncs, InitFrame)
