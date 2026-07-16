-- 命名空间声明
local addonName, addonTable = ...

-- 本地变量定义
local insert                = table.insert

-- WOW API 缓存
local CreateFrame           = CreateFrame
local UnitIsDeadOrGhost     = UnitIsDeadOrGhost

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell


--[[
简述：      玩家处于存活状态
分类：      玩家属性
分类索引：  1
位置：      1行1列

说明

使用UnitIsDeadOrGhost检测玩家是否死亡
    - True: 死亡
    - False: 存活

注意：因为没有检测玩家是否存活的直接函数，所以使用UnitIsDeadOrGhost来检测玩家是否死亡，取反后即可得到玩家是否存活的状态。

关于"秘密值"（Secret Value）：
在WoW 12.1中，很多API返回的值被标记为"secret"，不能直接用于逻辑判断或计算。UnitIsDeadOrGhost返回的布尔值可能是secret的，取反操作可能无法正确执行。
但是Cell:setCellBoolean这个函数设置了入参reverse，允许在设置cell颜色时，使用不同的EvaluateColorFromBoolean方案，实现取反。EvaluateColorFromBoolean是专门将秘密的布尔值转化为颜色的官方内置函数。


]]

-- 分类定义
-- CELL_CLASSIFICATION: 表示这个cell属于"玩家状态"分类
-- CELL_CLASSIFICATION_INDEX: 表示这是"玩家状态"分类下的第1个cell
-- CELL_POSITION_X/Y: 表示这个cell在矩阵中的位置（1行1列）
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS
local CELL_CLASSIFICATION_INDEX = 1
local CELL_POSITION_X = 1
local CELL_POSITION_Y = 1

-- 默认值：cell初始化时的B通道值（0-255）
-- 0表示黑色背景，用于初始化cell的颜色
local DEFAULT_VALUE = 0

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
    -- UnitIsDeadOrGhost("player") 返回：
    --   true  -> 玩家死亡或灵魂状态
    --   false -> 玩家存活状态
    -- 传入true表示反转颜色选择，确保B通道值正确表示玩家存活状态
    local function updateCell()
        cell:setCellBoolean(UnitIsDeadOrGhost("player"), true)
    end

    -- 初始化时立即更新一次状态
    updateCell()

    -- 注册事件：当玩家状态变化时更新cell
    -- PLAYER_DEAD: 玩家死亡
    -- PLAYER_ALIVE: 玩家复活
    -- PLAYER_UNGHOST: 玩家从灵魂状态恢复
    eventFrame:RegisterEvent("PLAYER_DEAD")
    eventFrame:RegisterEvent("PLAYER_ALIVE")
    eventFrame:RegisterEvent("PLAYER_UNGHOST")

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
