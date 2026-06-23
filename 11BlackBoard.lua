-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame -- 创建框体
local UIParent              = UIParent    -- 游戏主界面父框体

-- 插件级变量定义/引用

local GetUIScaleFactor      = addonTable.GetUIScaleFactor -- UI 缩放计算

addonTable.FrameInitFuncs   = {}                          -- 框架初始化函数表
addonTable.SIZE             = {}                          -- 尺寸表
-- 本地变量定义

local scale                 = 1
local SIZE                  = addonTable.SIZE

-- 代码部分

local function InitializeSize()              -- 初始化尺寸
    SIZE = {                                 -- 尺寸表主体
        BlackBoard = {                       -- BlackBoardFrame有多个Cell
            Width = 256,                     -- Cell横向个数
            Height = 4,                      -- Cell纵向个数
        },
        CELL = GetUIScaleFactor(scale * 4),  -- Cell尺寸
        MEGA = GetUIScaleFactor(scale * 8),  -- MegaCell尺寸
        BADGE = GetUIScaleFactor(scale * 2), -- Badge尺寸
        FONT = GetUIScaleFactor(scale * 6),  -- Font尺寸
        PAD = GetUIScaleFactor(scale * 1),   -- Padding尺寸
    }
end



local function CreateBlackBoardFrame() -- 创建矩阵框架
    InitializeSize()

    local frame = CreateFrame("Frame", addonName .. "BlackBoardFrame", UIParent)
    frame:SetPoint("TOPLEFT", UIParent, "TOPLEFT", 0, 0)
    frame:SetSize(SIZE.CELL * SIZE.BlackBoard.Width, SIZE.CELL * SIZE.BlackBoard.Height)
    frame:SetFrameStrata("TOOLTIP")
    frame:SetFrameLevel(9000)
    frame:Show()

    local bg = frame:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    bg:SetColorTexture(0, 0, 0, 1)
    bg:Show()
    addonTable.BlackBoardFrame = frame
end









C_Timer.After(0, function()
    CreateBlackBoardFrame()
    for _, func in ipairs(addonTable.FrameInitFuncs) do
        func()
    end
end)
