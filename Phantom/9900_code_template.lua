-- 命名空间声明
local addonName, addonTable = ...

-- 本地变量定义
local insert                = table.insert

-- WOW API 缓存
local CreateFrame           = CreateFrame

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell


--[[
简述：      （填写简述）
分类：      （填写分类名称）
分类索引：  （填写分类索引）
位置：      （填写矩阵位置）

说明

（填写说明）

]]

-- 分类定义
-- CELL_CLASSIFICATION: 表示这个cell属于哪个分类，必须替换为实际的分类常量
-- CELL_CLASSIFICATION_INDEX: 表示这是该分类下的第几个cell，必须替换为实际的索引值
-- CELL_POSITION_X/Y: 表示这个cell在矩阵中的位置，必须替换为实际的坐标
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.REPLACE_ME
local CELL_CLASSIFICATION_INDEX = nil
local CELL_POSITION_X = nil
local CELL_POSITION_Y = nil

-- 默认值：cell初始化时的B通道值（0-255），必须替换为实际的默认值
local DEFAULT_VALUE = nil

-- 开始代码
local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 每个文件独立的事件框架

    -- 创建cell实例
    -- 当文件只需要创建一个cell时，直接使用cell作为局部变量即可。
    -- 当文件需要创建多个cell时，可以使用一个table来存储所有cell实例，方便管理和访问。
    local cell = Cell:New({
        x = CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = CELL_CLASSIFICATION_INDEX,
        default_value = DEFAULT_VALUE,
    })

    -- 更新函数：设置cell的状态
    -- 当文件只需要创建一个更新函数时，直接使用updateCell作为函数名即可。
    -- 当文件需要创建多个更新函数时，使用清晰的名称。
    local function updateCell()
        -- cell:setCellBoolean(...)
    end

    -- 初始化时立即更新一次状态
    updateCell()

    -- 注册事件
    -- eventFrame:RegisterEvent("EVENT_NAME")

    -- 事件处理：所有事件都调用同一个更新函数
    -- 这种模式适用于多个事件触发相同处理逻辑的情况
    eventFrame:SetScript("OnEvent", function(self, event, ...)
        updateCell()
    end)

    -- 如果需要为不同事件调用不同函数，可以使用路由分配模式：
    -- eventFrame:SetScript("OnEvent", function(self, event, ...)
    --     self[event](self, ...)
    -- end)
end

-- 将初始化函数插入到全局初始化函数列表中，确保在插件加载时执行
-- 执行顺序：
-- 1. 所有文件加载，注册InitFrame到FrameInitFuncs
-- 2. 第二帧时执行所有FrameInitFuncs
-- 3. CreateMartixFrame先执行（在0005_matrix.lua中注册）
-- 4. 然后InitFrame执行（在本文件中注册）
insert(addonTable.FrameInitFuncs, InitFrame)
