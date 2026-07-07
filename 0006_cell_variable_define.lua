-- 命名空间声明
local addonName, addonTable = ...



-- 说明
-- 每个cell的RGB值分别有不同的涵义
-- R: 分类（根据cell用途不同，每个cell有个分类设置，范围0-255）
-- G: 索引（相同分类的cell，每个cell有个索引设置，范围0-255），代表同一个分类下的不同cell。
-- B: Value（根据cell用途不同，每个cell有个value设置，范围0-255），由解码器解析。

-- 以上逻辑确保了，即便无法准确定位像素的坐标，也能通过RGB值来传输数据，解码器可以根据RGB值来解析出cell的分类、索引和value，从而实现数据的传输和解析。


local CELL_CLASSIFICATION = {
    MARKER = 255,       -- 标记分类，用于定位的Cell，index表示处于第几行，value=0代表左侧开始，value=255代表右侧结束。
    PLAYER_STATUS = 5,  -- 玩家状态分类，index代表第几个，value各不相同。
    TARGET_STATUS = 10, -- 目标状态分类，index代表第几个，value各不相同。
    FOCUS_TARGET = 15,  -- 焦点目标分类，index代表第几个，value各不相同。
}
addonTable.CELL_CLASSIFICATION = CELL_CLASSIFICATION
