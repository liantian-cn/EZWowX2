-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
-- local CreateColor           = CreateColor
-- local CreateFrame           = CreateFrame
-- local issecretvalue         = issecretvalue
-- local UnitCastingDuration   = UnitCastingDuration
-- local UnitCastingInfo       = UnitCastingInfo
-- local UnitChannelDuration   = UnitChannelDuration
-- local UnitChannelInfo       = UnitChannelInfo
-- local UnitExists            = UnitExists

-- 插件级变量定义/引用
-- local Cell                  = addonTable.Cell
-- local IconCell              = addonTable.IconCell

-- 本地变量定义
-- local insert                = table.insert
-- local select                = select
-- 代码部分

--[[
简述：      玩家Buff信息
分类：      玩家Buff信息
分类索引：  无
位置：      从3行6列开始，向右延伸，总计10个 宽3高4的Aura实例

说明

显示焦点施法或引导进度、可中断状态和当前施法图标。施法纹理、可中断标记和持续时间对象使用secret检查后再显示。

]]

addonTable.PLAYER_BUFF_LIST = {
    1126,   -- 爪子
    155777, -- 萌芽
    774,    -- 回春
    8936,   -- 愈合
    48438,  -- 野性成长
    33763,  -- 生命绽放
    16870,  -- 清晰预兆
}
