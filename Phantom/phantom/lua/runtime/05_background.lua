--[[
original: runtime\05_background.lua
uuid: daff1721-dbdd-4c7f-ab23-40701e1e82ab
runtime_index: 5
摘要：
    创建像素矩阵背景与对角定位标记，并提供背景尺寸更新接口。

描述：
    将背景初始化函数登记到共享 UI 初始化队列，执行时创建宽 2、高 5 个 Cell 的背景框体。
    调试模式下背景居中并显示蓝色，普通模式下贴齐游戏界面左上角并保持透明。
    在背景的两个对角各放置一个 Cell 大小的双色棋盘格标记，供画面定位使用；
    将背景框体写入 addonTable.BackgroundFrame，供后续模块访问。
    初始化四类区域的共享长度，并提供按最大长度加两列留白调整背景宽度的函数，高度保持五个 Cell。


修改记录：
2026-09-20：画布使用 Canvas，定位标记使用 Marker 静态层级。
2026-09-06：liantian-cn初始化创建。

]]


--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local insert                   = table.insert                         -- 插入表元素
local CreateFrame              = CreateFrame                          -- 创建框体
local UIParent                 = UIParent                             -- 游戏主界面父框体

--[[  variable reference  ]]


local COLOR       = addonTable.COLOR       -- 共享背景色与定位标记配色
local DEBUG       = addonTable.DEBUG       -- 调试模式决定背景的位置和底色
local FrameLevel  = addonTable.FrameLevel  -- 背景与 Cell 底层框体的层级定义
local UIInitFuncs = addonTable.UIInitFuncs -- 共享 UI 初始化函数队列
local SIZE        = addonTable.SIZE        -- 共享 Cell 尺寸定义

--[[  logical code  ]]


--[[
后续更新BackgroundFrame的宽度，要获取通用Cell，条件Cell、ValueBar、Icon Tile几个最宽的决定。
注意这里的宽度是SIZE.CELL的倍数
]]
addonTable.GeneralCellLength = 0 -- 通用 Cell 行的共享长度，以 Cell 为单位
addonTable.ConditionCellLength = 0 -- 条件 Cell 行的共享长度，以 Cell 为单位
addonTable.ValueBarLength = 0 -- Value Bar 区域的共享长度，以 Cell 为单位
addonTable.IconTileLength = 0 -- Icon Tile 区域的共享长度，以 Cell 为单位


