-- 命名空间声明
local addonName, addonTable    = ...

-- WOW API 缓存
local insert                   = table.insert
local GetSpellCooldownDuration = C_Spell.GetSpellCooldownDuration
local IsSpellOverlayed         = C_SpellActivationOverlay.IsSpellOverlayed
local IsSpellUsable            = C_Spell.IsSpellUsable

-- 插件级变量定义/引用

local Cell                     = addonTable.Cell
addonTable.ClassSpells         = {}

-- 本地变量定义




local CommonSpells = {
    [1] = { spellId = 61304, name = "公共冷却" },
}


-- 说明
-- 技能冷却在第一行，2个标记为后开始
-- 每个技能冷却占用4个cell
-- 第一个：remainingCell，表示技能冷却剩余，通过 remaining = GetSpellCooldownDuration(spellID) 获得冷却对象，使用 remaining:EvaluateRemainingDuration(cell.quantizedCurve)获得冷却颜色，最后setCell更新颜色
-- 第二个：usableCell，表示技能是否可用，使用IsSpellUsable(spellID)获取技能是否可用的状态，使用setCellBoolean赋值颜色。
-- 第三个：overlayedCell，表示技能是否高亮，使用IsSpellOverlayed(spellID)获取技能是否高亮的状态，使用setCellBoolean赋值颜色。
-- 第四个：empty1Cell, 占位符，暂时没想到做啥。


-- 开始代码


local eventFrame = CreateFrame("Frame")
eventFrame:SetScript("OnEvent", function(self, event, ...)
    self[event](...)
end)

local function InitSpellFrame()
    Cell:New(1, 1, 255, 1, 1) -- 标记位：标记为的classification为255。技能冷却的classification为1，所以标记位的value为1。
    Cell:New(2, 1, 255, 2, 1) -- 标记位：标记为的classification为255。技能冷却的classification为1，所以标记位的value为1。

    local offsetX = 3         -- 从第3列开始放置技能图标
    local offsetIndex = 0     -- index 从零开始。每个cell增1。

    local allSpells = {}

    for _, spell in ipairs(CommonSpells) do
        insert(allSpells, spell)
    end

    for _, spell in ipairs(addonTable.ClassSpells) do
        insert(allSpells, spell)
    end

    for i, spell in ipairs(allSpells) do
        -- 及冷却的classification为1，value默认为255
        local remainingCell = Cell:New(offsetX, 1, 1, offsetIndex, 0)
        offsetIndex = offsetIndex + 1
        offsetX = offsetX + 1
        local usableCell = Cell:New(offsetX, 1, 1, offsetIndex, 0)
        offsetIndex = offsetIndex + 1
        offsetX = offsetX + 1
        local overlayedCell = Cell:New(offsetX, 1, 1, offsetIndex, 0)
        offsetIndex = offsetIndex + 1
        offsetX = offsetX + 1
        local empty1Cell = Cell:New(offsetX, 1, 1, offsetIndex, 0)
    end
end
insert(addonTable.FrameInitFuncs, InitSpellFrame)
