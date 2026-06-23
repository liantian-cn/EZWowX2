local addonName, addonTable = ... -- 插件入口固定写法

-- Lua 原生函数
local After = C_Timer.After

-- DejaVu Core
local DejaVu = _G["DejaVu"]
local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell
local CharCell = DejaVu.CharCell

After(2, function() -- 2 秒后执行，确保 DejaVu 核心已加载完成
    -- 左上和右下的标记点。
    -- 正式使用前先注释

    -- x:0 y:0
    -- 用途：左上角基准标记点。
    -- 更新函数：无
    Cell:New(0, 0, COLOR.MARK_POINT.NEAR_BLACK_1)

    -- x:1 y:1
    -- 用途：左上角基准标记点的对角辅助点。
    -- 更新函数：无
    Cell:New(1, 1, COLOR.MARK_POINT.NEAR_BLACK_1)

    -- x:0 y:1
    -- 用途：左上角浅色辅助标记点。
    -- 更新函数：无
    Cell:New(0, 1, COLOR.MARK_POINT.NEAR_BLACK_2)

    -- x:1 y:0
    -- 用途：左上角浅色辅助标记点。
    -- 更新函数：无
    Cell:New(1, 0, COLOR.MARK_POINT.NEAR_BLACK_2)

    -- x:82 y:26
    -- 用途：右下角基准标记点。
    -- 更新函数：无
    Cell:New(82, 26, COLOR.MARK_POINT.NEAR_BLACK_1)

    -- x:83 y:27
    -- 用途：右下角基准标记点的对角辅助点。
    -- 更新函数：无
    Cell:New(83, 27, COLOR.MARK_POINT.NEAR_BLACK_1)

    -- x:82 y:27
    -- 用途：右下角浅色辅助标记点。
    -- 更新函数：无
    Cell:New(82, 27, COLOR.MARK_POINT.NEAR_BLACK_2)

    -- x:83 y:26
    -- 用途：右下角浅色辅助标记点。
    -- 更新函数：无
    Cell:New(83, 26, COLOR.MARK_POINT.NEAR_BLACK_2)

    -- 左上的CharCell验证点，验证字体是否正确加载。

    -- x:0 y:2
    -- 用途：验证字符字体是否正确加载。
    -- 更新函数：无
    CharCell:New(0, 2):setCell("*")

    -- 右上角白色检测点

    -- x:82 y:2
    -- 用途：右上角白色检测点。
    -- 更新函数：无
    Cell:New(82, 2):setCell(COLOR.WHITE)

    -- 下方为各区域标记点，绿色为标记点。
    local function CreateMarkSet(x, y, height)
        for i = 1, height do
            -- x:x y:y - 1 + i
            -- 用途：绘制区域边界的绿色标记点。
            -- 更新函数：无
            Cell:New(x, y - 1 + i, COLOR.GREEN)
        end
    end

    CreateMarkSet(0, 4, 5)
    CreateMarkSet(61, 4, 5)
    CreateMarkSet(0, 9, 5)
    CreateMarkSet(21, 9, 5)
    CreateMarkSet(54, 10, 2)
    CreateMarkSet(69, 10, 2)
    CreateMarkSet(69, 12, 2)
    CreateMarkSet(54, 13, 1)
    CreateMarkSet(54, 12, 1)
    CreateMarkSet(0, 14, 5)
    CreateMarkSet(21, 14, 5)
    CreateMarkSet(42, 14, 4)
    CreateMarkSet(0, 19, 9)
    CreateMarkSet(21, 19, 9)
    CreateMarkSet(42, 19, 9)
    CreateMarkSet(63, 19, 9)
    CreateMarkSet(63, 15, 2)
    CreateMarkSet(42, 17, 2)
    CreateMarkSet(0, 26, 2)
    CreateMarkSet(41, 26, 2)
    CreateMarkSet(81, 17, 2)
end)