local function InitBackgroundFrame() -- 创建矩阵框架
    --[[
        初始化面板
        逻辑:
        - 以下尺寸都是SIZE.CELL的倍数
        - 初始面板大小仅有高5 宽2
        - 左上角和右下角是定位符。

        DEBUG模式：
        - debug模式下更显眼
    ]]

    local bgFrame = CreateFrame("Frame", addonName .. "BackgroundFrame", UIParent) -- 创建矩阵背景父框体
    if DEBUG then -- 按调试开关选择背景显示方式
        bgFrame:SetPoint("CENTER", UIParent, "CENTER", 0, 0)                       -- 调试时居中便于观察
    else
        bgFrame:SetPoint("TOPLEFT", UIParent, "TOPLEFT", 0, 0)                     -- 普通模式固定在界面左上角
    end
    bgFrame:SetSize(SIZE.CELL * 2, SIZE.CELL * 5)                                  -- 初始化为宽 2、高 5 个 Cell
    bgFrame:SetFrameStrata("TOOLTIP")                                              -- 将背景放入 TOOLTIP 显示层
    bgFrame:SetFrameLevel(FrameLevel.Canvas)                                       -- 使用画布层级
    bgFrame:Show() -- 显示矩阵背景框体

    local bgTexture = bgFrame:CreateTexture(nil, "BACKGROUND") -- 创建背景底色纹理
    bgTexture:SetAllPoints()                                   -- 铺满背景框体
    if DEBUG then -- 按调试开关选择背景显示方式
        bgTexture:SetColorTexture(COLOR.BLUE:GetRGBA())        -- 调试时用蓝色显示背景范围
    else
        bgTexture:SetColorTexture(COLOR.TRANSPARENT:GetRGBA()) -- 普通模式使背景底色透明
    end

    bgTexture:Show() -- 显示背景底色纹理



    local function CreateMaskFrame(mask_idx) -- 按标识创建一个双色棋盘格定位框体
        --[[
        每个标记位：
            整体一个Cell大小，由4个边长为 SIZE.CELL / 2 的方片组成。颜色不同，使用COLOR.MARK.POINT_0和COLOR.MARK.POINT_1
            排列为:
            0 | 1
            -----
            1 | 0

        ]]

        local _frame = CreateFrame("Frame", addonName .. "MaskFrame" .. mask_idx, bgFrame) -- 定位框体随背景移动
        _frame:SetSize(SIZE.CELL, SIZE.CELL)                                               -- 每个定位标记占一个 Cell
        _frame:SetFrameStrata("TOOLTIP") -- 使定位标记使用 TOOLTIP 显示层
        _frame:SetFrameLevel(FrameLevel.Marker)                                            -- 定位标记使用最高静态层级
        _frame:Show() -- 显示定位标记框体

        local cells = {}                -- 按行列保存标记的四块纹理
        local cell_size = SIZE.CELL / 2 -- 每块纹理边长为半个 Cell
        local colors = {                -- 棋盘格交替使用的两种标记颜色
            COLOR.MARK.POINT_0, -- 棋盘格第一种颜色
            COLOR.MARK.POINT_1, -- 棋盘格第二种颜色
        }

        for row = 1, 2 do -- 逐行创建两行定位色块
            cells[row] = {} -- 保存当前行的纹理
            for col = 1, 2 do -- 逐列创建当前行的两个色块
                local _texture = _frame:CreateTexture(nil, "ARTWORK") -- 创建当前行列的标记色块
                _texture:SetSize(cell_size, cell_size) -- 将色块设为半个 Cell 的宽高
                _texture:SetPoint(
                    "TOPLEFT", _frame, "TOPLEFT",
                    (col - 1) * cell_size, -(row - 1) * cell_size -- 从左上角向右、向下排列
                )

                local color = colors[(row + col) % 2 + 1] -- 行列和的奇偶决定颜色，形成 0/1、1/0 排列
                _texture:SetColorTexture(color:GetRGBA()) -- 应用当前色块的定位颜色

                cells[row][col] = _texture -- 按行列保存色块纹理
            end
        end
        return _frame -- 返回完成布局的定位框体
    end                                            -- CreateMaskFrame

    local top_left_mask = CreateMaskFrame("1")     -- 创建左上定位标记
    top_left_mask:SetPoint("TOPLEFT", bgFrame, "TOPLEFT", 0, 0) -- 将标记固定在背景左上角
    local bottom_right_mask = CreateMaskFrame("1") -- 创建右下定位标记
    bottom_right_mask:SetPoint("BOTTOMRIGHT", bgFrame, "BOTTOMRIGHT", 0, 0) -- 将标记固定在背景右下角并随尺寸变化移动


    addonTable.BackgroundFrame = bgFrame -- 发布背景框体供其他模块引用
end
insert(UIInitFuncs, InitBackgroundFrame) -- 登记初始化函数，由共享 UI 初始化流程执行


--[[
修复背板宽度
]]
local function BackgroundFrameResize() -- 按各区域共享长度更新背景尺寸
    local max_length = max(addonTable.GeneralCellLength, addonTable.ConditionCellLength, addonTable.ValueBarLength, addonTable.IconTileLength) -- 取四类区域中最大的共享长度
    addonTable.BackgroundFrame:SetSize(SIZE.CELL * (2 + max_length), SIZE.CELL * 5) -- 背景宽度为最大共享长度加两列留白，高度保持五个 Cell
end
addonTable.BackgroundFrameResize = BackgroundFrameResize -- 公开背景尺寸更新接口
