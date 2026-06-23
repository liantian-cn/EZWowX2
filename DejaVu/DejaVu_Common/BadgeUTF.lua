-- luacheck: globals C_Timer CreateFrame

-- Lua 原生函数
local byte = string.byte
local sub = string.sub
local len = string.len
local random = math.random
local insert = table.insert

-- WoW 官方 API
local CreateFrame = CreateFrame

local DejaVu = _G["DejaVu"]
local BadgeTitleTable = DejaVu.BadgeTitleTable
local Cell = DejaVu.Cell
local BadgeCell = DejaVu.BadgeCell
local MartixInitFuncs = DejaVu.MartixInitFuncs

local ROTATE_INTERVAL = 0.5
local UTF_CELL_COUNT = 16

local function char_to_rgb(char)
    local b1, b2, b3 = byte(char, 1, 3)
    return b1 or 0, b2 or 0, b3 or 0
end

local function split_utf8_chars(text)
    local chars = {}
    local index = 1
    local textLength = len(text)

    while index <= textLength do
        local currentByte = byte(text, index)
        local charLength = 1

        if currentByte >= 240 then
            charLength = 4
        elseif currentByte >= 224 then
            charLength = 3
        elseif currentByte >= 192 then
            charLength = 2
        end

        chars[#chars + 1] = sub(text, index, index + charLength - 1)
        index = index + charLength
    end

    return chars
end

local function clear_utf_cells(utfCells)
    for index = 1, UTF_CELL_COUNT do
        utfCells[index]:clearCell()
    end
end

local function render_utf_title(utfCells, title)
    local wrappedTitle = "*#" .. title .. "*#"
    local chars = split_utf8_chars(wrappedTitle)

    for index = 1, UTF_CELL_COUNT do
        local char = chars[index]

        if char then
            local r, g, b = char_to_rgb(char)
            utfCells[index]:setCellRGBA(r / 255, g / 255, b / 255, 1)
        else
            utfCells[index]:clearCell()
        end
    end
end

local function InitFrame()
    local eventFrame = CreateFrame("Frame")
    local IconCell = BadgeCell:New(64, 26)
    local UTFCells = {
        [1] = Cell:New(66, 26),
        [2] = Cell:New(67, 26),
        [3] = Cell:New(68, 26),
        [4] = Cell:New(69, 26),
        [5] = Cell:New(70, 26),
        [6] = Cell:New(71, 26),
        [7] = Cell:New(72, 26),
        [8] = Cell:New(73, 26),
        [9] = Cell:New(74, 26),
        [10] = Cell:New(75, 26),
        [11] = Cell:New(76, 26),
        [12] = Cell:New(77, 26),
        [13] = Cell:New(78, 26),
        [14] = Cell:New(79, 26),
        [15] = Cell:New(80, 26),
        [16] = Cell:New(81, 26),
    }
    local currentIndex = 0

    local function render_current_badge(entry)
        if not entry then
            IconCell:clearCell()
            clear_utf_cells(UTFCells)
            return
        end

        IconCell:setCell(entry.icon, entry.color)
        render_utf_title(UTFCells, entry.title or "")
    end

    local lowTimeElapsed = -random()

    eventFrame:HookScript("OnUpdate", function(_, elapsed)
        lowTimeElapsed = lowTimeElapsed + elapsed

        while lowTimeElapsed > ROTATE_INTERVAL do
            local badgeCount = #BadgeTitleTable

            lowTimeElapsed = lowTimeElapsed - ROTATE_INTERVAL

            if badgeCount == 0 then
                currentIndex = 0
                render_current_badge(nil)
                return
            end

            currentIndex = currentIndex + 1
            if currentIndex > badgeCount then
                currentIndex = 1
            end

            render_current_badge(BadgeTitleTable[currentIndex])
        end
    end)
end
insert(MartixInitFuncs, InitFrame)
