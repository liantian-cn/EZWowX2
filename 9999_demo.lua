-- 命名空间声明
local addonName, addonTable = ...

-- 本地变量定义
local insert = table.insert
local ICON_BORDER_COLOR = CreateColor(64 / 255, 158 / 255, 210 / 255, 1)

-- 代码部分

-- 创建演示实例
local function CreateDemoIconCell()
    local IconCell = addonTable.IconCell
    local iconCell = IconCell:New(1, 3)
    iconCell:SetIcon(3186652)
    iconCell:SetBorderColor(ICON_BORDER_COLOR)
    return iconCell
end

-- 将初始化函数插入到全局初始化函数列表中，确保在插件加载时执行
-- 执行顺序：
-- 1. 所有文件加载，注册CreateDemoIconCell到FrameInitFuncs
-- 2. 第二帧时执行所有FrameInitFuncs
-- 3. CreateMartixFrame先执行（在0005_matrix.lua中注册）
-- 4. 然后CreateDemoIconCell执行（在本文件中注册）
insert(addonTable.FrameInitFuncs, CreateDemoIconCell)
