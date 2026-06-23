local addonName, addonTable = ... -- 插件名称与共享表

-- WoW 官方 API
local CreateFrame           = CreateFrame -- 创建框体
local UIParent              = UIParent    -- 游戏主界面父框体
-- DejaVu Core
local DejaVu                = _G["DejaVu"]
local GetUIScaleFactor      = DejaVu.GetUIScaleFactor -- UI 缩放计算
-- 框架初始化函数表
DejaVu.MartixInitFuncs      = {}
-- Matrix
addonTable.FontPath         = "Interface\\Addons\\" .. addonName .. "\\PixNum.ttf"

local SIZE                  = {}

local scale                 = 1

local function InitializeSize()              -- 初始化尺寸
    SIZE = {                                 -- 尺寸表主体
        MATRIX = {                           -- MatrixFrame有多个Cell
            Width = 84,                      -- Cell横向个数
            Height = 28,                     -- Cell纵向个数
        },
        CELL = GetUIScaleFactor(scale * 4),  -- Cell尺寸
        MEGA = GetUIScaleFactor(scale * 8),  -- MegaCell尺寸
        BADGE = GetUIScaleFactor(scale * 2), -- Badge尺寸
        FONT = GetUIScaleFactor(scale * 6),  -- Font尺寸
        PAD = GetUIScaleFactor(scale * 1),   -- Padding尺寸
    }
    -- SIZE 结束
    addonTable.SIZE = SIZE
end                                -- InitializeSize 结束

local function CreateMatrixFrame() -- 创建矩阵框架
    InitializeSize()

    local frame = CreateFrame("Frame", addonName .. "MartixFrame", UIParent)
    frame:SetPoint("TOPRIGHT", UIParent, "TOPRIGHT", 0, 0)
    frame:SetSize(SIZE.CELL * SIZE.MATRIX.Width, SIZE.CELL * SIZE.MATRIX.Height)
    frame:SetFrameStrata("TOOLTIP")
    frame:SetFrameLevel(9000)
    frame:Show()

    local bg = frame:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    bg:SetColorTexture(0, 0, 0, 1)
    bg:Show()
    addonTable.MartixFrame = frame
end


C_Timer.After(0, function()
    CreateMatrixFrame()
    for _, func in ipairs(DejaVu.MartixInitFuncs) do
        func()
    end
end)
