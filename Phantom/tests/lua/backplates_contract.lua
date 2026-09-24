-- 使用真实画布及背板，验证纯构造和正常内容消费者；不模拟游戏实际绘制。
local state, addon, size = ...
local root = addon.BackgroundFrame
local levels = addon.FrameLevel
assert(root.level == 9500 and root.width == 2 * size and root.height == 5 * size)
local expectedLevels = {
    Canvas = 9500, Separator = 9550, Backplate = 9600, Content = 9650,
    AuraContainer = 9700, AuraButton = 9750, AuraContent = 9800, Overlay = 9850, Marker = 9900,
}
local count = 0
for key, value in pairs(levels) do
    assert(expectedLevels[key] == value)
    count = count + 1
end
assert(count == 9)
local markers = 0
for _, frame in ipairs(root.children) do
    if frame.level then
        assert(frame.level == levels.Marker)
        markers = markers + 1
    end
end
assert(markers == 10 and state.resizeCalls == 0)

local function black(backplate, x, y, width, height)
    local frame, texture = backplate.Frame, backplate.BackgroundTexture
    assert(frame.parent == root and frame.level == levels.Backplate and frame.strata == "TOOLTIP")
    assert(frame.point[1] == "TOPLEFT" and frame.point[2] == root and frame.point[3] == "TOPLEFT")
    assert(frame.point[4] == x * size and frame.point[5] == y * size)
    assert(frame.width == width * size and frame.height == height * size)
    assert(texture.layer == "BACKGROUND" and texture.r == 0 and texture.g == 0 and texture.b == 0 and texture.a == 1)
end

local general = addon.CellBackplate:New({x = 9, y = 1})
local cellBacking = addon.CellBackplate:New({x = 2, y = 2})
black(general, 9, 0, 1, 1)
black(cellBacking, 2, -1, 1, 1)
assert(#general.Frame.textures == 1 and #cellBacking.Frame.children == 0)
assert(general.Texture == nil and general.setCell == nil)
assert(addon.GeneralCellLength == 1 and addon.ConditionCellLength == 1)
assert(root.width == 3 * size and state.resizeCalls == 2) -- 沿用累计次数而非最大坐标算法。

local barBacking = addon.ValueBarBackplate:New(1, 3)
black(barBacking, 1.5, -2, 3, 1)
local separator = barBacking.SeparatorFrame
assert(separator.parent == root and barBacking.Frame.parent == root)
assert(separator.level == levels.Separator and separator.width == 4 * size and separator.height == size)
assert(separator.point[4] == size and separator.point[5] == -2 * size)
assert(barBacking.Frame.point[4] - separator.point[4] == size / 2)
assert(separator.point[4] + separator.width - barBacking.Frame.point[4] - barBacking.Frame.width == size / 2)
assert(barBacking.SeparatorTexture.layer == "BACKGROUND")
assert(barBacking.SeparatorTexture.r == 1 and barBacking.SeparatorTexture.g == 0 and barBacking.SeparatorTexture.b == 0)
assert(barBacking.StatusBar == nil and #barBacking.Frame.children == 0)
assert(addon.ValueBarLength == 4 and state.resizeCalls == 3 and root.width == 6 * size)

local iconBacking = addon.IconTileBackplate:New(2)
black(iconBacking, 3, -3, 2, 2)
assert(iconBacking.Icon == nil and #iconBacking.Frame.textures == 1 and #iconBacking.Frame.children == 0)
assert(addon.IconTileLength == 2 and state.resizeCalls == 4)

local cell = addon.Cell:New({x = 3, y = 2})
black(cell.Backplate, 3, -1, 1, 1)
assert(cell.Frame == cell.Backplate.Frame and cell.X == 3 and cell.Y == 2)
assert(cell.Texture.layer == "ARTWORK" and cell.Texture.r == 0)
assert(#cell.Frame.children == 0 and #cell.Frame.textures == 2)
cell:setCellBoolean(true)
assert(cell.Texture.r == 1 and cell.Backplate.BackgroundTexture.r == 0)
cell:setCellBoolean(true, true)
assert(cell.Texture.r == 0)
cell:setCellRGBA(0.2, 0.4, 0.6)
assert(cell.Texture.r == 0.2 and cell.Texture.g == 0.4 and cell.Texture.b == 0.6 and cell.Texture.a == 1)
cell:clearCell()
assert(cell.Texture.r == 0)

local bar = addon.ValueBar:New(5, 2, true)
black(bar.Backplate, 5.5, -2, 2, 1)
assert(bar.Frame == bar.Backplate.Frame and bar.X == 5 and bar.width == 2)
assert(bar.StatusBar.parent == bar.Frame and bar.StatusBar.anchor == bar.Frame)
assert(bar.StatusBar.level == levels.Content and bar.StatusBar.reverse == true)
assert(bar.StatusBar.low == 0 and bar.StatusBar.high == 100 and bar.StatusBar.fill == 0.5)
assert(bar.StatusBar.fillColor[1] == 1 and bar.StatusBar.fillColor[4] == 1)
bar:setMinMaxValues(10, 30)
bar:setValue(15)
assert(bar.StatusBar.fill == 0.25)
local forward = addon.ValueBar:New(8, 1, "true")
assert(forward.StatusBar.reverse == nil and forward.StatusBar.fill == 0.5)

local icon = addon.IconTile:New(3)
black(icon.Backplate, 5, -3, 2, 2)
assert(icon.Frame == icon.Backplate.Frame and icon.Background == icon.Backplate.BackgroundTexture)
assert(#icon.Frame.children == 0 and #icon.Frame.textures == 3)
assert(icon.Icon.layer == "ARTWORK" and icon.Border.layer == "OVERLAY")
assert(icon.Icon.hidden and icon.Border.hidden)
icon:SetIcon(12345)
icon:SetBorderColor(addon.COLOR.RED)
assert(not icon.Icon.hidden and not icon.Border.hidden and icon.Icon.texture == 12345)
assert(icon.BorderColor == addon.COLOR.RED and icon.Border.r == 1 and icon.Border.g == 0)
icon:Clear()
assert(icon.Icon.hidden and icon.Border.hidden and icon.Background.r == 0)
assert(icon.Icon.texture == 12345 and icon.BorderColor == addon.COLOR.RED)
assert(addon.GeneralCellLength == 1 and addon.ConditionCellLength == 2)
assert(addon.ValueBarLength == 9 and addon.IconTileLength == 4)
assert(state.resizeCalls == 8 and root.width == 11 * size and root.height == 5 * size)
for _, frame in ipairs(state.frames) do assert(frame.level ~= levels.Overlay) end
