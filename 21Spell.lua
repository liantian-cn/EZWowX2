-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local insert                = table.insert

-- 插件级变量定义/引用

local Cell                  = addonTable.Cell
addonTable.ClassSpells      = {}

-- 本地变量定义










-- 开始代码

local function InitSpellFrame()
    Cell:New(0, 0, 255, 1, 255) -- 标记位：
    Cell:New(0, 1, 255, 1, 255) -- 标记为
end
insert(addonTable.FrameInitFuncs, InitSpellFrame)
